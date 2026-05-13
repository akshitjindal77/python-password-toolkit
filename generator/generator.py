import random
import tkinter as tk
from tkinter import *
import os

uppercase = "QWERTYUIOPASDFGHJKLZXCVBNM"
lowercase = "qwertyuioplkjhgfdsazxcvbnm"
numbers = "1234567890"
symbols = "`;/.,<>?:][}{|!@#$%^&+-"
ambiguous = "O0Il1|"

all = uppercase + lowercase + numbers + symbols

def creating_pool(include_upper, include_lower, include_numbers, exclude_ambi, include_sym):
    pool = ""
    if include_upper:
        pool += uppercase
    if include_lower:
        pool += lowercase
    if include_numbers:
        pool += numbers
    if include_sym:
        pool += symbols
    if exclude_ambi:
        pool = ''.join(filter(lambda ch: ch not in ambiguous, pool))
    return pool

def generator(length, include_upper, include_lower, include_numbers, exclude_ambi, include_sym):
    if length < 4:
        return "Not possible"
        
    
    pool = creating_pool(include_upper, include_lower, include_numbers, exclude_ambi, include_sym)

    if not pool:
        return "Choose at least one character type"
    
    password = []
    if include_upper:
        password.append(random.choice(uppercase))
    if include_lower:
        password.append(random.choice(lowercase))
    if include_numbers:
        password.append(random.choice(numbers))
    if include_sym:
        password.append(random.choice(symbols))
    
    newlength = length - len(password)
    for _ in range(newlength):
        randomChar = random.choice(pool)
        password.append(randomChar)
    
    random.shuffle(password)
    final_pass = ''.join(password)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(BASE_DIR, "demo", "passwordgenerator.txt")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as file:
        file.write(f"Password: {final_pass}")
    return final_pass


def update_pass():
    length = length_var.get()
    include_upper = upper.get()
    include_lower = lower.get()
    include_numbers = num.get()
    include_sym = sym.get()
    exclude_ambi = ambi.get()
    new_password = generator(length, include_upper, include_lower, include_numbers, exclude_ambi, include_sym)
    pass_var.set(new_password)


root = tk.Tk()
root.title('Password Generator')

length_var = IntVar(value=8)
upper = IntVar(value=1)
lower = IntVar(value=1)
num = IntVar(value=1)
sym = IntVar(value=1)
ambi = IntVar(value=0)
pass_var = StringVar()

update_pass()

frame = tk.Frame(root)
frame.pack()

tk.Label(frame, text="Length of the password: ").grid(row=0, column= 0, sticky = 'w')
len_slider = tk.Scale(frame, from_= 4, to = 200, orient="horizontal", variable = length_var, command=lambda x: update_pass())
len_slider.grid(row=0, column=1)

tk.Checkbutton(frame, text="Include Uppercase", variable=upper, command=update_pass).grid(row=2, column=0, columnspan=2, sticky="w")
tk.Checkbutton(frame, text="Include Lowercase", variable=lower, command=update_pass).grid(row=3, column=0, columnspan=2, sticky="w")
tk.Checkbutton(frame, text="Include Numbers", variable=num, command=update_pass).grid(row=4, column=0, columnspan=2, sticky="w")
tk.Checkbutton(frame, text="Include Symbols", variable=sym, command=update_pass).grid(row=5, column=0, columnspan=2, sticky="w")
tk.Checkbutton(frame, text="Exclude Ambiguous Characters", variable=ambi, command=update_pass).grid(row=6, column=0, columnspan=2, sticky="w")


tk.Label(frame, text="Generated Password:").grid(row=7, column=0, sticky="w", pady=10)
tk.Entry(frame, textvariable=pass_var, width=30, state="readonly").grid(row=7, column=1, pady=10)


tk.Button(frame, text="Generate Password", command=update_pass).grid(row=8, column=0, columnspan=2, pady=10)
root.mainloop()



