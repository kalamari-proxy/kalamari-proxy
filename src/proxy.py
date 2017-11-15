import time
import asyncio
import http.client
import email.parser
from urllib.parse import urlparse
import logging

import config
import resource


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

        # Check if the request is on the blacklist, whitelist, or cachelist
        if self.blacklist.check(request):
            logging.info('Request is on the blacklist')
        if self.whitelist.check(request):
            logging.info('Request is on the whitelist')
        redirect = self.cachelist.check(request)
        if redirect:
            logging.info('Request is on the cached resource list. New location %s' % redirect)

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
        return (parsed.netloc, parsed.port or 80, path)

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

    @classmethod
    async def refresh_blacklist(self):
        '''
        Refresh blacklist to update and enforce new rule set after 12 hours
        '''
        self.blacklist = resource.ResourceList()
        self.blacklist.load(self, config.blacklist)

    @classmethod
    async def start_periodic_refresh(self, interval):
        '''
        Given an interval (in seconds) keep refreshing the blacklist.
        '''

        # Interval defaults to 12hrs
        interval = interval if interval >= 0 else (12 * 3600)

        while True:
            time.sleep(interval)
            self.refresh_blacklist()

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
