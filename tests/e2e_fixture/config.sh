#!/usr/bin/env sh
# SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: Apache-2.0
#
# Shared constants for the e2e fixture scripts. Sourced, not executed.
# Everything here is a deliberately public throwaway used only for testing.

# Identity of the throwaway GPG key.
KEY_UID="AVT E2E <avt-e2e@example.com>"
# Passphrase protecting the key. Committed on purpose: the whole point is to
# exercise the gpg-agent caching path the same way a real (primed) agent would.
KEY_PASSPHRASE="e2e-fixture-passphrase"

# The Ansible vault password (what vaultpw.gpg decrypts to).
VAULT_PASSWORD="s3cr3t-vault-password"

# The demo secret encrypted into host_vars, and the variable name it lives under.
SECRET_VAR="secret_var"
SECRET_VALUE="correct horse battery staple"
