'''
Integration tests which make full use of all proxy components.
'''
import unittest
import requests

proxies = {
    'http': 'http://127.0.0.1:3128'
}

class TestConnectExternalWebsites(unittest.TestCase):
    '''
    Tests that connect to external websites.
    '''
    def test_get_example_com(self):
        '''
        Test connection to example.com.
        '''
        r = requests.get('http://example.com', proxies=proxies)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Example Domain', r.text)

    def test_get_mozilla_detectportal(self):
        '''
        Test connection by requesting Mozilla's portal detection page.
        http://detectportal.firefox.com/success.txt
        '''
        r = requests.get('http://detectportal.firefox.com/success.txt',
                         proxies=proxies)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, 'success\n')
