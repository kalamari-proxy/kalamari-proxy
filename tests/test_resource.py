import unittest
import unittest.mock

import resource
import config
import proxy


class TestResource(unittest.TestCase):
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
