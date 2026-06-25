# SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
#
# SPDX-License-Identifier: Apache-2.0

"""End-to-end smoke test against the on-disk fixture in ``e2e_fixture/``.

The fixture mirrors a real ansible-vault setup: a passphrase-protected GPG key
whose passphrase is cached by ``setup-gpg.sh`` (just as a human would type it
once), a GPG-encrypted vault password loaded via ``vault.sh``, and an inventory
host whose ``host_vars`` hold a vault-encrypted variable. The test runs
``setup-gpg.sh`` to build an isolated ./gnupg keyring, then asserts that
``decrypt_string`` round-trips the secret back out.

The same fixture can be driven by hand to verify a system-wide install; see
``e2e_fixture/README.md``.

Skipped automatically if ``gpg``, ``ansible`` or ``ansible-vault`` are missing.
"""

import logging
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from ansible_vault_tools.main import decrypt_string

logger = logging.getLogger(__name__)

# ponytail: one happy-path round-trip is the smallest thing that fails if the
# GPG-agent -> vault.sh -> ansible -> decrypt pipeline breaks. No matrix needed.

FIXTURE = Path(__file__).parent / "e2e_fixture"
REQUIRED_BINARIES = ("gpg", "ansible", "ansible-vault")

# Mirrors e2e_fixture/config.sh; kept in sync by hand (two small constants).
SECRET_VAR = "secret_var"  # noqa: S105
SECRET_VALUE = "correct horse battery staple"  # noqa: S105

pytestmark = pytest.mark.skipif(
    any(shutil.which(b) is None for b in REQUIRED_BINARIES),
    reason=f"requires {', '.join(REQUIRED_BINARIES)} on PATH",
)


@pytest.fixture
def prepared_fixture() -> Iterator[Path]:
    """Import the throwaway key + prime the agent, yielding the fixture dir."""
    logger.info("running setup-gpg.sh to build isolated keyring in %s", FIXTURE)
    subprocess.run(  # noqa: S603
        [str(FIXTURE / "setup-gpg.sh")], cwd=FIXTURE, capture_output=True, text=True, check=True
    )
    try:
        yield FIXTURE
    finally:
        gnupghome = FIXTURE / "gnupg"
        logger.info("tearing down: killing gpg-agent and removing %s", gnupghome)
        subprocess.run(  # noqa: S603
            ["gpgconf", "--homedir", str(gnupghome), "--kill", "gpg-agent"],
            capture_output=True,
            check=False,
        )
        shutil.rmtree(gnupghome, ignore_errors=True)


def test_decrypt_string_roundtrip(prepared_fixture: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The secret in host_vars is decrypted back via the module + agent."""
    # decrypt_string resolves ansible.cfg, inventory and vault.sh relative to cwd.
    monkeypatch.chdir(prepared_fixture)

    logger.info("calling decrypt_string('testhost', '%s')", SECRET_VAR)
    result = decrypt_string("testhost", SECRET_VAR)
    logger.info("decrypt_string returned %d chars, matches=%s", len(result), result == SECRET_VALUE)
    assert result == SECRET_VALUE


# Sentinel env var the dynamic inventory below requires. Mimics openrail's
# inventory script needing inherited PATH to find a tomllib-capable Python.
ENV_SENTINEL = "AVT_INHERITED_ENV_CHECK"


@pytest.fixture
def env_dependent_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A project whose dynamic inventory only works if the env is propagated."""
    inventory = tmp_path / "inventory.sh"
    inventory.write_text(
        "#!/bin/sh\n"
        f'[ -n "${ENV_SENTINEL}" ] || {{ echo "missing inherited env" >&2; exit 1; }}\n'
        'if [ "$1" = "--list" ]; then\n'
        '  printf \'{"all":{"hosts":["testhost"]},"_meta":{"hostvars":'
        '{"testhost":{"myvar":"resolved-ok","ansible_connection":"local"}}}}\\n\'\n'
        "else\n"
        "  printf '{}\\n'\n"
        "fi\n"
    )
    inventory.chmod(0o755)
    (tmp_path / "ansible.cfg").write_text("[defaults]\ninventory = inventory.sh\n")
    monkeypatch.setenv(ENV_SENTINEL, "1")
    return tmp_path


def test_decrypt_string_propagates_environment(
    env_dependent_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: ansible must inherit the env, or inventory scripts break.

    The old code ran ansible with a replaced environment, wiping PATH and this
    sentinel. The dynamic inventory then failed, no host matched, and the tool
    reported a misleading 'Host not found'. With the env preserved, the host
    resolves and the variable comes back.
    """
    monkeypatch.chdir(env_dependent_project)

    logger.info("calling decrypt_string('testhost', 'myvar') with %s set", ENV_SENTINEL)
    assert decrypt_string("testhost", "myvar") == "resolved-ok"
