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

        # Send a default response. TODO: change this.
        writer.write(b'HTTP/1.1 404 Not Found\n\n')
        writer.close()

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
                raise ValueError('Line too long while parsing  header')
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
    def __init__(method, hostname, url, headers):
        self.method = method
        self.hostname = hostname
        self.url = url


class ProxySession():
    '''
    Manages communication between the client and Kalamari and between
    Karamari and the request destination.
    '''
    def __init__(self, reader, writer, request):
        self.reader = reader
        self.writer = writer
        self.request = request
