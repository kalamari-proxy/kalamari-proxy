import json
import urllib.request
import sys

blacklisturl = "https://kalamari-proxy.github.io/lists/blacklist.json"
whitelisturl = "https://kalamari-proxy.github.io/lists/whitelist.json" 
cachelisturl = "https://kalamari-proxy.github.io/lists/cachelist.json"

def obtainJSON(url):
req = urllib.request.urlopen(url)
data = req.read()

#pretty sure encoding will always be utf-8
#encoding = req.info().get_content_charset('utf-8')
data = json.loads(data.decode('utf-8'))
Return data


#testing access to json object
#print('\n')
#for d in json['domain']:
#   print (d)
#print('-------------')
#for p in json['path']:
#   print (p)
#print('-------------')
#for m in json['misc']:
#    print (m)
#print('\n')



class Resource_list(object):
    def __init__(self, data):
        self.data = data    # instance variable unique to each instance


    def check_Resource( urlToCheck ) 
	#Implement our regex
      return boolean
        
 

Whitelist = Resource_List(self, obtainJSON(whitelisturl))
Blacklist = Resource_List(self, obtainJSON(blacklisturl))
Cachelist = Resource_List(self, obtainJSON(cachelisturl))






#Pseudo code:
#Initialize Blacklist, Whitelist, and Cachelist JSON objects
#	Build for each list strings for regex (domain string, path string, misc string)
#	Build for each list a REGEX
#build classes:
#checkResource input:string , checks against BlackList REGEX output: boolean


