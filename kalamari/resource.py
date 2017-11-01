import json
import urllib.request
import sys
import re

blacklisturl = "https://kalamari-proxy.github.io/lists/blacklist.json"
whitelisturl = "https://kalamari-proxy.github.io/lists/whitelist.json"
cachelisturl = "https://kalamari-proxy.github.io/lists/cachelist.json"

#function to obtain JSON object
def obtain_json(url):
    '''
    function to obtain JSON object
    '''
    req = urllib.request.urlopen(url)
    data = req.read()
    data = json.loads(data.decode('utf-8'))
    return data


def convert_json(jsonOBJ):
    '''
    function to convert domain path and misc into strings for regex
    '''
    domains = ""
    paths = ""
    miscs = ""
    strings = []
    for d in jsonOBJ['domain']:
        domains = domains + d + "|"
    domains = domains[:-1]

    for p in jsonOBJ['path']:
        paths = paths + p + "|"
    paths = paths[:-1]

    for m in jsonOBJ['misc']:
        miscs = miscs + m + "|"
    miscs = miscs[:-1]

    strings.append(domains)
    strings.append(paths)
    strings.append(miscs)
    return strings


class ResourceList:
    '''
    Generic list class. Gets passed a url referring to Blacklist, Cachelist,
    or Whitelist. Produces json object and REGEX.
    '''
    def __init__(self,json):
        self.json = obtain_json(json)    # json object unique to each instance
        strings = convert_json(self.json)
        self.regex = re.compile(r'http://' + r'(' + strings[0]+ r')' + r'('+strings[1]+r')' + r'(.*)' )


Blacklist = ResourceList(blacklisturl)
Whitelist = ResourceList(whitelisturl)
Cachelist = ResourceList(cachelisturl)


class CheckBlack:
    '''
    Checks url request against Blacklist REGEX. Returns True if request matches
    REGEX.
    '''
    def __init__(self,request):
        self.request = request
        match = Blacklist.regex.match(request)
        if match:
            result = True
        else:
            result = False
        print (result)

class CheckWhite:
    '''
    Checks url request against Whitelist REGEX. Returns True if request matches
    REGEX.
    '''
    def __init__(self,request):
        self.request = request
        match = Whitelist.regex.match(request)
        if match:
            result = True
        else:
            result = False
        return result

class CheckCache:
    '''
    Checks url request against Cachelist REGEX. Returns True if request matches
    REGEX.
    '''
    def __init__(self,request):
        self.request = request
        match = Cachelist.regex.match(request)
        if match:
            result = True
        else:
            result = False
        return result



print(Blacklist.regex)

CheckBlack('http://adf.ly/ads/.facebook.com/somedir/something.js')
CheckBlack('http://freakshare.com/advertisements/blahblahblah')
CheckBlack('http://False.com/advertisements/')
