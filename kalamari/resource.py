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
        # self.strings = jsonTOstrings(self.json)
        self.regex = re.compile('http')

#will need to initialize these in their own function (refresh)
Blacklist = Resource_list(blacklisturl)
Whitelist = Resource_list(whitelisturl)
Cachelist = Resource_list(cachelisturl)

# Not how to set up these classes
class Check_black:
    def __init__(self,request):
            self.request = request

    match = Blacklist.regex.match(request)
    if match:
        result = True
    else:
        result = False
        def f(self):
            return result



class Check_white:
    def __init__(self,request):
            self.request = request
            
    match = Whitelist.regex.match(request)
    if match:
        result = True
    else:
        result = False
        def f(self):
            return result

class Check_cache:
    def __init__(self,request):
            self.request = request
    match = Cachelist.regex.match(request)
    if match:
        result = True
    else:
        result = False
        def f(self):
            return result

#sanity check
#print(Blacklist.json['domain'])
#print("-------------------")
s = jsonTOstrings(Blacklist.json)
print(s[0])
print("-------------------")
print(s[1])
print("-------------------")
print(s[2])
