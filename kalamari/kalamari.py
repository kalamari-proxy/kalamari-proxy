#! /usr/bin/env python3
import asyncio
import http.client
import email.parser
import http.client


class ProxyServer():
    MAXLINE = 65536
    MAXHEADERS = 100

    def __init__(self, loop):
        self.loop = loop
    
    async def proxy_server_handler(self, reader, writer):
        method_line = await reader.readline()
        print('method:', method_line)
        
        headers = await self.parse_headers(reader)
        for header, value in headers.items():
            print('%s: %s' % (header, value))

        writer.write(b'HTTP/1.1 404 Not Found\n\n')
        writer.close()
        print()

    @classmethod
    async def parse_headers(cls, reader):
        '''
        Port the HTTP header parsing code from the Python standard
        library to use asyncio.
        https://github.com/python/cpython/blob/3.6/Lib/http/client.py
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


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    proxy = ProxyServer(loop)
    coro = asyncio.start_server(proxy.proxy_server_handler, 'localhost', 3128,
                                loop=loop)
    server = loop.run_until_complete(coro)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
