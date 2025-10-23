# SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: Apache-2.0

"""Test suite for ansible_vault_tools.main module"""

from ansible_vault_tools._helpers import convert_ansible_errors


def test_convert_ansible_errors_undefined_variable():
    """Test conversion of 'variable not defined' error message"""
    error = 'fatal: [localhost]: FAILED! => {"msg": "VARIABLE IS NOT DEFINED!"}'
    result = convert_ansible_errors(error)
    assert result == "(undefined variable)"


def test_convert_ansible_errors_unknown_error():
    """Test handling of unknown error message"""
    error = "Some other random error"
    result = convert_ansible_errors(error)
    assert result == error  # Should return original error unchanged


def test_convert_ansible_errors_empty_string():
    """Test handling of empty error message"""
    error = ""
    result = convert_ansible_errors(error)
    assert result == ""  # Should return empty string unchanged
