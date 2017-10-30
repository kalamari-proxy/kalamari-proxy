import json
import urllib.request
import sys
import re

blacklisturl = "https://kalamari-proxy.github.io/lists/blacklist.json"
whitelisturl = "https://kalamari-proxy.github.io/lists/whitelist.json"
cachelisturl = "https://kalamari-proxy.github.io/lists/cachelist.json"

#function to obtain JSON object
def obtainJSON(url):
    req = urllib.request.urlopen(url)
    data = req.read()

#pretty sure encoding will always be utf-8
#encoding = req.info().get_content_charset('utf-8')
    data = json.loads(data.decode('utf-8'))
    return data

#function to convert domain path and misc into strings for regex
def jsonTOstrings(jsonOBJ):
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

# Generic list class
class Resource_list():
    def __init__(self,json):
        self.json = obtainJSON(json)    # json object unique to each instance
        #build regex here, will implement the jsonTOstrings function being printed below
        # current regex is not correct
        self.strings = jsonTOstrings(self.json)
        self.regex = re.compile('[.]*'(self.strings[0])'[.]*'(self.strings[1])'[.]*'(slef.strings[2]'[.]*')

Blacklist = Resource_list(blacklisturl)
Whitelist = Resource_list(whitelisturl)
Cachelist = Resource_list(cachelisturl)

# Not sure exactly what to return
class Check_black(urlTocheck):
    match = Blacklist.regex.match('urlTocheck')
    if match:
        return 1
    else:
        return -1



class Check_white(urlTocheck):
    match = Whitelist.regex.match('urlTocheck')
    if match:
        return 1
    else:
        return -1

class Check_cache('urlTocheck'):
    match = Cachelist.regex.match('urlTocheck')
    if match:
        return 1
    else:
        return -1
#sanity check
#print(Blacklist.json['domain'])
#print("-------------------")
s = jsonTOstrings(Blacklist.json)
print(s[0])
print("-------------------")
print(s[1])
print("-------------------")
print(s[2])
