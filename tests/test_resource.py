import unittest
import unittest.mock
import json

import resource
import config
import proxy


class TestResource(unittest.TestCase):
    @unittest.mock.patch('urllib.request.urlopen')
    def test_fetch_json(self, mock_urllib_request):
        json_payload = ('{'
                        '   "domain": ['
                        '       "adf.ly",'
                        '       "freakshare.com",'
                        '       "adsense.googleblog.com",'
                        '       "brightcove.com"'
                        '   ],'
                        '   "path": ['
                        '       ".*/advertisements/.*",'
                        '       ".*/ads/.*",'
                        '       ".*/tests/blacklist-path/.*"'
                        '   ],'
                        '   "misc": ['
                        '       "kalamari-proxy.github.io/tests/blacklist-misc/wildcard.*.txt"'
                        '   ]'
                        '}')

        json_payload = str.encode(json_payload)

        mock_urllib_request.return_value = unittest.mock.MagicMock()
        mock_urllib_request.return_value.read.return_value = json_payload

        data = resource.fetch_json(config.whitelist)

        self.assertEqual(len(data['domain']), 4)
        self.assertEqual(len(data['path']), 3)
        self.assertEqual(len(data['misc']), 1)

    @unittest.mock.patch('resource.fetch_json')
    def test_load_empty_ruleset(self, mock_fetch_json):
        mock_fetch_json.return_value = {}

        rl = resource.ResourceList()
        rl.load(config.blacklist)

        self.assertEqual(rl.domains, set())
        self.assertIsNone(rl.path_regex)
        self.assertIsNone(rl.full_regex)

    @unittest.mock.patch('resource.fetch_json')
    def test_load_domains(self, mock_fetch_json):
        DOMAINS = ['example.com', 'duckduckgo.com']
        mock_fetch_json.return_value = {'domain': DOMAINS}

        rl = resource.ResourceList()
        rl.load(config.whitelist)

        self.assertEqual(rl.domains, set(DOMAINS))

    @unittest.mock.patch('resource.fetch_json')
    def test_check_domain(self, mock_fetch_json):
        DOMAINS = ['example.com']
        mock_fetch_json.return_value = {'domain': DOMAINS}

        rl = resource.ResourceList()
        rl.load(config.blacklist)

        for domain in DOMAINS:
            request = proxy.HTTPRequest('GET', domain, 80, '/', {}, 1)
            self.assertTrue(rl.check(request))

        request = proxy.HTTPRequest('GET', 'gooddomain.com', 80, '/', {}, 1)
        self.assertFalse(rl.check(request))

    @unittest.mock.patch('resource.fetch_json')
    def test_check_path(self, mock_fetch_json):
        PATHS = ['.*/ads/.*']
        mock_fetch_json.return_value = {'path': PATHS}

        rl = resource.ResourceList()
        rl.load(config.blacklist)

        request = proxy.HTTPRequest('GET', 'bad.com', 80, '/ads/x', {}, 1)
        self.assertTrue(rl.check(request))
        request = proxy.HTTPRequest('GET', 'gooddomain.com', 80, '/', {}, 1)
        self.assertFalse(rl.check(request))

    @unittest.mock.patch('resource.fetch_json')
    def test_check_full(self, mock_fetch_json):
        MISC = ['example.com/ads/.*']
        mock_fetch_json.return_value = {'misc': MISC}

        rl = resource.ResourceList()
        rl.load(config.blacklist)

        request = proxy.HTTPRequest('GET', 'example.com', 80, '/ads/x', {}, 1)
        self.assertTrue(rl.check(request))
        request = proxy.HTTPRequest('GET', 'example.com', 80, '/good', {}, 1)
        self.assertFalse(rl.check(request))


class TestCacheList(unittest.TestCase):
    @unittest.mock.patch('resource.fetch_json')
    def test_check(self, mock_fetch_json):
        RULES = {'example\.com/file': 'test.com/file'}
        mock_fetch_json.return_value = RULES

        cl = resource.CacheList()
        cl.load(config.cachelist)

        request = proxy.HTTPRequest('GET', 'example.com', 80, '/file', {}, 1)
        self.assertEquals(cl.check(request), 'test.com/file')
        request = proxy.HTTPRequest('GET', 'example.com', 80, '/thing', {}, 1)
        self.assertIsNone(cl.check(request))

    @unittest.mock.patch('resource.fetch_json')
    def test_load_invalid_regex(self, mock_fetch_json):
        '''
        Test that loading an invalid regex does not raise an exception.
        '''
        RULES = {'exa(mple\.com/file': 'test.com/file'}
        mock_fetch_json.return_value = RULES

        cl = resource.CacheList()
        cl.load(config.cachelist)
