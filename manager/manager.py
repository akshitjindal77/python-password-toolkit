"""Encrypted password vault with legacy data recovery.

New vaults use scrypt + Fernet and do not overwrite the original
manager/master.hash or manager/vault.json files.
"""

from __future__ import annotations

import base64
import getpass
import hashlib
import json
import os
import re
import secrets
import tempfile
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


DATA_DIR = Path(__file__).resolve().parent

# Original project files — preserved for recovery.
LEGACY_VAULT = DATA_DIR / "vault.json"
LEGACY_MASTER_HASH = DATA_DIR / "master.hash"

# New vault files.
VAULT_FILE = DATA_DIR / "vault.enc"
META_FILE = DATA_DIR / "vault.meta.json"

# scrypt key-derivation settings.
SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1


class VaultError(Exception):
    """An expected vault error suitable for a user-facing message."""


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte Fernet key using salted, memory-hard scrypt."""

    secret = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=32,
        maxmem=64 * 1024 * 1024,
    )

    return base64.urlsafe_b64encode(secret)


def _atomic_write(path: Path, contents: bytes) -> None:
    """Write data through a temporary file before replacing the target."""

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = None

    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=".vault_tmp_",
            delete=False,
        ) as fh:
            tmp_name = fh.name
            fh.write(contents)
            fh.flush()
            os.fsync(fh.fileno())

        try:
            os.chmod(tmp_name, 0o600)
        except OSError:
            pass

        os.replace(tmp_name, path)

    finally:
        if tmp_name and os.path.exists(tmp_name):
            os.unlink(tmp_name)


def new_vault_exists(directory: Path = DATA_DIR) -> bool:
    """Check whether either new-format vault file already exists."""

    return (
        (directory / "vault.enc").exists()
        or (directory / "vault.meta.json").exists()
    )


def create_vault(
    password: str,
    initial: dict | None = None,
    directory: Path = DATA_DIR,
) -> bytes:
    """Create a new encrypted vault without overwriting an existing one."""

    if new_vault_exists(directory):
        raise VaultError(
            "A modern vault already exists (or its files are incomplete). "
            "Nothing was overwritten."
        )

    if len(password) < 12:
        raise VaultError(
            "Choose a master password of at least 12 characters."
        )

    # Each vault gets a unique cryptographic salt.
    salt = secrets.token_bytes(16)

    # Derive the encryption key from the master password.
    key = derive_key(password, salt)

    # Store only the salt and KDF settings, not a password hash.
    meta = {
        "format": 1,
        "kdf": "scrypt",
        "salt": base64.urlsafe_b64encode(salt).decode(),
        "n": SCRYPT_N,
        "r": SCRYPT_R,
        "p": SCRYPT_P,
    }

    data = {} if initial is None else initial

    if not isinstance(data, dict):
        raise VaultError(
            "Vault content is not a valid credential dictionary."
        )

    encrypted = Fernet(key).encrypt(
        json.dumps(data, ensure_ascii=False).encode("utf-8")
    )

    # These are separate files. If creation is interrupted,
    # the application refuses to load an incomplete vault.
    _atomic_write(directory / "vault.enc", encrypted)

    _atomic_write(
        directory / "vault.meta.json",
        json.dumps(meta, indent=2).encode("utf-8"),
    )

    return key


def unlock_vault(
    password: str,
    directory: Path = DATA_DIR,
) -> tuple[dict, bytes]:
    """Decrypt an existing new-format vault."""

    vault_file = directory / "vault.enc"
    meta_file = directory / "vault.meta.json"

    if not vault_file.is_file() or not meta_file.is_file():
        raise VaultError(
            "Missing modern vault file(s). "
            "Do not delete anything. Check your backups."
        )

    try:
        meta = json.loads(
            meta_file.read_text(encoding="utf-8")
        )

        if meta.get("format") != 1 or meta.get("kdf") != "scrypt":
            raise VaultError(
                "Unrecognized vault metadata format."
            )

        # Reject unexpected KDF settings.
        if (
            meta.get("n"),
            meta.get("r"),
            meta.get("p"),
        ) != (
            SCRYPT_N,
            SCRYPT_R,
            SCRYPT_P,
        ):
            raise VaultError(
                "Unexpected KDF parameters. "
                "Verify that this is the correct vault."
            )

        salt = base64.urlsafe_b64decode(meta["salt"])

        if len(salt) != 16:
            raise VaultError("Invalid vault salt.")

        key = derive_key(password, salt)

        decrypted = Fernet(key).decrypt(
            vault_file.read_bytes()
        )

        vault = json.loads(
            decrypted.decode("utf-8")
        )

        if not isinstance(vault, dict):
            raise VaultError(
                "Vault data has an unexpected structure."
            )

        return vault, key

    except InvalidToken:
        raise VaultError(
            "Incorrect master password, or encrypted vault "
            "does not match its metadata."
        ) from None

    except (
        ValueError,
        KeyError,
        UnicodeError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        raise VaultError(
            "Vault files are damaged or cannot be parsed."
        ) from exc


def save_vault(
    vault: dict,
    key: bytes,
    directory: Path = DATA_DIR,
) -> None:
    """Save encrypted data to an existing new-format vault."""

    if (
        not (directory / "vault.meta.json").is_file()
        or not (directory / "vault.enc").is_file()
    ):
        raise VaultError(
            "Modern vault files are missing; refusing to write."
        )

    encrypted = Fernet(key).encrypt(
        json.dumps(vault, ensure_ascii=False).encode("utf-8")
    )

    _atomic_write(
        directory / "vault.enc",
        encrypted,
    )


def recover_legacy_with_password(
    password: str,
    legacy_path: Path = LEGACY_VAULT,
) -> dict:
    """Decrypt the original vault using its original master password."""

    # Original project used SHA-256 directly to make the Fernet key.
    legacy_key = base64.urlsafe_b64encode(
        hashlib.sha256(
            password.encode("utf-8")
        ).digest()
    )

    return _decrypt_legacy(
        legacy_key,
        legacy_path,
    )


def recover_legacy_with_hash(
    hash_text: str,
    legacy_path: Path = LEGACY_VAULT,
) -> dict:
    """Recover from a matching ORIGINAL legacy master.hash backup."""

    hash_text = hash_text.strip()

    if not re.fullmatch(r"[a-fA-F0-9]{64}", hash_text):
        raise VaultError(
            "The old master.hash must contain exactly "
            "64 hexadecimal characters."
        )

    # This is possible because of the old design weakness.
    legacy_key = base64.urlsafe_b64encode(
        bytes.fromhex(hash_text)
    )

    return _decrypt_legacy(
        legacy_key,
        legacy_path,
    )


def _decrypt_legacy(
    key: bytes,
    legacy_path: Path,
) -> dict:
    """Attempt to decrypt the original vault without modifying it."""

    try:
        encrypted = (
            legacy_path
            .read_text(encoding="utf-8")
            .strip()
            .encode("utf-8")
        )

        data = json.loads(
            Fernet(key)
            .decrypt(encrypted)
            .decode("utf-8")
        )

        if not isinstance(data, dict):
            raise VaultError(
                "Legacy vault has unexpected content."
            )

        return data

    except FileNotFoundError:
        raise VaultError(
            f"Could not find legacy vault: {legacy_path}"
        ) from None

    except InvalidToken:
        raise VaultError(
            "The old password/hash does not decrypt the "
            "legacy vault, or its token is damaged."
        ) from None

    except (
        ValueError,
        UnicodeError,
        json.JSONDecodeError,
    ) as exc:
        raise VaultError(
            "Legacy vault data is unreadable."
        ) from exc


def _ask_new_master() -> str | None:
    """Ask for and confirm a new master password."""

    first = getpass.getpass(
        "Choose a NEW master password (12+ characters): "
    )

    second = getpass.getpass(
        "Confirm NEW master password: "
    )

    if first != second:
        print(
            "Passwords did not match. No changes were made."
        )
        return None

    if len(first) < 12:
        print(
            "Use at least 12 characters. No changes were made."
        )
        return None

    return first


def _first_run() -> tuple[dict, bytes] | None:
    """Create a modern vault or recover credentials from an old vault."""

    legacy_exists = LEGACY_VAULT.is_file()
    initial = {}

    if legacy_exists:
        print(
            "\nFound your ORIGINAL encrypted vault "
            "(manager/vault.json)."
        )

        print(
            "Your old files will NEVER be deleted or "
            "overwritten by this application."
        )

        print(
            "1. Recover using ORIGINAL old master password"
        )
        print(
            "2. Recover using a backup of ORIGINAL old master.hash"
        )
        print(
            "3. Start an EMPTY NEW demo vault (keeps old files)"
        )
        print("4. Cancel")

        choice = input("Choose 1-4: ").strip()

        if choice == "1":
            pw = getpass.getpass(
                "Enter the ORIGINAL password used "
                "to encrypt vault.json: "
            )

            try:
                initial = recover_legacy_with_password(pw)

            except VaultError as exc:
                print(f"Cannot recover: {exc}")
                return None

            print(
                f"Recovery succeeded "
                f"({len(initial)} saved site(s)). "
                f"Original files remain intact."
            )

        elif choice == "2":
            path = Path(
                input(
                    "Path to ORIGINAL master.hash backup: "
                ).strip().strip('"')
            )

            try:
                old_hash = path.read_text(
                    encoding="utf-8"
                )

                initial = recover_legacy_with_hash(
                    old_hash
                )

            except OSError as exc:
                print(
                    f"Cannot read the supplied hash backup: {exc}"
                )
                return None

            except VaultError as exc:
                print(f"Cannot recover: {exc}")
                return None

            print(
                f"Recovery succeeded "
                f"({len(initial)} saved site(s)). "
                f"Original files remain intact."
            )

        elif choice == "3":
            print(
                "Starting a separate new vault. "
                "The original vault.json and master.hash "
                "are untouched."
            )

        else:
            return None

    password = _ask_new_master()

    if password is None:
        return None

    try:
        key = create_vault(
            password,
            initial,
        )

    except VaultError as exc:
        print(f"Cannot create vault: {exc}")
        return None

    print(
        "New encrypted vault created successfully."
    )

    return initial, key


def main() -> None:
    """Run the password manager menu."""

    print("\n=== ENCRYPTED PASSWORD MANAGER ===")

    if new_vault_exists():

        if (
            not VAULT_FILE.is_file()
            or not META_FILE.is_file()
        ):
            print(
                "Modern vault is incomplete. "
                "Do not reset or delete it; "
                "restore the correct files."
            )
            return

        unlocked = None

        for attempt in range(3):
            pw = getpass.getpass(
                "Master password: "
            )

            try:
                unlocked = unlock_vault(pw)
                break

            except VaultError as exc:
                print(exc)

        if unlocked is None:
            print(
                "Too many unsuccessful attempts. "
                "Returning to main menu."
            )
            return

        vault, key = unlocked

    else:
        result = _first_run()

        if result is None:
            return

        vault, key = result

    while True:
        print("\n1. Add credential")
        print("2. Retrieve credential")
        print("3. List saved sites (names only)")
        print("4. Delete a saved credential")
        print("5. Generate strong password and save it")
        print("6. Return to toolkit menu")

        choice = input("Choose 1-6: ").strip()

        if choice == "1":
            site = input(
                "Site name: "
            ).strip()

            username = input(
                "Username: "
            ).strip()

            password = getpass.getpass(
                "Password to store: "
            )

            if not site or not username or not password:
                print(
                    "Site, username and password "
                    "cannot be empty."
                )
                continue

            if site in vault:
                confirmation = input(
                    "Replace existing site? (yes/no): "
                ).strip().lower()

                if confirmation != "yes":
                    continue

            vault[site] = {
                "username": username,
                "password": password,
            }

            save_vault(vault, key)

            print(
                "Credential saved in encrypted vault."
            )

        elif choice == "2":
            site = input(
                "Site name: "
            ).strip()

            if site in vault:
                print(
                    "Username:",
                    vault[site]["username"],
                )

                show = input(
                    "Show saved password on screen? "
                    "(yes/no): "
                ).strip().lower()

                if show == "yes":
                    print(
                        "Password:",
                        vault[site]["password"],
                    )

            else:
                print("Site not found.")

        elif choice == "3":
            print(
                "Saved sites:",
                ", ".join(sorted(vault))
                if vault else "(none)",
            )

        elif choice == "4":
            site = input(
                "Site to delete: "
            ).strip()

            if site not in vault:
                print("Site not found.")

            else:
                confirmation = input(
                    f"Type DELETE to remove {site}: "
                ).strip()

                if confirmation == "DELETE":
                    del vault[site]
                    save_vault(vault, key)

                    print("Credential deleted.")

        elif choice == "5":
            from generator.generator import generate_password

            site = input(
                "Site name: "
            ).strip()

            username = input(
                "Username: "
            ).strip()

            if not site or not username:
                print(
                    "Site and username cannot be empty."
                )
                continue

            password = generate_password(
                length=20
            )

            if site in vault:
                confirmation = input(
                    "Replace existing site? (yes/no): "
                ).strip().lower()

                if confirmation != "yes":
                    continue

            vault[site] = {
                "username": username,
                "password": password,
            }

            save_vault(vault, key)

            print(
                "Generated a strong password and SAVED "
                "it in your encrypted vault."
            )

            show = input(
                "Show it once on screen? (yes/no): "
            ).strip().lower()

            if show == "yes":
                print(
                    "Generated password:",
                    password,
                )

        elif choice == "6":
            return

        else:
            print("Please choose 1-6.")


if __name__ == "__main__":
    # Allow running manager.py directly as well.
    import sys

    sys.path.insert(
        0,
        str(DATA_DIR.parent),
    )

    main()