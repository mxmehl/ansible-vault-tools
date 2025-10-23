# SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: Apache-2.0

"""Helper functions for Ansible Vault Tools"""

import re
import shutil
import sys


def convert_ansible_errors(error: str) -> str:
    """Convert typical Ansible errors to more user-friendly messages"""
    if "VARIABLE IS NOT DEFINED" in error:
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


def format_data(data: dict) -> str:
    """Format data nicely in columns"""
    if len(data) > 1:
        max_key_length = max(len(key) for key in data.keys())

        formatted_strings = [f"{key.ljust(max_key_length)}: {value}" for key, value in data.items()]
    else:
        # If only one host, return the single value
        formatted_strings = [f"{value}" for _, value in data.items()]

    return "\n".join(formatted_strings)


def rewrap_text(text: str) -> str:
    """Replace lines starting with exactly 8 spaces with 2 spaces"""
    return re.sub(r"(?m)^ {8}", "", text)


def executable(command: str) -> str:
    """Return the path to an executable command"""
    path = shutil.which(command)
    if not path:
        sys.exit(f"ERROR: {command} is not installed or not found in PATH.")
    return path
