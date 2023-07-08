#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2023 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: Apache-2.0

CMD=$1

# Encrypt
if [[ $CMD == "encrypt" ]]; then
    pass=$2
    vaultpw=$(echo -n "$pass" | ansible-vault encrypt_string 2> /dev/null)

# Decrypt
elif [[ $CMD == "decrypt" ]]; then
    host=$2
    var=$3

    # run ansible msg for variable
    # send return as JSON
    vaultpw=$(ANSIBLE_LOAD_CALLBACK_PLUGINS=1 ANSIBLE_STDOUT_CALLBACK=json ansible "$host" -m debug -a "msg={{$var}}" 2> /dev/null)
    # Parse JSON to just get the "msg"
    vaultpw=$(jq -r ".plays[].tasks[].hosts[].msg" <<< "$vaultpw")

else
    echo "Invalid command"
    echo ""
    echo "Usage:"
    echo "ansible-vault-tools encrypt <password>"
    echo "ansible-vault-tools decrypt <host> <variable>"
    exit 1
fi

echo "$vaultpw"
