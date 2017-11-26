import re
import json
import urllib.request


def fetch_json(url):
    '''
    Download JSON data and parse it.
    '''
    req = urllib.request.urlopen(url)
    data = req.read()
    data = json.loads(data.decode('utf-8'))
    return data


class ResourceList():
    '''
    Stores a ruleset and allows checking a request against the ruleset.
    '''
    def __init__(self):
        self.domains = set()
        self.path_regex = None
        self.full_regex = None

    def load(self, url):
        '''
        Download a ruleset from a given URL.
        '''
        ruleset = fetch_json(url)

        if 'domain' in ruleset:
            self.domains = set(ruleset['domain'])
        else:
            self.domains = set()

        if 'path' in ruleset:
            self.path_regex = re.compile('|'.join(ruleset['path']))
        else:
            self.path_regex = None

        if 'misc' in ruleset:
            self.full_regex = re.compile('|'.join(ruleset['misc']))
        else:
            self.full_regex = None

    def check(self, request):
        '''
        Indicate whether a request matches the blacklist.
        :param request HTTPRequest:
        '''
        host_parts = request.host.split('.')
        for i in range(len(host_parts)):
            if '.'.join(host_parts[i:]) in self.domains:
                return True

        if self.path_regex is not None:
            if self.path_regex.match(request.path):
                return True

        if self.full_regex is not None:
            url = request.host + request.path
            if self.full_regex.match(url):
                return True

        return False


class CacheList():
    '''
    Holds a cached resource ruleset and allows checking a request for
    a better location to load the cached resource from.
    '''
    def __init__(self):
        self.resources = dict()

    def load(self, url):
        ruleset = fetch_json(url)

        for rule, url in ruleset.items():
            try:
                rule_regex = re.compile(rule)
            except Exception as err:
                continue  # skipping invalid regex
            self.resources[re.compile(rule)] = url

    def check(self, request):
        '''
        :return: a new URL as a string or None if no rule matches.
        '''
        url = request.host + request.path
        for rule, redirect in self.resources.items():
            if rule.match(url):
                return redirect

        return None
