import json
import urllib.request
import sys

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
    for p in jsonOBJ['path']:
        paths = domains + p + "|"
    for m in jsonOBJ['misc']:
        miscs = domains + m + "|"
    strings.append(domains)
    strings.append(paths)
    strings.append(miscs)
    return strings

# Generic list class
class Resource_list():
    def __init__(self,json):
        self.json = obtainJSON(json)    # instance variable unique to each instance
        #build regex here

Blacklist = Resource_list(blacklisturl)

#sanity check
#print(Blacklist.json['domain'])
#print("-------------------")
s = jsonTOstrings(Blacklist.json)
print(s[0])
print("-------------------")
print(s[1])
print("-------------------")
print(s[2])
