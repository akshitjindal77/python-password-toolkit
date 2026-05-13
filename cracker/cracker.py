import hashlib
import itertools

def hash_func(password, algorithm):
    h_pass = getattr(hashlib, algorithm, None)
    if not h_pass:
        raise ValueError(f"Unsupported hash algorithm {algorithm}")
    return h_pass(password.encode()).hexdigest()

def brute_force(target, charset, length, algorithm="sha256"):
    for curr_len in range(1, length+1):
        for combo in itertools.product(charset, repeat=curr_len):
            password = ''.join(combo)
            if hash_func(password, algorithm) == target:
                return password
    return None

def dictionary_attack(target, dictionary, algorithm="sha256"):
    try:
        with open(dictionary, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                password = line.strip()
                if hash_func(password, algorithm) == target:
                    return password
    except FileNotFoundError:
        print(f"Error: File {dictionary} not found")
    return None

def hybrid_attack(target, dictionary, charset, length, algorithm):
    try:
        with open(dictionary, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                base_pass = line.strip()
                for curr_length in range(1,length+1):
                    for combo in itertools.product(charset, repeat=curr_length):
                        suffix = ''.join(combo)
                        password = base_pass + suffix
                        if hash_func(password, algorithm) == target:
                            return password
    except FileNotFoundError:
        print(f"File {dictionary} not found")
    return None
                        

def main():
    target = input("Enter the target hash: ").strip()
    algorithm = input("Enter the algorithm: ") 
    attack_type = int(input("Choose attack type (1 for 'dictionary' , 2 for 'brute_force' or 3 for 'Hybrid): "))
    

    if attack_type == 1:
        dictionary = input("Enter the dictionary file: ")
        result = dictionary_attack(target, dictionary, algorithm)
        if result:
            print(f"Password found: {result}")
        else:
            print("Password not found")
    elif attack_type == 2:
        charset = input("Enter the character set: ")
        length = int(input("Enter the maximum length: "))
        result = brute_force(target, charset, length, algorithm)
        if result:
            print(f"Password found: {result}")
        else:
            print("Password not found")
    elif attack_type == 3:
        dictionary = input("Enter the dictionary file: ")
        charset = input("Enter the character set: ")
        length = int(input("Enter the maximum length: "))
        result = hybrid_attack(target, dictionary, charset, length, algorithm)
        if result:
            print(f"Password found: {result}")
        else:
            print("Password not found")

    else:
        print("The attack type you entered is invalid. Please choose 1, 2, or 3.")

if __name__ == "__main__":
    main()