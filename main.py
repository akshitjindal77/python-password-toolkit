"""Single entry point for the Password Security Toolkit."""

from manager.manager import main as manager_main
from generator.generator import main as generator_main
from cracker.cracker import main as audit_main


def main():
    while True:
        print("\n" + "=" * 49)
        print("        PASSWORD SECURITY TOOLKIT")
        print("=" * 49)

        print("1. Encrypted password manager")
        print("2. Password generator (Tkinter window)")
        print("3. Password hash-audit demonstrations")
        print("4. Exit")

        answer = input("Choose 1-4: ").strip()

        if answer == "1":
            manager_main()
        elif answer == "2":
            generator_main()
        elif answer == "3":
            audit_main()
        elif answer == "4":
            print("Goodbye.")
            return
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()