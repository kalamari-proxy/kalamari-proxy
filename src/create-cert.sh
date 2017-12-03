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
    echo "Usage: $SCRIPTNAME -c common_name 
            [-s subject_alternative_name]
       -c common name for certificate
       -s subject alternative names in comma-separated format
"
}

# create the CSR and key file for signing
generateConfig() {
    # only do SAN stuff if SAN's present
    if [ -n "$SUBJECT_ALTERNATIVE_NAMES" ]; then
        echo "[ req ]
default_bits       = 2048
distinguished_name = req_distinguished_name
req_extensions     = req_ext
prompt             = no
[ req_distinguished_name ]
countryName                = US
stateOrProvinceName        = Wisconsin
localityName               = Madison
organizationName           = Kalamari Proxy
commonName                 = $COMMON_NAME
[ req_ext ]
subjectAltName = @alt_names
[alt_names]" > $COMMON_NAME.cfg

        declare -i dnsnum
        dnsnum=1
        sans=${SUBJECT_ALTERNATIVE_NAMES//,/ }
        IFS=' '
        for san in $sans; do
            echo "DNS.$dnsnum   = $san" >> $COMMON_NAME.cfg
            dnsnum=$((dnsnum+1))
        done
        
        # Run openssl to create csr and private key for signing
        openssl req -config $COMMON_NAME.cfg -nodes -new -newkey rsa:2048 -out $COMMON_NAME.csr -keyout $COMMON_NAME.key > /dev/null 2>&1
        RETVAL=$?
        
        # cleanup config file
        rm $COMMON_NAME.cfgh
    else 
        # generate CSR non-interactively without SAN's
        openssl req -nodes -new -newkey rsa:2048 -out $COMMON_NAME.csr -keyout $COMMON_NAME.key \
        -subj "/C=US/ST=Wisconsin/L=Madison/O=Kalamari Proxy/CN=$COMMON_NAME" > /dev/null 2>&1
        RETVAL=$?
    fi
    
    # make sure last operation completed successfully
    if [ $RETVAL -ne 0 ]; then
        logmessage "Could not create csr and key for $COMMON_NAME"
        exit 1
    fi
}

# create certificate with existing key and csr
signCertificate() {
    # check to see if csr or key does not exist
    if [ ! -r $COMMON_NAME.csr ] || [ ! -r $COMMON_NAME.key ]; then
        logmessage "Cannot read $COMMON_NAME.csr and or $COMMON_NAME.key"
        exit 1
    fi

    # sign csr - TODO: Doesn't work yet, no CA being generated
    openssl x509 -req -in $COMMON_NAME.csr -CA $CACRT -CAkey $CAKEY -CAcreateserial -out $COMMON_NAME.crt -days 365 -sha256
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
while getopts ":c:s:" opt; do
    case $opt in
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
if [ ! -n "$COMMON_NAME" ]; then
    echo Error: Must specify common name
    usage
    exit 1
fi

# generate CSR
generateConfig

# sign certificate
signCertificate
