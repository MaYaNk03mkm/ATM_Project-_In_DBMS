import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime

# ---- Database Setup ----
def init_db():
    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            pin TEXT,
            balance REAL
        )
    ''')

    # TRANSACTIONS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            txn_type TEXT,
            amount REAL,
            balance_after REAL,
            date_time TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---- Helper Functions ----
def get_user(pin):
    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE pin=?", (pin,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_balance(pin, new_balance):
    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance=? WHERE pin=?", (new_balance, pin))
    conn.commit()
    conn.close()

def record_txn(user_id, txn_type, amount, balance_after):
    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (user_id, txn_type, amount, balance_after, date_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, txn_type, amount, balance_after, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# ---- GUI Functions ----
def register_user():
    name = reg_name.get()
    pin = reg_pin.get()
    balance = reg_balance.get()

    if not name or not pin or not balance:
        messagebox.showwarning("Error", "All fields are required!")
        return

    try:
        balance = float(balance)
    except:
        messagebox.showwarning("Error", "Balance must be a number!")
        return

    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name, pin, balance) VALUES (?, ?, ?)", (name, pin, balance))
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", "User Registered Successfully!")
    reg_name.delete(0, tk.END)
    reg_pin.delete(0, tk.END)
    reg_balance.delete(0, tk.END)

def login_user():
    pin = login_pin.get()
    user = get_user(pin)
    if user:
        global current_user
        current_user = user
        login_frame.pack_forget()
        atm_menu()
    else:
        messagebox.showerror("Error", "Invalid PIN")

def atm_menu():
    menu_frame = tk.Frame(root, bg="#e8f4f8")
    menu_frame.pack(fill="both", expand=True)

    tk.Label(menu_frame, text=f"Welcome, {current_user[1]}", font=("Arial", 16, "bold"),
             bg="#0078D7", fg="white", pady=10).pack(fill=tk.X)

    tk.Button(menu_frame, text="Check Balance", width=20,
              command=lambda: check_balance(menu_frame)).pack(pady=10)
    tk.Button(menu_frame, text="Deposit Money", width=20,
              command=lambda: deposit_money(menu_frame)).pack(pady=10)
    tk.Button(menu_frame, text="Withdraw Money", width=20,
              command=lambda: withdraw_money(menu_frame)).pack(pady=10)
    tk.Button(menu_frame, text="View Transactions", width=20,
              command=view_history).pack(pady=10)
    tk.Button(menu_frame, text="Logout", width=20, bg="#dc3545", fg="white",
              command=lambda: logout(menu_frame)).pack(pady=10)

def check_balance(frame):
    messagebox.showinfo("Balance", f"Your current balance is ₹{current_user[3]}")

def deposit_money(frame):
    def deposit():
        amount = deposit_entry.get()
        try:
            amount = float(amount)
            new_balance = current_user[3] + amount
            update_balance(current_user[2], new_balance)
            record_txn(current_user[0], "Deposit", amount, new_balance)
            messagebox.showinfo("Success", f"₹{amount} deposited successfully!")
            refresh_user()
            deposit_window.destroy()
        except:
            messagebox.showwarning("Error", "Enter a valid amount")

    deposit_window = tk.Toplevel(root)
    deposit_window.title("Deposit Money")
    tk.Label(deposit_window, text="Enter amount:").pack(pady=5)
    deposit_entry = tk.Entry(deposit_window)
    deposit_entry.pack(pady=5)
    tk.Button(deposit_window, text="Deposit", command=deposit).pack(pady=10)

def withdraw_money(frame):
    def withdraw():
        amount = withdraw_entry.get()
        try:
            amount = float(amount)
            if amount > current_user[3]:
                messagebox.showwarning("Error", "Insufficient balance!")
            else:
                new_balance = current_user[3] - amount
                update_balance(current_user[2], new_balance)
                record_txn(current_user[0], "Withdraw", amount, new_balance)
                messagebox.showinfo("Success", f"₹{amount} withdrawn successfully!")
                refresh_user()
                withdraw_window.destroy()
        except:
            messagebox.showwarning("Error", "Enter a valid amount")

    withdraw_window = tk.Toplevel(root)
    withdraw_window.title("Withdraw Money")
    tk.Label(withdraw_window, text="Enter amount:").pack(pady=5)
    withdraw_entry = tk.Entry(withdraw_window)
    withdraw_entry.pack(pady=5)
    tk.Button(withdraw_window, text="Withdraw", command=withdraw).pack(pady=10)

def refresh_user():
    global current_user
    current_user = get_user(current_user[2])

def view_history():
    hist = tk.Toplevel(root)
    hist.title("Transaction History")
    hist.geometry("600x350")

    cols = ("ID", "Date/Time", "Type", "Amount", "Balance After")
    tree = ttk.Treeview(hist, columns=cols, show="headings", height=12)
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, anchor=tk.CENTER, width=110)

    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    conn = sqlite3.connect("atm.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT id, date_time, txn_type, amount, balance_after
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 100
    """, (current_user[0],))
    rows = cur.fetchall()
    conn.close()

    for r in rows:
        tree.insert("", tk.END, values=r)

def logout(frame):
    frame.pack_forget()
    login_screen()

def register_screen():
    main_frame.pack_forget()
    global reg_name, reg_pin, reg_balance
    reg_frame = tk.Frame(root, bg="#e8f4f8")
    reg_frame.pack(fill="both", expand=True)

    tk.Label(reg_frame, text="Register New User", font=("Arial", 16, "bold"),
             bg="#0078D7", fg="white", pady=10).pack(fill=tk.X)

    tk.Label(reg_frame, text="Name:").pack(pady=5)
    reg_name = tk.Entry(reg_frame)
    reg_name.pack(pady=5)

    tk.Label(reg_frame, text="PIN:").pack(pady=5)
    reg_pin = tk.Entry(reg_frame, show="*")
    reg_pin.pack(pady=5)

    tk.Label(reg_frame, text="Initial Balance:").pack(pady=5)
    reg_balance = tk.Entry(reg_frame)
    reg_balance.pack(pady=5)

    tk.Button(reg_frame, text="Register", bg="#28a745", fg="white",
              command=register_user).pack(pady=10)
    tk.Button(reg_frame, text="Back",
              command=lambda: [reg_frame.pack_forget(), main_frame.pack()]).pack(pady=5)

def login_screen():
    global login_frame, login_pin
    login_frame = tk.Frame(root, bg="#e8f4f8")
    login_frame.pack(fill="both", expand=True)

    tk.Label(login_frame, text="ATM Login", font=("Arial", 16, "bold"),
             bg="#0078D7", fg="white", pady=10).pack(fill=tk.X)
    tk.Label(login_frame, text="Enter PIN:").pack(pady=10)
    login_pin = tk.Entry(login_frame, show="*")
    login_pin.pack(pady=5)
    tk.Button(login_frame, text="Login", command=login_user,
              bg="#0078D7", fg="white").pack(pady=10)
    tk.Button(login_frame, text="Back",
              command=lambda: [login_frame.pack_forget(), main_frame.pack()]).pack()

# ---- Main Window ----
root = tk.Tk()
root.title("💳 ATM Machine System")
root.geometry("400x400")
root.config(bg="#e8f4f8")

main_frame = tk.Frame(root, bg="#e8f4f8")
main_frame.pack(fill="both", expand=True)

tk.Label(main_frame, text="💳 ATM Machine System", font=("Arial", 18, "bold"),
         bg="#0078D7", fg="white", pady=10).pack(fill=tk.X)
tk.Button(main_frame, text="Login", width=20, bg="#0078D7", fg="white",
          command=lambda: [main_frame.pack_forget(), login_screen()]).pack(pady=20)
tk.Button(main_frame, text="Register", width=20, bg="#28a745", fg="white",
          command=register_screen).pack(pady=10)
tk.Button(main_frame, text="Exit", width=20, bg="#dc3545", fg="white",
          command=root.destroy).pack(pady=10)

root.mainloop()
