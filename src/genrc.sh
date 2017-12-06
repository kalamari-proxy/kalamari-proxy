#!/bin/bash

echo Generating root certificate...
openssl req -nodes -newkey rsa:2048 -keyout ca.key -out ca.csr -days 5500 -subj "/C=US/ST=Wisconsin/L=Madison/O=Kalamari Proxy/OU=Kalamari Proxy/CN=Kalamari Proxy Root Certificate Authority X1" > /dev/null 2>&1
openssl x509 -req -days 365 -in ca.csr -signkey ca.key -out ca.crt > /dev/null 2>&1
rm ca.csr > /dev/null 2>&1
