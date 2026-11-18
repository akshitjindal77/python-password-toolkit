"""Offline password-hash auditing demonstrations.

This module demonstrates weaknesses of fast, unsalted
password hashes using synthetic test credentials only.
"""

import hashlib
import itertools
import time


def hash_func(
    password: str,
    algorithm: str = "sha256",
) -> str:
    """Calculate a hash for a synthetic test password."""

    if algorithm not in (
        "sha256",
        "sha1",
        "md5",
    ):
        raise ValueError(
            "This training demo supports SHA-256, "
            "SHA-1, and MD5."
        )

    return getattr(
        hashlib,
        algorithm,
    )(
        password.encode("utf-8")
    ).hexdigest()


def dictionary_attack(
    target: str,
    candidates,
    algorithm="sha256",
):
    """Compare a test hash against a predefined word list."""

    attempts = 0

    for password in candidates:
        attempts += 1

        if hash_func(
            password,
            algorithm,
        ) == target:
            return password, attempts

    return None, attempts


def brute_force(
    target: str,
    charset: str,
    max_length: int,
    algorithm="sha256",
    max_attempts=200_000,
):
    """Try combinations from a small test character set."""

    attempts = 0

    for length in range(
        1,
        max_length + 1,
    ):
        for chars in itertools.product(
            charset,
            repeat=length,
        ):
            if attempts >= max_attempts:
                return None, attempts

            attempts += 1

            password = "".join(chars)

            if hash_func(
                password,
                algorithm,
            ) == target:
                return password, attempts

    return None, attempts


def hybrid_attack(
    target: str,
    candidates,
    charset: str,
    max_length: int,
    algorithm="sha256",
    max_attempts=200_000,
):
    """Append small variations to test dictionary words."""

    attempts = 0

    for base in candidates:
        for length in range(
            1,
            max_length + 1,
        ):
            for chars in itertools.product(
                charset,
                repeat=length,
            ):
                if attempts >= max_attempts:
                    return None, attempts

                attempts += 1

                suffix = "".join(chars)
                password = base + suffix

                if hash_func(
                    password,
                    algorithm,
                ) == target:
                    return password, attempts

    return None, attempts


def main():
    """Run the interactive offline hash-auditing demos."""

    print("\n=== OFFLINE PASSWORD HASH AUDIT DEMO ===")

    print(
        "This feature uses ONLY synthetic test "
        "credentials, never real accounts."
    )

    while True:
        print(
            "\n1. Dictionary demo "
            "(test password: welcome)"
        )
        print(
            "2. Brute-force demo "
            "(test password: cab)"
        )
        print(
            "3. Hybrid demo "
            "(test password: sun7)"
        )
        print(
            "4. Return to toolkit menu"
        )

        choice = input(
            "Choose 1-4: "
        ).strip()

        if choice == "4":
            return

        started = time.perf_counter()

        if choice == "1":
            target = hash_func("welcome")

            found, attempts = dictionary_attack(
                target,
                [
                    "admin",
                    "123456",
                    "letmein",
                    "welcome",
                ],
            )

        elif choice == "2":
            target = hash_func("cab")

            found, attempts = brute_force(
                target,
                "abc",
                3,
            )

        elif choice == "3":
            target = hash_func("sun7")

            found, attempts = hybrid_attack(
                target,
                [
                    "sea",
                    "sun",
                    "star",
                ],
                "0123456789",
                1,
            )

        else:
            print("Choose 1-4.")
            continue

        seconds = (
            time.perf_counter() - started
        )

        print(
            f"Algorithm: SHA-256; "
            f"test hash: {target}"
        )

        print(
            f"Recovered TEST password: {found!r}; "
            f"attempts: {attempts}; "
            f"time: {seconds:.5f}s"
        )

        print(
            "Lesson: fast unsalted hashes make "
            "offline guessing cheap. "
            "Use salted scrypt, Argon2id, or bcrypt "
            "for password protection."
        )


if __name__ == "__main__":
    main()