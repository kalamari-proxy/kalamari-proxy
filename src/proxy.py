import time
import asyncio
import http.client
import email.parser
from urllib.parse import urlparse
import logging
import select
import ssl
import subprocess

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
        self.start_periodic_refresh(config.list_refresh)

        # create the acl object to handle incoming connections
        logging.info("Initializing Access Control Lists (ACL's)")
        self.acl = acl.ACL(config.ip_acl)

        # Create SSL Context
        self.ssl_context = ssl.SSLContext()
        self.ssl_context.load_cert_chain('ca.crt', 'ca.key')

    async def handler(self, reader, writer):
        '''
        Handler for incoming proxy requests.
        '''
        # Check if request origin is allowed by the ACL
        allowed = self.check_if_ip_allowed(writer.get_extra_info('peername')[0])
        if not allowed:
            writer.write(b'HTTP/1.1 403 Forbidden\r\n\r\n')
            writer.close()
            return

        # Read the request method and headers
        method_line = (await reader.readline()).decode('utf8')
        headers = await self.parse_headers(reader)
        print('got headers: %s' % headers)

        # Parse method line
        method, target, version = ProxyServer.parse_method(method_line)
        if method == 'CONNECT':
            hostname, port = target.split(':')
            request = HTTPRequest(method, hostname, port, '', headers,
                                  self.get_next_session_id())
        else:
            hostname, port, path = ProxyServer.parse_url(target)
            request = HTTPRequest(method, hostname, port, path, headers,
                                  self.get_next_session_id())

        logging.info('HTTP REQUEST ' + str(request))

        # Check if the request is on the blacklist or whitelist
        if self.whitelist.check(request):
            logging.info('Request is on the whitelist (Session %i)' % request.session_id)
        elif self.blacklist.check(request):
            logging.info('Request is on the blacklist (Session %i)' % request.session_id)
            writer.write(b'HTTP/1.1 404 Not Found\n\n')
            writer.close()
            return

        # Check if the request is on the cached resources list
        redirect = self.cachelist.check(request)
        if redirect:
            logging.info('Request is on the cached resource list (Session %i)' % request.session_id)
            hostname, port, path = ProxyServer.parse_url(redirect)
            request = HTTPRequest(method, hostname, port, path, headers, request.session_id)
            logging.info('Redirecting request to: %s' % request)

        # Create a ProxySession instance to handle the request
        if request.method == 'CONNECT':
            print('Handling TLS request')
            writer.write(b'HTTP/1.1 200 OK\r\n\r\n')

            self.gen_cert(request.host)

            ssl_context = ssl.SSLContext()
            ssl_context.load_cert_chain('%s.crt' % request.host, '%s.key' % request.host)

            sock = writer.get_extra_info('socket')
            wrapped = ssl_context.wrap_socket(
                sock=sock,
                server_side=True,
                do_handshake_on_connect=False
            )
            await self.run_handshake(wrapped)
            #self.loop.create_task(self.loop.create_connection(ProxySessionTLS, sock=wrapped))
            reader, writer = await asyncio.open_connection(sock=wrapped, loop=self.loop)
            proxysession = ProxySessionTLS(self.loop, self, reader, writer, request.host)
            self.loop.create_task(proxysession.handle_request())
        else:
            proxysession = ProxySession(self.loop, reader, writer, request)
            proxysession.connect()
            self.loop.create_task(proxysession.run())

    async def run_handshake(self, sock):
        '''
        Coppied from the Python documentation:
        https://docs.python.org/3/library/ssl.html#notes-on-non-blocking-sockets
        '''
        while True:
            try:
                print('trying to handshake')
                sock.do_handshake()
                break
            except ssl.SSLWantReadError:
                print('handshake needs read')
                select.select([sock], [], [])
            except ssl.SSLWantWriteError:
                print('handshake needs write')
                select.select([], [sock], [])

    def gen_cert(self, hostname):
        sans = '*.{host},*.*.{host},*.*.*.{host},*.*.*.*.{host},*.*.*.*.*.{host}'
        subprocess.call(['./create-cert.sh', '-c', hostname, '-s', sans])

    def check_if_ip_allowed(self, ip):
        '''
        Check if `ip` is allowed to make proxy requests based on the ACL.
        '''
        try:
            if ip is None:
                logging.info('Could not get remote IP address')
                return False
            else:
                if not self.acl.ip_allowed(ip):
                    logging.info('Request from {} comes from disallowed network per ACL\'s'.format(ip))
                    return False
                else:
                    logging.info('Request from {} comes from allowed network per ACL\'s'.format(ip))
                    return True

        # case where invalid ip address source
        except ValueError:
            logging.error('Invalid Inbound IP Address: {}'.format(ip))
            return

    def get_next_session_id(self):
        tmp = self.next_sess_id
        self.next_sess_id += 1
        return tmp

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
        if len(split) == 1 and split[0] == '':
            raise ValueError('Missing HTTP verb')
        else:
            verb = split[0]

        # check for HTTP request target (aka URL)
        if len(split) < 2:
            logging.debug('Parsing method: %s' % method)
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

    async def refresh_lists(self, interval):
        '''
        Refresh blacklist, whitelist, and cached resource lists.
        '''
        while True:
            # Sleep first because the lists are initialized automatically upon
            # initializeation. So, we should sleep first.
            await asyncio.sleep(interval)
            logging.debug('Refreshing lists')

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
                logging.error('Error while refreshing lists: %s' % err)



    def start_periodic_refresh(self, interval=12*3600):
        '''
        Automatically refresh the blacklist, whitelist, and cached
        resource list every `interval` seconds. The default interval is
        12 hours.

        The refresh functionality can be disabled by setting the
        the refresh interval to a negative number.
        '''
        logging.debug('Starting periodic list refresh')

        if interval < 0:
            return

        asyncio.ensure_future(self.refresh_lists(interval))


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


class ProxySessionTLS():
    def __init__(self, loop, proxy, reader, writer, hostname):
        self.loop = loop
        self.proxy = proxy
        self.reader = reader
        self.writer = writer
        self.hostname = hostname

    async def handle_request(self):
        method_line = (await self.reader.readline()).decode('utf8')
        headers = await ProxyServer.parse_headers(self.reader)

        # Parse method line
        print('METHOD:', method_line)
        method, target, version = ProxyServer.parse_method(method_line)
        if method == 'CONNECT':
            hostname, port = target.split(':')
            print('HOSTNAME CONNECT: ', hostname)
            request = HTTPRequest(method, hostname, port, '', headers,
                                  self.proxy.get_next_session_id())
        else:
            print('HOSTNAME OTHER: ', self.hostname)
            # Set port to 0 because it doesn't matter anymore
            request = HTTPRequest(method, self.hostname, None, target, headers,
                                  self.proxy.get_next_session_id())

        logging.info('HTTP REQUEST ' + str(request))

        # Check if the request is on the blacklist or whitelist
        if self.proxy.whitelist.check(request):
            logging.info('Request is on the whitelist (Session %i)' % request.session_id)
        elif self.proxy.blacklist.check(request):
            logging.info('Request is on the blacklist (Session %i)' % request.session_id)
            self.writer.write(b'HTTP/1.1 404 Not Found\n\n')
            self.writer.close()
            return

        # Check if the request is on the cached resources list
        redirect = self.proxy.cachelist.check(request)
        if redirect:
            logging.info('Request is on the cached resource list (Session %i)' % request.session_id)
            hostname, port, path = ProxyServer.parse_url(redirect)
            request = HTTPRequest(method, hostname, port, path, headers, request.session_id)
            logging.info('Redirecting request to: %s' % request)


        proxysession = ProxySession(self.loop, self.reader, self.writer, request)
        proxysession.connect()
        self.loop.create_task(proxysession.run())


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
            self.proxysession.writer.write(b'HTTP/1.1 200 OK\r\n\r\n')
            return

        self.transport.write('{method} {path} HTTP/1.0\r\nHost: {host}\r\nConnection: close\r\n'.format(**{
            'method': self.request.method,
            'host': self.request.host,
            'path': self.request.path
        }).encode('iso-8859-1'))
        for header, value in self.request.headers.items():
            if header.lower() in ('connection', 'host'):
                continue
            self.transport.write('{header}: {value}\r\n'.format(**{
                'header': header,
                'value': value
            }).encode('iso-8859-1'))
        self.transport.write(b'\r\n')

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
