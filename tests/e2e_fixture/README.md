<!--
SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
SPDX-License-Identifier: Apache-2.0
-->

# End-to-end test fixture

A self-contained ansible-vault project used by `tests/test_e2e.py` and for
manual verification of a system-wide `ansible-vault-tools` install.

It mirrors a real setup:

- a **passphrase-protected** throwaway GPG key (`private-key.asc`),
- the Ansible vault password encrypted to that key (`vaultpw.gpg`),
- `vault.sh`, which decrypts `vaultpw.gpg` via the gpg-agent,
- `ansible.cfg` + `inventory.ini` wiring it together,
- `host_vars/testhost.yml` with a vault-encrypted `secret_var`.

## Why a passphrase?

`decrypt_string()` runs `ansible` with a **completely wiped environment**, and
`vault.sh` uses `gpg --use-agent`. A passphrase-protected key only decrypts if
the agent already holds the passphrase — exactly the production situation where
you unlock the key once and the agent remembers it. `setup-gpg.sh` primes that
cache, so the test exercises the real agent path instead of bypassing it.

> [!WARNING]
> Everything here is a **deliberately public throwaway**. The committed
> passphrase and keys only ever protect a dummy vault password that protects a
> dummy secret. Never reuse this key for anything real.

## Manual verification with an installed CLI

```shell
pip install ansible-vault-tools[ansible-deps]   # or however you install it

cd tests/e2e_fixture
./setup-gpg.sh                                  # imports key into ./gnupg, primes agent
ansible-vault-tools decrypt --host testhost --var secret_var
# -> correct horse battery staple
```

`setup-gpg.sh` uses an isolated `GNUPGHOME` (`./gnupg`), so it never touches
your real `~/.gnupg`. That directory is gitignored.

## Rotating the committed key material

```shell
cd tests/e2e_fixture
./regenerate.sh   # rewrites private-key.asc, vaultpw.gpg, host_vars/testhost.yml
```

Shared constants (UID, passphrase, secret) live in `config.sh`. If you change
`secret_var`'s name or value there, update the two matching constants at the top
of `tests/test_e2e.py`.
