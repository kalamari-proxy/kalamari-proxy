'''
Integration tests which make full use of all proxy components.
'''
import unittest
import hashlib
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

    def test_get_duckduckgo_https(self):
        '''
        Test connection by requesting https://duckduckgo.com and checking
        that the status code is 200 and "DuckDuckGo" is in the response.
        '''
        r = requests.get('https://duckduckgo.com/', proxies=proxies)
        self.assertEqual(r.status_code, 200)
        self.assertIn('DuckDuckGo', r.text)

    def test_get_github_redirect(self):
        '''
        Test connection by requesting http://github.com/ and checking
        that we are redirected.
        '''
        r = requests.get('http://github.com/', proxies=proxies)
        self.assertEqual(r.history[0].status_code, 301)
        self.assertEqual(r.url, 'https://github.com/')
        
    def test_blocked_resource(self):
        '''
        Test blocked resource response by requesting a resource that appears
        on the blacklist
        '''
        r = requests.get('http://freakshare.com/',proxies=proxies)
        self.assertEqual(r.status_code, 404)
        
    def test_get_example_cached3(self):
        '''
        Test cached resource functionality by requesting
        http://example.com/cached3 and checking that the exxpected file
        is returned.
        '''
        r = requests.get('http://example.com/cached3', proxies=proxies)
        self.assertEqual(r.status_code, 200)
        filehash = hashlib.sha1(r.content).hexdigest()
        self.assertEqual(filehash, 'cf596a256c0b1c49a725a394dba3f6c968ad077c')
