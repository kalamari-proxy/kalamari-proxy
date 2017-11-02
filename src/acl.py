import logging
import ipaddress
# Module Doc: https://docs.python.org/3/library/ipaddress.html

class ACL():
	'''
	This module handles the ACL logic and determines whether a given client should be allowed to connect to the ProxyServer and make requests
	Networks are specified in CIDR format, see doc here: https://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing
	'''

	def __init__(self, list_cidr):
		'''
		Constructor for ACL class
		'''

		# split up the comma-separated list of networks in CIDR notation 
		nets = list_cidr.split(',')

		# create empty list to store network objects
		self.networks = []

		for net in nets:
			try:
				self.networks.append(ip_network(net))

			except ValueError, ex:
				logging.error('Invalid IP ACL network {0}'.format(net))
				raise 'Invalid IP ACL network {0}'.format(net)


	def ip_allowed(self, ip):
		"""
		Checks networks to see if the ip should be allowed to access the proxy. 

		:return: True or False if the IP is allowed.
        :raises: ValueError if a line longer than MAXLINE characters is
          discovered.
        :raises: ValueError if more than MAXHEADERS headers are
          discovered.
		"""

		return True
