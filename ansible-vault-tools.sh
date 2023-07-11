#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2023 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: Apache-2.0

CMD=$1

# Encrypt string
if [[ $CMD == "encrypt-string" ]]; then
    pass=$2
    vaultpw=$(echo -n "$pass" | ansible-vault encrypt_string 2> /dev/null)

# Decrypt string
elif [[ $CMD == "decrypt-string" ]]; then
    host=$2
    var=$3

    # run ansible msg for variable
    # send return as JSON
    vaultpw=$(ANSIBLE_LOAD_CALLBACK_PLUGINS=1 ANSIBLE_STDOUT_CALLBACK=json ansible "$host" -m debug -a "msg={{$var}}" 2> /dev/null)
    # Parse JSON to just get the "msg"
    vaultpw=$(jq -r ".plays[].tasks[].hosts[].msg" <<< "$vaultpw")

# Encrypt file
elif [[ $CMD == "encrypt-file" ]]; then
    file=$2
    ansible-vault encrypt "$file"

# Decrypt file
elif [[ $CMD == "decrypt-file" ]]; then
    file=$2
    ansible-vault decrypt "$file"

else
    echo "Invalid command"
    echo ""
    echo "Usage:"
    echo "ansible-vault-tools encrypt-string <password>"
    echo "ansible-vault-tools decrypt-string <host> <variable>"
    echo ""
    echo "ansible-vault-tools encrypt-file <file-path>"
    echo "ansible-vault-tools decrypt-file <file-path>"
    exit 1
fi

echo "$vaultpw"
