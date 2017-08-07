#!/bin/bash

##!
#
# This script sets up a basic server configuration.
#
# First, it generates or links to certificates for HTTPS.
# It takes one argument for determining the openssl flag
# for the passphrase protocol.
# Valid options for generating passwords are:
#
# - ``-aes128``
# - ``-aes192``
# - ``-aes256``
#
# To link to an existing key instead, pass the option::
#
#     ./setup_server.sh -link
#
# The script performs the following steps:
#
# #. Creates a ``keys`` directory
# #. - Prompts for the locations of private key and certificates to create softlinks
#      if the softlinks option is passed.
#    - Otherwise, a ``keys/privkey.pem`` with the password flag passed is created
#      along with a cert.pem to use for SSL connections
# #. Generates a random list of salts from ``generatesalt.py``
# #. Copies a example ``config.yml`` to the working directory
#
# If the certificate is not linked, it is self-signed and valid for one year.
#
# After completing these steps, the script reminds the user to edit ``config.yml``.
#
##!

passwordopt=$1

if [ ! -d keys ]
then
    mkdir keys
fi

if [ "$passwordopt" = "-link" ]
then
    echo "What is the location of your private key:"
    read privlocation
    echo "What is the location of your SSL certificate:"
    read certlocation

    if [ -f $privlocation ]
    then
        ln -s $privlocation keys/privkey.pem
    else
        echo "Cannot find file $privlocation"
        exit 1
    fi

    if [ -f $certlocation ]
    then
        ln -s $certlocation keys/cert.pem
    else
        echo "Cannot find file $certlocation"
        exit 1
    fi

fi

if [ ! -f keys/privkey.pem ]
then
    openssl genrsa "$passwordopt" -out keys/privkey.pem 2048
    openssl req -new -x509 -days 365 -key keys/privkey.pem -out keys/cert.pem
fi

if [ ! -f keys/salt.txt ]
then
    python -mgeneratesalt > keys/salt.txt
fi

if [ ! -f config.yml ]
then
    cp ../test/config.yml .
fi

echo "Do not forget to edit the configuration file:"
echo ""
echo " config.yml"
echo ""
