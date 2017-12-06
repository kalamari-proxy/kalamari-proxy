#!/bin/bash
 
#Required
domain=kalamari-proxy.github.io
commonname=$domain
 
#Change to your company details
country=US
state=Wisconsin
locality=Dane
organization=Kalamari-Proxy
organizationalunit=Mantis_Shrimp
email=sahowell@wisc.edu
 
#Optional
password=dummypassword
 
if [ -z "$domain" ]
then
    echo "Argument not present."
    echo "Useage $0 [common name]"
 
    exit 99
fi
 
echo "Generating key request for $domain"
 
#Generate a key
openssl genrsa -passout pass:$password -out $domain.key 2048 -noout
 
#Create the request
echo "Creating CSR"
openssl req -new -key $domain.key -out $domain.csr -passin pass:$password \
    -subj "/C=$country/ST=$state/L=$locality/O=$organization/OU=$organizationalunit/CN=$commonname/emailAddress=$email"
 
echo "---------------------------"
echo "-----Below is your CSR-----"
echo "---------------------------"
echo
cat $domain.csr
 
echo
echo "---------------------------"
echo "-----Below is your Key-----"
echo "---------------------------"
echo
cat $domain.key
