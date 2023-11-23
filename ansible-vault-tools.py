#!/usr/bin/env python3
"""Encrypt or decrypt using Ansible-vault and Ansible"""

# SPDX-FileCopyrightText: 2023 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
import json
import argparse

parser = argparse.ArgumentParser(description=__doc__)
subparsers = parser.add_subparsers(title="commands", dest="command", required=True)
# Encrypt arguments
parser_encrypt = subparsers.add_parser(
    "encrypt",
    help="Encrypt a string using ansible-vault",
)
parser_encrypt.add_argument(
    "-s",
    "--string",
    help="String that shall be encrypted",
    dest="encrypt_string",
)
# Decrypt arguments
parser_decrypt = subparsers.add_parser(
    "decrypt",
    help="Print a variable of one or multiple hosts and decrypt it if necessary",
)
parser_decrypt.add_argument(
    "-H",
    "--host",
    help="Host name from Ansible inventory for which you want to get the variable",
    dest="decrypt_host",
)
parser_decrypt.add_argument(
    "-v",
    "--var",
    help="Variable you want to print",
    dest="decrypt_var",
)


def encrypt(password):
    """Encrypt string with ansible-vault"""
    result = subprocess.run(
        ["ansible-vault", "encrypt_string"],
        input=password,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def decrypt(host, var):
    """Decrypt/print a variable from one or multiple hosts"""
    # Run ansible msg for variable
    # Send return as JSON
    ansible_command = ["ansible", host, "-m", "debug", "-a", f"msg={{{{ {var} }}}}"]
    ansible_env = {
        "ANSIBLE_LOAD_CALLBACK_PLUGINS": "1",
        "ANSIBLE_STDOUT_CALLBACK": "json",
    }
    result = subprocess.run(
        ansible_command, env=ansible_env, capture_output=True, text=True
    )

    # Parse JSON to just get the "msg"
    ansible_output = json.loads(result.stdout)
    msg = [
        host["msg"]
        for play in ansible_output["plays"]
        for task in play["tasks"]
        for host in task["hosts"].values()
    ]

    # Pretty print the JSON
    return json.dumps(msg, indent=2)


def main():
    """Main function"""
    args = parser.parse_args()

    if args.command == "encrypt":
        password = (
            input("Enter string: ") if not args.encrypt_string else args.encrypt_string
        )
        vaultpw = encrypt(password)
    elif args.command == "decrypt":
        host = input("Enter host: ") if not args.decrypt_host else args.decrypt_host
        var = input("Enter variable: ") if not args.decrypt_var else args.decrypt_var
        vaultpw = decrypt(host, var)

    print(vaultpw)


if __name__ == "__main__":
    main()
