#!/usr/bin/env python3
"""Encrypt or decrypt using Ansible-vault and Ansible"""
# SPDX-FileCopyrightText: 2023 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=invalid-name

import argparse
import json
import os
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
subparsers = parser.add_subparsers(title="commands", dest="command", required=True)
# Encrypt arguments
parser_encrypt = subparsers.add_parser(
    "encrypt",
    help="Encrypt a string using ansible-vault",
)
encrypt_flags = parser_encrypt.add_mutually_exclusive_group(required=True)
encrypt_flags.add_argument(
    "-s",
    "--string",
    help="String that shall be encrypted",
    dest="encrypt_string",
)
encrypt_flags.add_argument(
    "-f",
    "--file",
    help="File that shall be encrypted",
    dest="encrypt_file",
)
# Decrypt arguments
parser_decrypt = subparsers.add_parser(
    "decrypt",
    help="Print a variable of one or multiple hosts and decrypt it if necessary",
)
decrypt_flags = parser_decrypt.add_mutually_exclusive_group(required=True)
decrypt_flags.add_argument(
    "-H",
    "--host",
    help="Host name from Ansible inventory for which you want to get the variable",
    dest="decrypt_host",
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


def convert_ansible_errors(error: str) -> str:
    """Convert typical Ansible errors to more user-friendly messages"""
    if "The task includes an option with an undefined variable" in error:
        return "(undefined variable)"

    # If no conversion was possible, return the original error
    return error


def ask_for_confirm(question: str) -> bool:
    """Ask for confirmation.

    Args:
        question (str): The question to ask the user.

    Returns:
        bool: True if the user confirms with 'y', False otherwise.
    """
    while True:
        answer = input(f"{question} [y/n]: ").lower().strip()
        if answer in ("y", "n"):
            break
        print("Invalid input. Please enter 'y' or 'n'.")

    return answer == "y"


def encrypt_string(password):
    """Encrypt string with ansible-vault"""
    result = subprocess.run(
        ["ansible-vault", "encrypt_string"],
        input=password,
        text=True,
        capture_output=True,
        check=False,
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


def decrypt_file(filename) -> None:
    """Decrypt file with ansible-vault"""

    if not os.path.exists(filename):
        sys.exit(f"ERROR: File '{filename}' does not exist")

    decrypted_content = subprocess.run(
        ["ansible-vault", "decrypt", "--output", "-", filename], check=False, capture_output=True
    )

    if decrypted_content.returncode != 0:
        sys.exit(
            f"ERROR: Could not decrypt file '{filename}'. This is the error:"
            f"\n{decrypted_content.stderr.decode()}"
        )

    print(decrypted_content.stdout.decode().strip())
    if ask_for_confirm("Shall I write the encrypted content as seen above to the file?"):
        decrypted_content = subprocess.run(
            ["ansible-vault", "decrypt", filename], check=True, capture_output=True
        )


def decrypt_string(host, var) -> str:
    """Decrypt/print a variable from one or multiple hosts"""
    # Run ansible msg for variable
    # Send return as JSON
    ansible_command = ["ansible", host, "-m", "debug", "-a", f"msg={{{{ {var} }}}}"]
    ansible_env = {
        "ANSIBLE_LOAD_CALLBACK_PLUGINS": "1",
        "ANSIBLE_STDOUT_CALLBACK": "json",
    }
    result = subprocess.run(
        ansible_command, env=ansible_env, capture_output=True, text=True, check=False
    )

    # Parse JSON
    try:
        ansible_output = json.loads(result.stdout)["plays"][0]["tasks"][0]["hosts"]
    except IndexError:
        sys.exit(f"ERROR: Host '{host}' not found.")

    # Attempt to create a :-separated list of host/values
    output = {}
    for host, values in ansible_output.items():
        output[host] = convert_ansible_errors(values["msg"])

    return format_data(output)


def main():
    """Main function"""
    args = parser.parse_args()
    output = ""

    # ENCRYPTION
    if args.command == "encrypt":
        if args.encrypt_string:
            password = input("Enter string: ") if not args.encrypt_string else args.encrypt_string
            output = encrypt_string(password)
        elif args.encrypt_file:
            filename = input("Enter filename: ") if not args.encrypt_file else args.encrypt_file
            # TODO
    # DECRYPTION
    elif args.command == "decrypt":
        if args.decrypt_host:
            host = input("Enter host: ") if not args.decrypt_host else args.decrypt_host
            var = input("Enter variable: ") if not args.decrypt_var else args.decrypt_var
            output = decrypt_string(host, var)
        elif args.decrypt_file:
            filename = input("Enter filename: ") if not args.decrypt_file else args.decrypt_file
            decrypt_file(filename)

    if output:
        print(output)


if __name__ == "__main__":
    main()
