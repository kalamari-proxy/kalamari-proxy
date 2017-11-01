import unittest
import proxy

class TestProxyServer(unittest.TestCase):
    def test_parse_method(self):
        METHOD = 'GET http://example.com/ HTTP/1.1'
        method, target, version = proxy.ProxyServer.parse_method(METHOD)

        self.assertEqual(method, 'GET')
        self.assertEqual(target, 'http://example.com/')
        self.assertEqual(version, 'HTTP/1.1')
