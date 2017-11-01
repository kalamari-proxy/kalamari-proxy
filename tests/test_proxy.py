import unittest
import proxy

class TestProxyServer(unittest.TestCase):
    def test_parse_method(self):
        METHOD = 'GET http://example.com/ HTTP/1.1'
        method, target, version = proxy.ProxyServer.parse_method(METHOD)

        self.assertEqual(method, 'GET')
        self.assertEqual(target, 'http://example.com/')
        self.assertEqual(version, 'HTTP/1.1')

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
