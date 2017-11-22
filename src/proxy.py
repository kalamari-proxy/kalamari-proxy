import time
import asyncio
import http.client
import email.parser
from urllib.parse import urlparse
import logging

import config
import resource
import acl


class ProxyServer():
    '''
    Handle incoming proxy requests and perform request parsing.
    '''
    MAXLINE = 65536
    MAXHEADERS = 100

    def __init__(self, loop):
        self.loop = loop

        logging.info("Initializing proxy...")

        self.next_sess_id = 1

        # Load blacklist, whitelist, and cache list
        self.blacklist = resource.ResourceList()
        self.whitelist = resource.ResourceList()
        self.cachelist = resource.CacheList()
        self.blacklist.load(config.blacklist)
        self.whitelist.load(config.whitelist)
        self.cachelist.load(config.cachelist)

        # Start periodic refresh
        asyncio.ensure_future(self.start_periodic_refresh(config.list_refresh))
  
        # create the acl object to handle incoming connections 
        logging.info("Initializing Access Control Lists (ACL's)")
        self.acl = acl.ACL(config.ip_acl)

    async def handler(self, reader, writer):
        '''
        Handler for incoming proxy requests.
        '''
        # Read the request method and headers
        method_line = (await reader.readline()).decode('utf8')
        headers = await self.parse_headers(reader)

        # Parse method line
        method, target, version = ProxyServer.parse_method(method_line)
        if method == 'CONNECT':
            hostname, port = target.split(':')
            request = HTTPRequest(method, hostname, port, '', headers, self.next_sess_id)
        else:
            hostname, port, path = ProxyServer.parse_url(target)
            request = HTTPRequest(method, hostname, port, path, headers, self.next_sess_id)

        logging.info('HTTP REQUEST ' + str(request))

        # this is where we should reject requests that come from unauthorized ip's
        request_allowed_acl = False
        try:
            ip_address = writer.get_extra_info('peername')[0]

            if ip_address is None:
                logging.info('Could not get remote IP address')
                writer.write(b'HTTP/1.1 403 Forbidden\n\n')
                writer.close()

            else:
                if not self.acl.ip_allowed(ip_address):
                    logging.info('Request from {} comes from disallowed network per ACL\'s, returning \'HTTP/1.1 403 Forbidden\''.format(ip_address))
                    writer.write(b'HTTP/1.1 403 Forbidden\n\n')
                    writer.close()

                else:
                    logging.info('Request from {} comes from allowed network per ACL\'s, continuing to process request'.format(ip_address))
                    request_allowed_acl = True

        # case where invalid ip address source
        except ValueError:
            logging.error('Invalid Inbound IP Address: {}, returning \'HTTP/1.1 403 Forbidden\''.format(ip_address))
            writer.write(b'HTTP/1.1 403 Forbidden\n\n')
            writer.close()


        if request_allowed_acl:
            # Check if the request is on the blacklist or whitelist
            if self.whitelist.check(request):
                logging.info('Request is on the whitelist')
            elif self.blacklist.check(request):
                logging.info('Request is on the blacklist')
                writer.write(b'HTTP/1.1 404 Not Found\n\n')
                writer.close()
                return

            # Check if the request is on the cached resources list
            redirect = self.cachelist.check(request)
            if redirect:
                logging.info('Request is on the cached resource list.')
                hostname, port, path = ProxyServer.parse_url(redirect)
                request = HTTPRequest(method, hostname, port, path, headers, request.session_id)
                logging.info('Redirecting request to: %s' % request)

            # Create a ProxySession instance to handle the request
            proxysession = ProxySession(self.loop, reader, writer, request)
            proxysession.connect()
            self.loop.create_task(proxysession.run())

            # increment session id
            self.next_sess_id += 1

    @staticmethod
    def parse_method(method):
        '''
        Given an HTTP request method line like:

        GET http://foobar.com/ HTTP/1.1\r\n

        Parse that line into the verb (GET), url (http://foobar.com/), and
        protocol (HTTP/1.1). This method returns these values arranged in a
        tuple like:

        ("GET", "http://foobar.com/", "HTTP/1.1")
        '''
        split = method.split(' ')

        # check for HTTP verb (GET, POST, etc.)
        if len(split) < 1:
            raise ValueError('Missing HTTP verb')
        else:
            verb = split[0]

        # check for HTTP request target (aka URL)
        if len(split) < 2:
            raise ValueError('missing request target')
        else:
            target = split[1]

        # check for HTTP version
        if len(split) < 3:
            raise ValueError('missing HTTP version')
        else:
            # remove CRLF from end of method line
            version = split[2].strip()

        return (verb, target, version)

    @staticmethod
    def parse_url(url):
        '''
        Decompose a URL and return a tuple containing:
        (hostname, port, path)
        '''
        parsed = urlparse(url)
        path = parsed.path or '/'
        if parsed.query:
            path += '?%s' % parsed.query
        return (parsed.hostname, parsed.port or 80, path)

    @classmethod
    async def parse_headers(cls, reader):
        '''
        Read HTTP header data from `reader`. This code is a port of the
        HTTP header parsing code from the Python standard library; it
        has been modified to use asyncio.
        https://github.com/python/cpython/blob/3.6/Lib/http/client.py

        :return: a dict of headers and values.
        :raises: ValueError if a line longer than MAXLINE characters is
          discovered.
        :raises: ValueError if more than MAXHEADERS headers are
          discovered.
        '''
        headers = []
        while True:
            line = await reader.readline()
            if len(line) > cls.MAXLINE:
                raise ValueError('Line too long while parsing header')
            headers.append(line)
            if len(headers) > cls.MAXHEADERS:
                raise ValueError('Too many headers found while parsing')
            if line in (b'\r\n', b'\n', b''):
                break

        hstring = b''.join(headers).decode('iso-8859-1')
        parser = email.parser.Parser(_class=http.client.HTTPMessage)
        return parser.parsestr(hstring)

    async def refresh_lists(self):
        '''
        Refresh blacklist, whitelist, and cached resource lists.
        '''
        try:
            blacklist = resource.ResourceList()
            blacklist.load(config.blacklist)
            whitelist = resource.ResourceList()
            whitelist.load(config.whitelist)
            cachelist = resource.CacheList()
            cachelist.load(config.cachelist)

            self.blacklist = blacklist
            self.whitelist = whitelist
            self.cachelist = cachelist

        except Exception as err:
            logging.error('Error encountered while refreshing lists: %s' % err)

    async def start_periodic_refresh(self, interval=12*3600):
        '''
        Automatically refresh the blacklist, whitelist, and cached
        resource list every `interval` seconds. The default interval is
        12 hours.

        The refresh functionality can be disabled by setting the
        the refresh interval to a negative number.
        '''
        if interval < 0:
            return

        while True:
            # Sleep first because the lists are initialized automatically upon
            # initializeation. So, we should sleep first.
            await asyncio.sleep(interval)
            await self.refresh_lists()


class HTTPRequest():
    '''
    Class to store information about a request.
    '''
    def __init__(self, method, hostname, port, path, headers, session_id):
        self.method = method
        self.host = hostname
        self.port = port
        self.path = path
        self.headers = headers
        self.session_id = session_id

        self.time = time.time()

    def timed_out(self):
        if time.time() - self.time > config.timeout:
            return True
        return False

    def __str__(self):
        return (
            '(Session {0}) - '
            'method={1}, '
            'host={2}, '
            'port={3}, '
            'path={4}'
            ).format(
            self.session_id,
            self.method,
            self.host,
            self.port,
            self.path)


class ProxySession():
    '''
    Manages communication between the client and Kalamari and between
    Karamari and the request destination.
    '''
    def __init__(self, loop, reader, writer, request):
        self.loop = loop
        self.reader = reader
        self.writer = writer
        self.request = request
        self.output = None

    def connect(self):
        '''
        Connect to the remote server and add the socket to the event
        loop.
        '''
        # Creates a socket and uses inherited methods from asyncio.Protocol as
        # callbacks for network events.
        self.output = ProxySessionOutput(self, self.request)
        coro = self.loop.create_connection(lambda: self.output,
                                           self.request.host, self.request.port)
        self.task = asyncio.async(coro)

    async def run(self):
        while not self.output.ready() and not self.request.timed_out():
            await asyncio.sleep(0.5)

        if self.request.timed_out():
            logging.info('Request timed out: %s' % self.request)
            return

        while not self.reader.at_eof():
            data = await self.reader.read(8192)
            self.output.transport.write(data)


class ProxySessionOutput(asyncio.Protocol):
    '''
    Handle the outboud connection to the destination server.
    '''

    def __init__(self, proxysession, request):
        super().__init__()
        self.proxysession = proxysession
        self.request = request
        self.transport = None

    def ready(self):
        '''
        Indicates if we are ready to forward output.
        '''
        if self.transport is None:
            return False
        return True

    def connection_made(self, transport):
        '''
        Callback for when the network connection was successful.
        Forward the request to the remote server.
        '''

        logging.debug('CONNECTION SUCCESSFUL TO REMOTE (Session {0})'.format(self.request.session_id))

        self.transport = transport

        logging.debug('FORWARDING REQUEST TO REMOTE (Session {0})'.format(self.request.session_id))

        # Special handling for the CONNECT method.
        # Notify the client that the connection has been opened.
        if self.request.method == 'CONNECT':
            self.proxysession.writer.write(b'HTTP/1.1 200 OK\n\n')
            return

        self.transport.write('GET {path} HTTP/1.1\nHost: {host}\nConnection: close\n\n'.format(**{
            'host': self.request.host,
            'path': self.request.path
        }).encode('iso-8859-1'))

    def data_received(self, data):
        '''
        Callback for when data was received over the network.
        Pass the data to the proxy session.
        '''

        logging.debug('RESPONSE RECEIEVED FROM REMOTE (Session {0})'.format(self.request.session_id))

        logging.debug('FORWARDING RESPONSE TO USER (Session {0})'.format(self.request.session_id))

        self.proxysession.writer.write(data)

        logging.debug('FORWARDED RESPONSE TO USER (Session {0})'.format(self.request.session_id))

    def connection_lost(self, exc):
        '''
        Callback for when thenetwork connection is closed.
        Notify the proxy session to close.
        '''

        logging.debug('DISCONNECTED FROM REMOTE (Session {0})'.format(self.request.session_id))

        self.proxysession.writer.close()
