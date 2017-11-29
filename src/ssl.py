import logging
import asyncio
import subprocess

class CertificateAuthority():
    '''
    This module handles the ACL logic and determines whether a given client should be allowed to connect to the ProxyServer and make requests
    Networks are specified in CIDR format, see doc here: https://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing
    '''

    def __init__(self, password):
        '''
        Constructor for Certificate Authority
        '''  

        # load the root CA from the filesystem
        load_root_authority()

    def __sys_call(self):
        '''
        Checks networks to see if the ip should be allowed to access the proxy.

        :return: runs a script and 
        '''

        pass

    def load_root_authority(self):
        '''
        Checks networks to see if the ip should be allowed to access the proxy.

        :return: a CertificateKeyPair with the key and the pair for a certificate
        '''

        try:
            # read the key file
            key_file = open('rootCA.key', 'r')
            root_key = key_file.read()

            # read the crt file
            crt_file = open('rootCA.crt', 'r')
            root_crt = crt_file.read()

            self.root_pair = CertificateKeyPair(root_key, root_crt)

        except IOError:
            logging.error('Could not load root certificate authority key file and or certificate')

    def generate_cert(self, cn):
        '''
        Checks networks to see if the ip should be allowed to access the proxy.

        :return: a CertificateKeyPair with the key and the pair for a certificate
        '''

        pass

class CertificateKeyPair():
    '''
    This module functions as a structure to hold a certificate key pair
    '''

    def __init__(self, key, cert):
        '''
        Constructor for a CertificateKeyPair without a password
        '''

        self.key = key
        self.cert = cert
