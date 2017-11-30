#!/bin/bash

SCRIPTNAME=`basename $0`
CACRT=./ca.crt
CAKEY=./ca.key

#############
# Functions #
############

# logs name of script and error to console
logmessage() {
    echo $SCRIPTNAME: $1
}

# prints usage for help text
usage() {
    echo "Usage: $SCRIPTNAME -n session# -c common_name 
            [-s subject_alternative_name]
       -n session number to use for naming files while working
       -c common name for certificate
       -s subject alternative names in comma-separated format
"
}

# create the CSR and key file for signing
generateConfig() {
    echo "[ req ]
default_bits       = 2048
distinguished_name = req_distinguished_name
req_extensions     = req_ext
[ req_distinguished_name ]
countryName                 = US
stateOrProvinceName         = Wisconsin
localityName               = Madison
organizationName           = Kalamari Proxy
commonName                 = $COMMON_NAME" > $SESSION_NUMBER.cfg
#[ req_ext ]
#subjectAltName = @alt_names
#[alt_names]
#DNS.1   = bestflare.com
#DNS.2   = usefulread.com
#DNS.3   = chandank.com" > $SESSION_NUMBER.cfg

    # Run openssl to create csr and private key for signing
}

# create certificate with existing key and csr
signCertificate() {
    # check to see if csr or key does not exist
    if [ ! -r $SESSION_NUMBER.csr ] || [ ! -r $SESSION_NUMBER.key ]; then
        logmessage "Cannot read $SESSION_NUMBER.csr and or $SESSION_NUMBER.key"
        exit 1
    fi
}

########
# Main #
########

# see if key and cert exist and are readable
if [ ! -r $CACRT ] || [ ! -r $CAKEY ]; then
    logmessage "Either $CAKEY or $CACRT does not exist or is not readable"
    exit 1
fi

# process flags
while getopts ":n:c:s:" opt; do
    case $opt in
        n)
            SESSION_NUMBER=$OPTARG
            ;;
        c)
            COMMON_NAME=$OPTARG
            ;;
        s)
            SUBJECT_ALTERNATIVE_NAMES=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            exit 1
            ;;
    esac
done

# make sure mandatory options set
if [ ! -n "$SESSION_NUMBER" ]; then
    echo Error: Must specify session number
    usage
    exit 1
fi
if [ ! -n "$COMMON_NAME" ]; then
    echo Error: Must specify common name
    usage
    exit 1
fi

# generate CSR
generateConfig

# sign certificate
signCertificate

# cleanup
cleanup
