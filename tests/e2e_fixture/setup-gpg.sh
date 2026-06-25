#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: Apache-2.0
#
# Prepare an isolated GPG keyring for the e2e fixture.
#
# Imports the committed throwaway private key into ./gnupg (NOT your real
# ~/.gnupg) and primes the gpg-agent cache with the passphrase, exactly as if a
# human had typed it once. After this, `ansible-vault-tools decrypt` can run
# against this directory and vault.sh will decrypt vaultpw.gpg non-interactively
# via the agent.
#
# Run it from anywhere; it operates relative to its own location:
#   ./setup-gpg.sh
#
# Then, from this directory:
#   ansible-vault-tools decrypt --host testhost --var secret_var

set -euo pipefail

cd "$(dirname "$0")"

# shellcheck source=tests/e2e_fixture/config.sh
. ./config.sh

export GNUPGHOME="$PWD/gnupg"

echo ">> setting up isolated keyring at $GNUPGHOME"
rm -rf "$GNUPGHOME"
mkdir -p "$GNUPGHOME"
chmod 700 "$GNUPGHOME"
printf 'allow-loopback-pinentry\n' >"$GNUPGHOME/gpg-agent.conf"

echo ">> importing throwaway private key"
gpg --batch --pinentry-mode loopback --passphrase "$KEY_PASSPHRASE" \
  --import private-key.asc 2>&1 | grep -v '^$' || true

echo ">> priming gpg-agent cache (simulates typing the passphrase once)"
gpg --batch --pinentry-mode loopback --passphrase "$KEY_PASSPHRASE" \
  --decrypt vaultpw.gpg >/dev/null

echo ">> ready. From this directory you can now run:"
echo "     ansible-vault-tools decrypt --host testhost --var ${SECRET_VAR}"
