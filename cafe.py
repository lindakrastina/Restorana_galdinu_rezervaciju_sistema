import sqlite3
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
import bcrypt
import re

# ------------------------
# DATU BĀZE
# ------------------------
conn = sqlite3.connect("restorans2.db")
cursor = conn.cursor()

# Lietotāji (login/registration)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Klienti, galdiņi, rezervācijas
cursor.execute("""
CREATE TABLE IF NOT EXISTS klienti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vards TEXT NOT NULL,
    telefons TEXT NOT NULL
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS galdini (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vietas INTEGER NOT NULL
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS rezervacijas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    klients_id INTEGER,
    galdins_id INTEGER,
    datums TEXT,
    laiks TEXT,
    FOREIGN KEY (klients_id) REFERENCES klienti(id) ON DELETE CASCADE,
    FOREIGN KEY (galdins_id) REFERENCES galdini(id) ON DELETE CASCADE
)
""")
conn.commit()

# ------------------------
# LOGIN / REGISTRĀCIJA GUI
# ------------------------
def login_gui():
    def login():
        user = username_entry.get().strip()
        pw = password_entry.get().strip().encode("utf-8")
        cursor.execute("SELECT password FROM users WHERE username=?", (user,))
        result = cursor.fetchone()
        if result and bcrypt.checkpw(pw, result[0].encode("utf-8")):
            messagebox.showinfo("Veiksmīgi", "Login veiksmīgs!")
            root.destroy()
        else:
            messagebox.showerror("Kļūda", "Nepareizs lietotājvārds vai parole!")

    def validate_password(pw):
        if len(pw) < 8:
            return "❌ Parolei jābūt vismaz 8 simboliem!"
        if not re.search(r"[A-Z]", pw):
            return "❌ Parolei jābūt vismaz 1 lielajam burtam!"
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", pw):
            return "❌ Parolei jābūt vismaz 1 speciālajam simbolam!"
        return None

    def register():
        user = username_entry.get().strip()
        pw = password_entry.get().strip()
        if not user or not pw:
            messagebox.showerror("Kļūda", "Lietotājvārds un parole nedrīkst būt tukši!")
            return
        pw_error = validate_password(pw)
        if pw_error:
            messagebox.showerror("Nepareiza parole", pw_error)
            return
        pw_hash = bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pw_hash))
            conn.commit()
            messagebox.showinfo("Veiksmīgi", "Reģistrācija veiksmīga! Tagad vari login.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Kļūda", "Šāds lietotājvārds jau eksistē!")

    root = tk.Tk()
    root.title("Login / Reģistrācija")
    root.geometry("300x180")

    tk.Label(root, text="Lietotājvārds:").pack(pady=5)
    username_entry = tk.Entry(root)
    username_entry.pack()

    tk.Label(root, text="Parole:").pack(pady=5)
    password_entry = tk.Entry(root, show="*")
    password_entry.pack()

    tk.Button(root, text="Login", command=login).pack(pady=5)
    tk.Button(root, text="Reģistrēties", command=register).pack(pady=5)

    root.mainloop()

# ------------------------
# KONSOLE FUNKCIJAS
# ------------------------
def start_konsole():
    def derigs_datums(datums):
        try:
            d = datetime.strptime(datums, "%Y-%m-%d")
            return d.date() >= datetime.now().date()
        except:
            return False

    def derigs_laiks(datums, laiks):
        try:
            ievadits = datetime.strptime(f"{datums} {laiks}", "%Y-%m-%d %H:%M")
            return ievadits >= datetime.now()
        except:
            return False

    def eksiste(tabula, id):
        cursor.execute(f"SELECT * FROM {tabula} WHERE id=?", (id,))
        return cursor.fetchone() is not None

    # --- KLIENTI ---
    def pievienot_klientu():
        vards = input("Ievadi klienta vārdu: ").strip()
        if not all(x.isalpha() or x.isspace() for x in vards):
            print("❌ Kļūda: vārdā drīkst būt tikai burti!")
            return
        telefons = input("Ievadi telefona numuru: ").strip()
        if not telefons.isdigit():
            print("❌ Kļūda: telefona numuram jābūt ciparos!")
            return
        cursor.execute("INSERT INTO klienti (vards, telefons) VALUES (?, ?)", (vards, telefons))
        conn.commit()
        print("✅ Klients pievienots!")

    def dzest_klientu():
        paradit_klientus()
        klients_id = input("Ievadi klienta ID, ko dzēst: ")
        if not eksiste("klienti", klients_id):
            print("❌ Kļūda: klients neeksistē!")
            return
        cursor.execute("DELETE FROM klienti WHERE id=?", (klients_id,))
        cursor.execute("DELETE FROM rezervacijas WHERE klients_id=?", (klients_id,))
        conn.commit()
        print("✅ Klients un rezervācijas dzēstas!")

    def paradit_klientus():
        print("\n--- Klienti ---")
        cursor.execute("SELECT * FROM klienti")
        dati = cursor.fetchall()
        if not dati:
            print("Nav klientu.")
        for k in dati:
            print(f"[{k[0]}] {k[1]} | {k[2]}")

    # --- GALDIŅI ---
    def pievienot_galdinu():
        try:
            vietas = int(input("Ievadi vietu skaitu: "))
            if vietas <= 0:
                print("❌ Kļūda: jābūt pozitīvam skaitlim!")
                return
            cursor.execute("INSERT INTO galdini (vietas) VALUES (?)", (vietas,))
            conn.commit()
            print("✅ Galdiņš pievienots!")
        except:
            print("❌ Kļūda: ievadi skaitli!")

    def dzest_galdinu():
        paradit_galdinus()
        galdins_id = input("Ievadi galdiņa ID, ko dzēst: ")
        if not eksiste("galdini", galdins_id):
            print("❌ Kļūda: galdiņš neeksistē!")
            return
        cursor.execute("DELETE FROM galdini WHERE id=?", (galdins_id,))
        cursor.execute("DELETE FROM rezervacijas WHERE galdins_id=?", (galdins_id,))
        conn.commit()
        print("✅ Galdiņš un rezervācijas dzēstas!")

    def paradit_galdinus():
        print("\n--- Galdiņi ---")
        cursor.execute("SELECT * FROM galdini")
        dati = cursor.fetchall()
        if not dati:
            print("Nav galdiņu.")
        for g in dati:
            print(f"[{g[0]}] Vietas: {g[1]}")

    # --- REZERVĀCIJAS ---
    def rezervet():
        paradit_klientus()
        klients_id = input("Izvēlies klienta ID: ")
        if not eksiste("klienti", klients_id):
            print("❌ Kļūda: klients neeksistē!")
            return
        paradit_galdinus()
        galdins_id = input("Izvēlies galdiņa ID: ")
        if not eksiste("galdini", galdins_id):
            print("❌ Kļūda: galdiņš neeksistē!")
            return
        datums = input("Ievadi datumu (YYYY-MM-DD): ")
        if not derigs_datums(datums):
            print("❌ Kļūda: nepareizs vai pagātnes datums!")
            return
        laiks = input("Ievadi laiku (HH:MM): ")
        if not derigs_laiks(datums, laiks):
            print("❌ Kļūda: nevar rezervēt pagātnes laiku!")
            return
        jaunais_sakums = datetime.strptime(f"{datums} {laiks}", "%Y-%m-%d %H:%M")
        jaunais_beigas = jaunais_sakums + timedelta(hours=3)
        cursor.execute("SELECT datums, laiks FROM rezervacijas WHERE galdins_id=? AND datums=?", (galdins_id, datums))
        rezervacijas = cursor.fetchall()
        for rez in rezervacijas:
            vecais_sakums = datetime.strptime(f"{rez[0]} {rez[1]}", "%Y-%m-%d %H:%M")
            vecais_beigas = vecais_sakums + timedelta(hours=3)
            if jaunais_sakums < vecais_beigas and jaunais_beigas > vecais_sakums:
                print("❌ Šis galdiņš ir aizņemts (3h rezervācija)!")
                return
        cursor.execute("INSERT INTO rezervacijas (klients_id, galdins_id, datums, laiks) VALUES (?, ?, ?, ?)",
                       (klients_id, galdins_id, datums, laiks))
        conn.commit()
        print("✅ Rezervācija veikta uz 3 stundām!")

    def dzest_rezervaciju():
        paradit_rezervacijas()
        rez_id = input("Ievadi rezervācijas ID: ")
        if not eksiste("rezervacijas", rez_id):
            print("❌ Kļūda: rezervācija neeksistē!")
            return
        cursor.execute("DELETE FROM rezervacijas WHERE id=?", (rez_id,))
        conn.commit()
        print("✅ Rezervācija dzēsta!")

    def paradit_rezervacijas():
        print("\n--- Rezervācijas ---")
        cursor.execute("""
        SELECT rezervacijas.id, klienti.vards, klienti.telefons, galdini.vietas, datums, laiks
        FROM rezervacijas
        JOIN klienti ON rezervacijas.klients_id = klienti.id
        JOIN galdini ON rezervacijas.galdins_id = galdini.id
        """)
        dati = cursor.fetchall()
        if not dati:
            print("Nav rezervāciju.")
        for r in dati:
            print(f"[{r[0]}] {r[1]} ({r[2]}) | {r[3]} vietas | {r[4]} {r[5]}")

    # ------------------------
    # MENU
    # ------------------------
    def menu():
        while True:
            print("\n===== RESTORĀNS =====")
            print("1 - Pievienot klientu")
            print("2 - Dzēst klientu")
            print("3 - Pievienot galdiņu")
            print("4 - Dzēst galdiņu")
            print("5 - Rezervēt galdiņu")
            print("6 - Dzēst rezervāciju")
            print("7 - Parādīt rezervācijas")
            print("0 - Iziet")
            izvēle = input(">>> ")
            if izvēle == "1":
                pievienot_klientu()
            elif izvēle == "2":
                dzest_klientu()
            elif izvēle == "3":
                pievienot_galdinu()
            elif izvēle == "4":
                dzest_galdinu()
            elif izvēle == "5":
                rezervet()
            elif izvēle == "6":
                dzest_rezervaciju()
            elif izvēle == "7":
                paradit_rezervacijas()
            elif izvēle == "0":
                print("Programma beidzas.")
                break
            else:
                print("❌ Nepareiza izvēle!")

    menu()
    conn.close()

# ------------------------
# START
# ------------------------
login_gui()
start_konsole()