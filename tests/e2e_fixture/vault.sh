#!/bin/sh
# SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: Apache-2.0
#
# Vault password script for the e2e fixture.
#
# IMPORTANT: ansible-vault-tools' decrypt_string() runs `ansible` with a
# COMPLETELY WIPED environment (no PATH, HOME or GNUPGHOME). This script must
# therefore be fully self-contained:
#   1. set a PATH before calling any external command (even dirname),
#   2. point GNUPGHOME at the isolated ./gnupg keyring next to this script,
#   3. decrypt via the agent (the passphrase was primed by setup-gpg.sh).
#
# This is the same constraint a real production vault.sh faces, so it doubles
# as documentation of the supported pattern.

# Absolute shebang above + this PATH make the script work under a wiped env.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export GNUPGHOME="$script_dir/gnupg"

gpg --batch --use-agent --decrypt "$script_dir/vaultpw.gpg" 2>/dev/null
