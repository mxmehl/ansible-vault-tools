# SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: Apache-2.0

"""Test suite for ansible_vault_tools.main module."""

from ansible_vault_tools._helpers import ansible_json_env, convert_ansible_errors


def test_ansible_json_env_preserves_environment(monkeypatch) -> None:
    """Regression: the env must be extended, not replaced.

    Replacing os.environ wiped PATH/HOME, breaking inventory scripts and the
    vault password script, which surfaced as a misleading 'Host not found'.
    """
    monkeypatch.setenv("PATH", "/sentinel/bin")
    monkeypatch.setenv("HOME", "/sentinel/home")

    env = ansible_json_env()

    assert env["PATH"] == "/sentinel/bin"
    assert env["HOME"] == "/sentinel/home"
    assert env["ANSIBLE_LOAD_CALLBACK_PLUGINS"] == "1"
    assert env["ANSIBLE_STDOUT_CALLBACK"] == "json"


def test_convert_ansible_errors_undefined_variable() -> None:
    """Test conversion of 'variable not defined' error message."""
    error = 'fatal: [localhost]: FAILED! => {"msg": "VARIABLE IS NOT DEFINED!"}'
    result = convert_ansible_errors(error)
    assert result == "(undefined variable)"


def test_convert_ansible_errors_unknown_error() -> None:
    """Test handling of unknown error message."""
    error = "Some other random error"
    result = convert_ansible_errors(error)
    assert result == error  # Should return original error unchanged


def test_convert_ansible_errors_empty_string() -> None:
    """Test handling of empty error message."""
    error = ""
    result = convert_ansible_errors(error)
    assert result == ""  # Should return empty string unchanged
