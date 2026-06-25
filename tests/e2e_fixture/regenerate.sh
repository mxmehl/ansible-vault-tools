#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: Apache-2.0
#
# Regenerate the committed key material for the e2e fixture.
#
# This is NOT run by the test suite. Run it by hand only when you want to
# rotate the throwaway key or the encrypted artifacts. It produces three
# committed files in this directory:
#
#   private-key.asc  - the (passphrase-protected) GPG private key, ASCII-armored
#   vaultpw.gpg      - the Ansible vault password, encrypted to that key
#   host_vars/testhost.yml - the demo secret, ansible-vault-encrypted
#
# Everything here is a DELIBERATELY PUBLIC throwaway. The key only ever
# protects a dummy vault password that itself only protects a dummy secret.
# Nothing sensitive is involved; the passphrase is committed on purpose so the
# test and manual runs can prime the gpg-agent cache the same way a human would.

set -euo pipefail

cd "$(dirname "$0")"

# shellcheck source=tests/e2e_fixture/config.sh
. ./config.sh

work="$(mktemp -d "${TMPDIR:-/tmp}/avt-regen-XXXXXX")"
chmod 700 "$work"
cleanup() {
  gpgconf --homedir "$work" --kill gpg-agent >/dev/null 2>&1 || true
  rm -rf "$work"
}
trap cleanup EXIT

echo ">> generating passphrase-protected key in throwaway keyring $work"
printf 'allow-loopback-pinentry\n' >"$work/gpg-agent.conf"
gpg --homedir "$work" --batch --pinentry-mode loopback --passphrase "$KEY_PASSPHRASE" \
  --quick-generate-key "$KEY_UID" default default never

echo ">> exporting private key to private-key.asc"
gpg --homedir "$work" --batch --pinentry-mode loopback --passphrase "$KEY_PASSPHRASE" \
  --armor --export-secret-keys "$KEY_UID" >private-key.asc

echo ">> encrypting vault password into vaultpw.gpg"
printf '%s' "$VAULT_PASSWORD" | gpg --homedir "$work" --batch --yes --trust-model always \
  --encrypt --recipient "$KEY_UID" --output vaultpw.gpg

echo ">> encrypting demo secret into host_vars/testhost.yml"
mkdir -p host_vars
# Write the vault password to a temp file so ansible-vault can read it without
# touching the committed gnupg runtime dir.
pwfile="$work/vaultpw.txt"
printf '%s' "$VAULT_PASSWORD" >"$pwfile"
{
  echo "---"
  ANSIBLE_CONFIG=/dev/null \
    ansible-vault encrypt_string --vault-password-file "$pwfile" --name "$SECRET_VAR" "$SECRET_VALUE"
  echo
} >host_vars/testhost.yml

echo ">> done. Regenerated: private-key.asc, vaultpw.gpg, host_vars/testhost.yml"
