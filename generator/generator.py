"""Secure password generator using cryptographic randomness."""

from __future__ import annotations

import secrets
import string


AMBIGUOUS = set("O0Il1|")
SYS_RANDOM = secrets.SystemRandom()


def generate_password(
    length: int = 20,
    include_upper: bool = True,
    include_lower: bool = True,
    include_numbers: bool = True,
    exclude_ambi: bool = False,
    include_sym: bool = True,
) -> str:
    """Generate a password using selected character categories."""

    groups = []

    if include_upper:
        groups.append(string.ascii_uppercase)

    if include_lower:
        groups.append(string.ascii_lowercase)

    if include_numbers:
        groups.append(string.digits)

    if include_sym:
        groups.append("!@#$%^&*()-_=+[]{}?")

    if exclude_ambi:
        groups = [
            "".join(
                character
                for character in group
                if character not in AMBIGUOUS
            )
            for group in groups
        ]

    groups = [
        group
        for group in groups
        if group
    ]

    if not groups:
        raise ValueError(
            "Select at least one character category."
        )

    if length < len(groups):
        raise ValueError(
            "Length must be at least the number "
            "of selected categories."
        )

    if not 4 <= length <= 200:
        raise ValueError(
            "Choose a length between 4 and 200 characters."
        )

    # Ensure at least one character from each selected category.
    result = [
        secrets.choice(group)
        for group in groups
    ]

    pool = "".join(groups)

    # Fill the remaining length.
    result.extend(
        secrets.choice(pool)
        for _ in range(length - len(result))
    )

    # Securely shuffle the resulting characters.
    SYS_RANDOM.shuffle(result)

    return "".join(result)


def main() -> None:
    """Launch the graphical password-generator window."""

    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()

    except Exception as exc:
        print(f"Cannot open GUI: {exc}")
        return

    root.title("Secure Password Generator")
    root.geometry("530x340")
    root.resizable(False, False)

    frame = tk.Frame(
        root,
        padx=18,
        pady=18,
    )

    frame.pack(
        fill="both",
        expand=True,
    )

    length = tk.IntVar(value=20)

    upper = tk.BooleanVar(value=True)
    lower = tk.BooleanVar(value=True)
    digits = tk.BooleanVar(value=True)
    symbols = tk.BooleanVar(value=True)
    no_ambiguous = tk.BooleanVar(value=False)

    password_var = tk.StringVar(value="")

    tk.Label(
        frame,
        text="Password length",
    ).grid(
        row=0,
        column=0,
        sticky="w",
    )

    tk.Scale(
        frame,
        from_=4,
        to=64,
        orient="horizontal",
        variable=length,
        length=290,
    ).grid(
        row=0,
        column=1,
        sticky="we",
    )

    options = [
        ("Include uppercase", upper),
        ("Include lowercase", lower),
        ("Include numbers", digits),
        ("Include symbols", symbols),
        ("Exclude ambiguous characters", no_ambiguous),
    ]

    for index, (name, variable) in enumerate(
        options,
        start=1,
    ):
        tk.Checkbutton(
            frame,
            text=name,
            variable=variable,
        ).grid(
            row=index,
            column=0,
            columnspan=2,
            sticky="w",
        )

    tk.Label(
        frame,
        text="Generated password",
    ).grid(
        row=6,
        column=0,
        sticky="w",
        pady=(10, 0),
    )

    tk.Entry(
        frame,
        textvariable=password_var,
        state="readonly",
        width=43,
    ).grid(
        row=7,
        column=0,
        columnspan=2,
        sticky="we",
    )

    def regenerate():
        try:
            password = generate_password(
                length=length.get(),
                include_upper=upper.get(),
                include_lower=lower.get(),
                include_numbers=digits.get(),
                exclude_ambi=no_ambiguous.get(),
                include_sym=symbols.get(),
            )

            password_var.set(password)

        except ValueError as exc:
            messagebox.showerror(
                "Password generator",
                str(exc),
            )

    def copy():
        if password_var.get():
            root.clipboard_clear()
            root.clipboard_append(
                password_var.get()
            )

            root.update()

            messagebox.showinfo(
                "Copied",
                "Copied to clipboard. "
                "Clear the clipboard after use.",
            )

    tk.Button(
        frame,
        text="Generate password",
        command=regenerate,
    ).grid(
        row=8,
        column=0,
        pady=14,
    )

    tk.Button(
        frame,
        text="Copy",
        command=copy,
    ).grid(
        row=8,
        column=1,
        pady=14,
    )

    tk.Label(
        frame,
        text=(
            "Generated passwords are not "
            "written to plaintext files."
        ),
    ).grid(
        row=9,
        column=0,
        columnspan=2,
        sticky="w",
    )

    regenerate()

    root.mainloop()


if __name__ == "__main__":
    main()