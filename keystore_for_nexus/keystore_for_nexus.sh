#!/bin/bash

# created:    20260312 / alphabeit
# lastupdate: 20260317 / alphabeit

# Alphabeit https://github.com/Alphabeit
# no license, feel free to use

#=========================================================
# DESC
#=========================================================
#  When using a Nexus Repository Manager (Nexus) and RetHat Enterprise Linux (RHEL) systems, it 
# could be for intrest to use the Nexus, to proxy the packages of the RHEL sources. In that case,
# the Nexus require a certificate (Keystore) created by a RHEL system with an active subscription.
# See also https://help.sonatype.com/en/proxying-rhel-yum-repositories.html for more infos by
# Sonatype (Company behind Nexus).
#
# This Ansible module is made for creating and receiving these Keystore files. 
#
#  It will only create the Keystore files, receive and offers them by 'REGISTER.content_keystone' in
# base64 encoding. It didint load them into the Nexus Store (you have to do this by you own). Please
# dont forget you have to decode them back from base64. 
# 
# The moudle have to get executed on a RHEL system with an active subscription. Created and testet 
# was the module on a RHEL 10 system.





#=========================================================
# REQU
#=========================================================
# Please ensure:
# > openssl is installed.
# > keystore is installed.
# > Destination System is a RHEL system and have an active subscription.
# > Module is correct loaded (I placed it intro the ../libary).
#  > ├── inventory
#    │   └── inventory.ini
#    ├── library                   <- 
#    │   └── keystore_for_nexus.sh <- 
#    ├── playbooks
#    │   ├── ansible.cfg





#=========================================================
# EXAMPLES
#=========================================================
#
# - name: create and read keystore
#   keystore_for_nexus:
#     password: "pa$$w0rd"
#   delegate_to: RHEL10_0815
#   register: keystore_value
#
# - name: save keystore on nexus
#   ansible.builtin.copy:
#     dest: /etc/nexus/store/keystore.p12
#     content: "{{ keystore_value.content_keystone | b64decode }}"
#     owner: nexus
#     group: nexus
#     mode: 0644
#   delegate_to: NEXUS
#





#=========================================================
# FUNCS
#=========================================================
#
 #============================
# Tools Check
#============================
# Prove, if openssl and keytool exists

function tools_check {

    # prove openssl
    if [ ! -f /usr/bin/openssl ]; then
        result_of_openssl_check=false
    else
        result_of_openssl_check=true
    fi

    # prove keytool
    if [ ! -f /usr/bin/keytool ]; then
        result_of_keytool_check=false
    else
        result_of_keytool_check=true
    fi
}



 #============================
# Subscription Check
#============================
# RHEL System have to need an active subscribtion.

function subscription_check {

    result_of_subscription_check=true

    # check subscription, save error code
    subscription-manager status | grep Registered > /dev/null 2>&1
    local exit_code=$(echo $?)

    # when error code isnt success
    if [ $exit_code -ne 0 ]; then
        result_of_subscription_check=false
    else
        result_of_subscription_check=true
    fi
}



 #============================
# Certificates Check
#============================
# Keystore get created from certificates of subscription. So they been also required.

function certification_check {

    # fetch key by keyword 'key' 
    local key=$(ls -A1 /etc/pki/entitlement | grep key)
    local key_count=$(echo $key | wc -l)
    path_key=$(echo /etc/pki/entitlement/$key)

    # fetch cert by invert the match of keyword 'key' 
    local cert=$(ls -A1 /etc/pki/entitlement | grep --invert-match key)
    local cert_count=$(echo $cert | wc -l)
    path_cert=$(echo /etc/pki/entitlement/$cert)

    # when result files isnt less or more as one
    if [ $key_count -ne 1 ] || [ $cert_count -ne 1 ]; then
        result_of_certification_check=false
    else
        result_of_certification_check=true
    fi
}



 #============================
# Create Keystore
#============================

function create_keystore {

    # combine key and cert
    openssl pkcs12 -export -in $path_cert -inkey $path_key -name certificate_and_key -out certificate_and_key.p12 -passout pass:$password -nodes 

    # convert to keystore
    keytool -importkeystore -srckeystore certificate_and_key.p12 -srcstoretype PKCS12 -srcstorepass $password -deststorepass $password -destkeystore keystore.p12 -deststoretype PKCS12 > /dev/null 2>&1

    # when file didint exists
    if [ ! -f keystore.p12 ]; then
        result_of_create_keystore=false
    else
        result_of_create_keystore=true

        # write msg for print
        msg="Keystore got created. Content avaliable as base64 by REGISTER.content_keystone ."
        content_keystone=$(base64 -w0 keystore.p12)

        # clean up
        rm -f keystore.p12 > /dev/null 2>&1
        rm -f certificate_and_key.p12 > /dev/null 2>&1
    fi
}





#=========================================================
# EXEC
#=========================================================
# Execute module. 

# load vars 
source $1

# module runs fine
msg=""
content_keystone=""

# require $password for Keystore
if [ -z "$password" ]; then
    printf '{"failed": true, "msg": "Missing required arguments: password"}'
    exit 1
fi

# prove requirment tools
tools_check
if [ ! "$result_of_openssl_check" ]; then
    printf '{"failed": true, "msg": "Couldnt find openssl. Please ensure, programm is installed and avaliable by $PATH."}'
    exit 1
elif [ ! "$result_of_keytool_check" ]; then
    printf '{"failed": true, "msg": "Couldnt find keytool. Please ensure, programm is installed and avaliable by $PATH"}'
    exit 1
fi

# when subscription_check failed, stop module
subscription_check
if [ ! "$result_of_subscription_check" ]; then
    printf '{"failed": true, "msg": "Subscription check failed. Is the system you use a RHEL system and have it an active subscription?"}'
    exit 1
fi

# when certificates not found, stop module
certification_check
if [ ! "$result_of_certification_check" ]; then
    printf '{"failed": true, "msg": "Module coulndt find certificates in /etc/pki/entitlement, who required to create Keystore."}'
    exit 1
fi

# create keystore
create_keystore
# stop module when keystore file didint got created
if [ ! "$result_of_create_keystore" ]; then
    printf '{"failed": true, "msg": "Module coulndt created keystore file."}'
    exit 1
fi

# when keystore file got created
# func create_keystore had override msg and content_keystone
printf '{"changed": true, "msg": "%s", "content_keystone": "%s"}' "$msg" "$content_keystone"
exit 0




