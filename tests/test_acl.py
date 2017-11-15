import unittest
import time
import acl
import config

class TestProxyServer(unittest.TestCase):
    def setUp(self):
        self.acl = acl.ACL(config.ip_acl)

    def test_valid_ips(self):
        self.assertTrue(self.acl.ip_allowed('192.168.1.1'))
        self.assertTrue(self.acl.ip_allowed('127.0.0.1'))

    def test_invalid_ips(self):
        self.assertFalse(self.acl.ip_allowed('192.168.2.1'))

    def test_invalid_acl_format(self):
        self.failUnlessRaises(ValueError, acl.ACL, '10.0.0.0/200')

    def test_invalid_ip_format(self):
        with self.assertRaises(ValueError):
            self.acl.ip_allowed('400.0.0.1')
