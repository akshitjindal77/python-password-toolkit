import hashlib
import json
import os
import base64
from cryptography.fernet import Fernet
import getpass

VAULT_FILE = os.path.join(os.path.dirname(__file__), 'vault.json')
MASTER_HASH_FILE = os.path.join(os.path.dirname(__file__), 'master.hash')

def generate_key(password):
    return Fernet.generate_key()

def encrypt_data(data, key):
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data, key):
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_master_hash():
    if os.path.exists(MASTER_HASH_FILE):
        with open(MASTER_HASH_FILE, 'r') as f:
            return f.read().strip()
    return None

def save_master_hash(master_hash):
    with open(MASTER_HASH_FILE, 'w') as f:
        f.write(master_hash)

def load_vault(key):
    if os.path.exists(VAULT_FILE):
        with open(VAULT_FILE, 'r') as f:
            encrypted_data = f.read()
            decrypted_data = decrypt_data(encrypted_data, key)
            return json.loads(decrypted_data)
    return {}

def save_vault(vault, key):
    encrypted_data = encrypt_data(json.dumps(vault), key)
    with open(VAULT_FILE, 'w') as f:
        f.write(encrypted_data)

def add_password(site, username, password, vault, key):
    vault[site] = {'username': username, 'password': password}
    save_vault(vault, key)

def get_password(site, vault):
    if site in vault:
        return vault[site]['username'], vault[site]['password']
    return None, None

def list_sites(vault):
    return list(vault.keys())

def delete_password(site, vault, key):
    if site in vault:
        del vault[site]
        save_vault(vault, key)
        return True
    return False

def main():
    master_hash = load_master_hash()
    if master_hash is None:
        # First run, set master password
        master_password = getpass.getpass("Set master password: ")
        confirm_password = getpass.getpass("Confirm master password: ")
        if master_password != confirm_password:
            print("Passwords do not match.")
            return
        master_hash = hash_password(master_password)
        save_master_hash(master_hash)
        entered_password = master_password
        print("Master password set.")
    else:
        # Verify master password
        entered_password = getpass.getpass("Enter master password: ")
        if hash_password(entered_password) != master_hash:
            print("Incorrect master password.")
            return

    # Generate key from master password
    key = base64.urlsafe_b64encode(hashlib.sha256(entered_password.encode()).digest())

    vault = load_vault(key)

    while True:
        print("\nPassword Manager")
        print("1. Add password")
        print("2. Get password")
        print("3. List sites")
        print("4. Delete password")
        print("5. Quit")
        choice = input("Choose an option: ").strip()

        if choice == '1':
            site = input("Site: ").strip()
            username = input("Username: ").strip()
            password = getpass.getpass("Password: ")
            add_password(site, username, password, vault, key)
            print("Password added.")
        elif choice == '2':
            site = input("Site: ").strip()
            username, password = get_password(site, vault)
            if username:
                print(f"Username: {username}")
                print(f"Password: {password}")
            else:
                print("Site not found.")
        elif choice == '3':
            sites = list_sites(vault)
            if sites:
                print("Sites:")
                for site in sites:
                    print(f"  - {site}")
            else:
                print("No sites stored.")
        elif choice == '4':
            site = input("Site: ").strip()
            if delete_password(site, vault, key):
                print("Password deleted.")
            else:
                print("Site not found.")
        elif choice == '5':
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()