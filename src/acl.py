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

		:raises: ValueError if any of the items in the ACL are invalid CIDR notation
		'''

		# split up the comma-separated list of networks in CIDR notation 
		nets = list_cidr.split(',')

		# create empty list to store network objects
		self.networks = []

		for net in nets:
			try:
				self.networks.append(ipaddress.IPv4Network(net))

			except ValueError:
				raise ValueError('Invalid IP ACL {0}'.format(net))

	def ip_allowed(self, ip):
        '''
        Checks networks to see if the ip should be allowed to access the proxy.

        :return: True or False if the IP is allowed.
        :raises: ValueError if an invalid IP address is passed into the function.
        '''

		try:
			ip_address = ipaddress.IPv4Address(ip)

		except ValueError:
			raise ValueError('Invalid IP address {0}'.format(ip))

		for net in self.networks:
			if ip_address in net:
				return True

		return False
