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
    Generic list class. Gets passed a url referring to Blacklist, Cachelist,
    or Whitelist. Produces json object and REGEX.
    '''
    def __init__(self):
        self.domains = set()
        self.path_regex = None
        self.full_regex = None

    def load(self, url):
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
        if request.host in self.domains:
            return True

        if self.path_regex is not None:
            if self.path_regex.match(request.path):
                return True

        if self.full_regex is not None:
            url = request.host + request.path
            if self.full_regex.match(url):
                return True

        return False
