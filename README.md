<!--
SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
SPDX-License-Identifier: Apache-2.0
-->

# Ansible Vault Tools

A simple CLI tool and Python library to encrypt and decrypt strings and files
using [Ansible Vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html),
and to inspect decrypted host variables from an Ansible inventory.

## Requirements

- Python 3.11 or newer
- `ansible` and `ansible-vault` executables available in `PATH` (provided by
  the `ansible` and `ansible-vault` packages)

## Installation

Install with the optional Ansible dependencies included:

```shell
pip install "ansible-vault-tools[ansible-deps]"
```

Or, if you manage Ansible separately:

```shell
pip install ansible-vault-tools
```

## Usage

### CLI

```
ansible-vault-tools <command> [options]
```

#### `encrypt` — encrypt a string or file

```shell
# Encrypt a string (prompts for input if omitted)
ansible-vault-tools encrypt --string "my secret"
ansible-vault-tools encrypt -s

# Encrypt a file in place
ansible-vault-tools encrypt --file secrets.yml
ansible-vault-tools encrypt -f secrets.yml
```

#### `decrypt` — decrypt a variable or file

```shell
# Decrypt a specific variable for a host (prompts if omitted)
ansible-vault-tools decrypt --host webserver01 --var db_password
ansible-vault-tools decrypt -H webserver01 -v db_password

# Decrypt variables for all hosts
ansible-vault-tools decrypt --host all --var db_password

# Decrypt a vault-encrypted file (shows content, then asks to write it back)
ansible-vault-tools decrypt --file secrets.yml
ansible-vault-tools decrypt -f secrets.yml
```

#### `allvars` — print all variables for a host

```shell
# Print all resolved variables for a specific host
ansible-vault-tools allvars --host webserver01
ansible-vault-tools allvars -H webserver01

# Print hostvars for all hosts
ansible-vault-tools allvars --host all
```

### Library

The individual functions can also be imported directly:

```python
from ansible_vault_tools.main import encrypt_string, encrypt_file, decrypt_string, decrypt_file, allvars
```

| Function | Description |
|---|---|
| `encrypt_string(password)` | Encrypt a string with `ansible-vault encrypt_string` |
| `encrypt_file(filename)` | Encrypt a file in place with `ansible-vault encrypt` |
| `decrypt_string(host, var)` | Decrypt a variable from Ansible inventory host(s) |
| `decrypt_file(filename)` | Decrypt a vault-encrypted file |
| `allvars(host)` | Return all variables for a host as JSON |

## License

The project is mainly licensed under [Apache-2.0](LICENSES/Apache-2.0.txt). It may also contain files under different licenses and copyright holders. The project is REUSE compliant so it's fully transparent.
