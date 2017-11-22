import unittest
import unittest.mock

import asyncio
import time
import proxy


class TestProxyServer(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    @unittest.mock.patch('proxy.ProxyServer.start_periodic_refresh')
    def test_init_starts_periodic_refresh(self, mock_start_refresh):
        proxy.ProxyServer(self.loop)
        self.assertTrue(mock_start_refresh.called)
    
    def test_parse_method(self):
        METHOD = 'GET http://example.com/ HTTP/1.1'
        method, target, version = proxy.ProxyServer.parse_method(METHOD)

        self.assertEqual(method, 'GET')
        self.assertEqual(target, 'http://example.com/')
        self.assertEqual(version, 'HTTP/1.1')

    def test_parse_method_missing_verb(self):
        METHOD = ''
        with self.assertRaises(ValueError):
            proxy.ProxyServer.parse_method(METHOD)

    def test_parse_method_without_version(self):
        METHOD = 'GET http://example.com/'
        with self.assertRaises(ValueError):
            proxy.ProxyServer.parse_method(METHOD)

    def test_parse_method_without_target(self):
        METHOD = 'GET http://example.com/'
        with self.assertRaises(ValueError):
            proxy.ProxyServer.parse_method(METHOD)

    def test_parse_method_with_empty_message(self):
        METHOD = ''
        with self.assertRaises(ValueError):
            proxy.ProxyServer.parse_method(METHOD)

    def test_parse_url(self):
        URL = 'http://example.com/hello_world'
        host, port, path = proxy.ProxyServer.parse_url(URL)

        self.assertEqual(host, 'example.com')
        self.assertEqual(port, 80)
        self.assertEqual(path, '/hello_world')

    def test_parse_url_with_query(self):
        URL = 'http://example.com/hello_world?q=hello'
        host, port, path = proxy.ProxyServer.parse_url(URL)

        self.assertEqual(host, 'example.com')
        self.assertEqual(port, 80)
        self.assertEqual(path, '/hello_world?q=hello')

    def test_parse_headers(self):
        class MockReader():
            def __init__(self):
                self.lines = [b'Host: example.com\n', b'Test: value\n', b'\n']

            async def readline(self):
                return self.lines.pop(0)

        async def run_async_test():
            headers = await proxy.ProxyServer.parse_headers(MockReader())
            self.assertEqual(headers['host'], 'example.com')
            self.assertEqual(headers['test'], 'value')
            self.assertEqual(len(headers), 2)

        self.loop.run_until_complete(run_async_test())

    def test_start_periodic_refresh_with_negative_interval(self):
        self.assertIsNone(proxy.ProxyServer.start_periodic_refresh(None, -1))


class TestHTTPRequest(unittest.TestCase):
    def test_timed_out(self):
        request = proxy.HTTPRequest('GET', 'example.com', 80, '/', {}, 1)
        self.assertFalse(request.timed_out())

        request.time = time.time() - 1000
        self.assertTrue(request.timed_out())


class TestProxySessionOutput(unittest.TestCase):
    def setUp(self):
        self.mock_proxysession = unittest.mock.MagicMock()
        self.mock_request = unittest.mock.MagicMock()
        
        self.session = proxy.ProxySessionOutput(self.mock_proxysession,
                                                self.mock_request)

    def test_ready_before_calling_connection_made(self):
        '''
        Test that ready() returns False before connection_made is
        called.
        '''
        self.assertFalse(self.session.ready())

    def test_connection_made_method_connect(self):
        self.mock_request.method = 'CONNECT'
        mock_transport = unittest.mock.MagicMock()

        self.session.connection_made(mock_transport)

        self.assertTrue(self.mock_proxysession.writer.write.called)
        self.assertFalse(mock_transport.write.called)
        self.assertTrue(self.session.ready())

    def test_connection_made_method_get(self):
        self.mock_request.method = 'GET'
        transport = unittest.mock.MagicMock()
        self.session.connection_made(transport)

        self.assertFalse(self.mock_proxysession.writer.write.called)
        self.assertTrue(self.session.ready())

    def test_data_received_passes_data_to_proxysession(self):
        self.session.data_received(b'data')
        self.assertTrue(self.mock_proxysession.writer.write.called)

    def test_connection_lost_closes_proxysession_writer(self):
        self.session.connection_lost(None)
        self.assertTrue(self.mock_proxysession.writer.close.called)
