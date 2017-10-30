import asyncio
import http.client
import email.parser


class ProxyServer():
    '''
    Handle incoming proxy requests and perform request parsing.
    '''
    MAXLINE = 65536
    MAXHEADERS = 100

    def __init__(self, loop):
        self.loop = loop
    
    async def handler(self, reader, writer):
        '''
        Handler for incoming proxy requests.
        '''
        # Read the request method
        method_line = await reader.readline()
        print('method:', method_line)

        # Read headers from the request
        headers = await self.parse_headers(reader)

        # Create an HTTP request object to contain the details
        # TODO: stop using hardcoded values. Use parsed values instead.
        request = HTTPRequest('GET', 'localhost', 80, 'http://localhost/', headers)
        proxysession = ProxySession(self.loop, reader, writer, request)
        proxysession.connect()

        self.loop.create_task(proxysession.run())

        # Send a default response. TODO: change this.
        # writer.write(b'HTTP/1.1 404 Not Found\n\n')
        # writer.close()

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


class HTTPRequest():
    '''
    Class to store information about a request.
    '''
    def __init__(self, method, hostname, port, path, headers):
        self.method = method
        self.host = hostname
        self.port = port
        self.path = path
        self.headers = headers


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

    def connection_made(self, transport):
        '''
        Callback for when the network connection was successful.
        Forward the request to the remote server.
        '''
        self.transport = transport
        self.transport.write('GET {path} HTTP/1.1\nHost: {host}\nConnection: close\n\n'.format(**{
            'host': self.request.host,
            'path': self.request.path
        }).encode('iso-8859-1'))

    def data_received(self, data):
        '''
        Callback for when data was received over the network.
        Pass the data to the proxy session.
        '''
        self.proxysession.writer.write(data)

    def connection_lost(self, exc):
        '''
        Callback for when thenetwork connection is closed.
        Notify the proxy session to close.
        '''
        self.proxysession.writer.close()
