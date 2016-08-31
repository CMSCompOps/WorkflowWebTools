#!/bin/bash

##!
# .. describe:: setup_server.sh
#
# :author: Daniel Abercrombie <dabercro@mit.edu>
#
# This script sets up a basic server configuration.
# It takes one argument for determining the openssl flag
# for the passphrase protocol.
# Valid options for generating passwords are:
#
# - -aes128
# - -aes192
# - -aes256
#
# The script performs the following steps:
#
# #. Creates a ``keys`` directory
# #. Generates a ``keys/privkey.pem`` with the password flag you passed
# #. Generates a random list of salts from ``generatesalt.py``
# #. Copies a example ``config.yml`` to the working directory
# #. Creates a cert.pem to use for SSL connections
#
# If any of the files usually generated by the first four steps are
# already present, the step is skipped.
# The certificate is self-signed and valid for one year.
#
# After completing these steps, the script reminds the user to edit ``config.yml``.
##!

passwordopt=$1

if [ ! -d keys ]
then
    mkdir keys
fi

if [ ! -f keys/privkey.pem ]
then
    openssl genrsa $passwordopt -out keys/privkey.pem 2048
fi

if [ ! -f keys/salt.txt ]
then
    python -mgeneratesalt > keys/salt.txt
fi

if [ ! -f config.yml ]
then
    cp ../test/config.yml .
fi

openssl req -new -x509 -days 365 -key keys/privkey.pem -out keys/cert.pem

echo "Do not forget to edit the configuration file:"
echo ""
echo " config.yml"
echo ""