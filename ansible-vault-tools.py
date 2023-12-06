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


def convert_ansible_errors(error: str) -> str:
    """Convert typical Ansible errors to more user-friendly messages"""
    if "The task includes an option with an undefined variable" in error:
        return "(undefined variable)"

    # If no conversion was possible, return the original error
    return error


def encrypt_string(password):
    """Encrypt string with ansible-vault"""
    result = subprocess.run(
        ["ansible-vault", "encrypt_string"],
        input=password,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def format_data(data: dict) -> str:
    """Format data nicely in columns"""
    if len(data) > 1:
        max_key_length = max(len(key) for key in data.keys())

        formatted_strings = [f"{key.ljust(max_key_length)}: {value}" for key, value in data.items()]
    else:
        # If only one host, return the single value
        formatted_strings = list(data.values())

    return "\n".join(formatted_strings)


def decrypt_string(host, var):
    """Decrypt/print a variable from one or multiple hosts"""
    # Run ansible msg for variable
    # Send return as JSON
    ansible_command = ["ansible", host, "-m", "debug", "-a", f"msg={{{{ {var} }}}}"]
    ansible_env = {
        "ANSIBLE_LOAD_CALLBACK_PLUGINS": "1",
        "ANSIBLE_STDOUT_CALLBACK": "json",
    }
    result = subprocess.run(ansible_command, env=ansible_env, capture_output=True, text=True)

    # Parse JSON
    ansible_output = json.loads(result.stdout)["plays"][0]["tasks"][0]["hosts"]

    # Attempt to create a :-separated list of host/values
    output = {}
    for host, values in ansible_output.items():
        output[host] = convert_ansible_errors(values["msg"])

    return format_data(output)


def main():
    """Main function"""
    args = parser.parse_args()

    if args.command == "encrypt":
        password = input("Enter string: ") if not args.encrypt_string else args.encrypt_string
        vaultpw = encrypt_string(password)
    elif args.command == "decrypt":
        host = input("Enter host: ") if not args.decrypt_host else args.decrypt_host
        var = input("Enter variable: ") if not args.decrypt_var else args.decrypt_var
        vaultpw = decrypt_string(host, var)

    print(vaultpw)


if __name__ == "__main__":
    main()
