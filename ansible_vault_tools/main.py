#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: Apache-2.0

"""Encrypt or decrypt using Ansible-vault and Ansible"""

import argparse
import json
import os
import subprocess
import sys
from importlib.metadata import version

from ansible_vault_tools._helpers import (
    ask_for_confirm,
    convert_ansible_errors,
    executable,
    format_data,
    rewrap_text,
)

__version__ = version("ansible-vault-tools")

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--version", action="version", version="%(prog)s " + __version__)

# First-level subcommands
subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

# Common flags, usable for all effective subcommands
common_flags = argparse.ArgumentParser(add_help=False)  # No automatic help to avoid duplication

# Command: encrypt
parser_encrypt = subparsers.add_parser(
    "encrypt",
    help="Encrypt a string or file using ansible-vault",
    parents=[common_flags],
)
encrypt_flags = parser_encrypt.add_mutually_exclusive_group(required=True)
encrypt_flags.add_argument(
    "-s",
    "--string",
    help="String that shall be encrypted",
    dest="encrypt_string",
    nargs="?",
    const="",
)
encrypt_flags.add_argument(
    "-f",
    "--file",
    help="File that shall be encrypted",
    dest="encrypt_file",
)

# Command: decrypt
parser_decrypt = subparsers.add_parser(
    "decrypt",
    help="Decrypt a string or file using ansible-vault",
    parents=[common_flags],
)
decrypt_flags = parser_decrypt.add_mutually_exclusive_group(required=True)
decrypt_flags.add_argument(
    "-H",
    "--host",
    help=(
        "Host name from Ansible inventory for which you want to get a specific variable. "
        "Also supports 'all'"
    ),
    dest="decrypt_host",
    nargs="?",
    const="",
)
decrypt_flags.add_argument(
    "-f",
    "--file",
    help="File that shall be decrypted",
    dest="decrypt_file",
)
parser_decrypt.add_argument(
    "-v",
    "--var",
    help="Variable you want to print",
    dest="decrypt_var",
)

# Command: allvars
parser_allvars = subparsers.add_parser(
    "allvars",
    help="Print all variables of a host",
    parents=[common_flags],
)
parser_allvars.add_argument(
    "-H",
    "--host",
    help=(
        "Host name from Ansible inventory for which you want to get all variables. "
        "Also supports 'all'"
    ),
    dest="allvars_host",
)


def encrypt_string(password: str) -> str:
    """Encrypt string with ansible-vault"""
    result = subprocess.run(
        [executable("ansible-vault"), "encrypt_string"],
        input=password,
        text=True,
        capture_output=True,
        check=False,
    )
    return rewrap_text(result.stdout.strip())


def encrypt_file(filename: str) -> str:
    """Encrypt a file with ansible-vault"""

    if not os.path.exists(filename):
        sys.exit(f"ERROR: File '{filename}' does not exist")

    encrypted_return = subprocess.run(
        [executable("ansible-vault"), "encrypt", filename], check=False, capture_output=True
    )

    if encrypted_return.returncode != 0:
        sys.exit(
            f"ERROR: Could not encrypt file '{filename}'. This is the error:"
            f"\n{encrypted_return.stderr.decode()}"
        )

    return f"Encrypted '{filename}' successfully"


def decrypt_string(host, var) -> str:
    """Decrypt/print a variable from one or multiple hosts"""
    # Run ansible msg for variable
    # Send return as JSON
    ansible_command = [executable("ansible"), host, "-m", "debug", "-a", f"var={var}"]
    ansible_env = {
        "ANSIBLE_LOAD_CALLBACK_PLUGINS": "1",
        "ANSIBLE_STDOUT_CALLBACK": "json",
    }
    try:
        result = subprocess.run(
            ansible_command, env=ansible_env, capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        sys.exit(f"Decrypting the variable failed: {e.stderr}")
    except FileNotFoundError:
        sys.exit(f"ERROR: {executable} is not installed or not found in PATH.")

    # Parse JSON
    try:
        ansible_output = json.loads(result.stdout)["plays"][0]["tasks"][0]["hosts"]
    except IndexError:
        sys.exit(f"ERROR: Host '{host}' not found.")

    # Attempt to create a :-separated list of host/values
    output = {}
    for hostname, values in ansible_output.items():
        output[hostname] = convert_ansible_errors(values[var])

    return format_data(output)


def decrypt_file(filename: str) -> str:
    """Decrypt file with ansible-vault"""

    if not os.path.exists(filename):
        sys.exit(f"ERROR: File '{filename}' does not exist")

    decrypted_content = subprocess.run(
        [executable("ansible-vault"), "decrypt", "--output", "-", filename],
        check=False,
        capture_output=True,
    )

    if decrypted_content.returncode != 0:
        sys.exit(
            f"ERROR: Could not decrypt file '{filename}'. This is the error:"
            f"\n{decrypted_content.stderr.decode()}"
        )

    print(decrypted_content.stdout.decode().strip())
    if ask_for_confirm("Shall I write the encrypted content as seen above to the file?"):
        decrypted_content = subprocess.run(
            [executable("ansible-vault"), "decrypt", filename], check=True, capture_output=True
        )
        return f"Decrypted '{filename}' successfully"

    return f"File '{filename}' was not changed"


def allvars(host: str) -> str:
    """Decrypt/print all variables from one or multiple hosts"""
    # Run ansible var for all host vars as seen from localhost
    # Send return as JSON
    ansible_command = [executable("ansible"), "localhost", "-m", "debug", "-a", "var=hostvars"]
    ansible_env = {
        "ANSIBLE_LOAD_CALLBACK_PLUGINS": "1",
        "ANSIBLE_STDOUT_CALLBACK": "json",
    }
    result = subprocess.run(
        ansible_command, env=ansible_env, capture_output=True, text=True, check=False
    )

    # Reduce JSON
    ansible_output = json.loads(result.stdout)["plays"][0]["tasks"][0]["hosts"]["localhost"][
        "hostvars"
    ]

    # If only a specific host was requested, reduce the output to that host
    if host != "all":
        try:
            ansible_output = ansible_output[host]
        except KeyError:
            sys.exit(f"ERROR: Host '{host}' not found.")

    return json.dumps(ansible_output, indent=2)


def _cli():
    """Function when called from command line"""
    args = parser.parse_args()
    output = ""

    # ENCRYPTION
    if args.command == "encrypt":
        if args.encrypt_string is not None:
            password = input("Enter string: ") if not args.encrypt_string else args.encrypt_string
            output = encrypt_string(password)
        elif args.encrypt_file:
            filename = input("Enter filename: ") if not args.encrypt_file else args.encrypt_file
            output = encrypt_file(filename)
    # DECRYPTION
    elif args.command == "decrypt":
        if args.decrypt_host is not None:
            host = input("Enter host: ") if not args.decrypt_host else args.decrypt_host
            var = input("Enter variable: ") if not args.decrypt_var else args.decrypt_var
            output = decrypt_string(host, var)
        elif args.decrypt_file:
            filename = input("Enter filename: ") if not args.decrypt_file else args.decrypt_file
            output = decrypt_file(filename)
    # ALLVARS
    elif args.command == "allvars":
        host = input("Enter host: ") if not args.allvars_host else args.allvars_host
        output = allvars(host)

    if output:
        print(output)


if __name__ == "__main__":
    _cli()
