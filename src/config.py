#import logging
import os

DEFAULT_REFRESH = 3600
DEFAULT_TIMEOUT = 150

blacklist = os.getenv('BLACKLIST',
                      'https://kalamari-proxy.github.io/lists/blacklist.json')
whitelist = os.getenv('WHITELIST',
                      'https://kalamari-proxy.github.io/lists/whitelist.json')
cachelist = os.getenv('CACHELIST',
                      'https://kalamari-proxy.github.io/lists/cachelist.json')
ip_acl = os.getenv('IP_ACL', '192.168.1.0/24,127.0.0.0/8,172.17.0.1/32')

try:
    list_refresh = int(os.getenv('REFRESH', DEFAULT_REFRESH))
except ValueError:
    logging.warn('Could not parse REFRESH environment variable an an integer.')
    list_refresh = DEFAULT_REFRESH

webserver_ip = os.getenv('WEBSERVER_IP', '127.0.0.1')
webserver_port = os.getenv('WEBSERVER_PORT', '8080')

try:
    timeout = os.getenv('TIMEOUT', DEFAULT_TIMEOUT)
except ValueError:
    logging.warn('Could not parse TIMEOUT environment variable as an integer.')
    timeout = DEFAULT_TIMEOUT
