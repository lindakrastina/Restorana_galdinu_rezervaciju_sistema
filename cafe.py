import sqlite3
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
import bcrypt
import re
import requests


# ------------------------
# DATU BĀZE
# ------------------------
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("restorans2.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS klienti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vards TEXT NOT NULL,
            telefons TEXT NOT NULL
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS galdini (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vietas INTEGER NOT NULL
        )
        """)

        self.cursor.execute("""
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

        self.conn.commit()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


# ------------------------
# LOGIN / REGISTRĀCIJA GUI
# ------------------------
class AuthGUI:
    def __init__(self, db):
        self.db = db

    def login_gui(self):
        def login():
            user = username_entry.get().strip()
            pw = password_entry.get().strip().encode("utf-8")

            self.db.cursor.execute("SELECT password FROM users WHERE username=?", (user,))
            result = self.db.cursor.fetchone()

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
                self.db.cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (user, pw_hash)
                )
                self.db.commit()
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
# SISTĒMA (KONSOLE + API)
# ------------------------
class RestaurantSystem:
    def __init__(self, db):
        self.db = db

    # API
    def paradit_edienkarti(self):
        print("\n--- Ēdienkarte (API) ---")
        try:
            response = requests.get("https://www.themealdb.com/api/json/v1/1/search.php?f=a")
            data = response.json()

            if data["meals"] is None:
                print("Nav ēdienu.")
                return

            for meal in data["meals"][:10]:
                print(f"🍽️ {meal['strMeal']} | {meal['strCategory']} | {meal['strArea']}")

        except Exception as e:
            print("❌ Kļūda ar API:", e)

    # PALĪG
    def derigs_datums(self, datums):
        try:
            d = datetime.strptime(datums, "%Y-%m-%d")
            return d.date() >= datetime.now().date()
        except:
            return False

    def derigs_laiks(self, datums, laiks):
        try:
            ievadits = datetime.strptime(f"{datums} {laiks}", "%Y-%m-%d %H:%M")
            return ievadits >= datetime.now()
        except:
            return False

    def eksiste(self, tabula, id):
        self.db.cursor.execute(f"SELECT * FROM {tabula} WHERE id=?", (id,))
        return self.db.cursor.fetchone() is not None

    # --- KLIENTI ---
    def pievienot_klientu(self):
        vards = input("Ievadi klienta vārdu: ").strip()
        if not all(x.isalpha() or x.isspace() for x in vards):
            print("❌ Kļūda: vārdā drīkst būt tikai burti!")
            return

        telefons = input("Ievadi telefona numuru: ").strip()
        if not telefons.isdigit():
            print("❌ Kļūda: telefona numuram jābūt ciparos!")
            return

        self.db.cursor.execute(
            "INSERT INTO klienti (vards, telefons) VALUES (?, ?)",
            (vards, telefons)
        )
        self.db.commit()
        print("✅ Klients pievienots!")

    def dzest_klientu(self):
        self.paradit_klientus()
        klients_id = input("Ievadi klienta ID, ko dzēst: ")

        if not self.eksiste("klienti", klients_id):
            print("❌ Kļūda: klients neeksistē!")
            return

        self.db.cursor.execute("DELETE FROM klienti WHERE id=?", (klients_id,))
        self.db.cursor.execute("DELETE FROM rezervacijas WHERE klients_id=?", (klients_id,))
        self.db.commit()
        print("✅ Klients un rezervācijas dzēstas!")

    def paradit_klientus(self):
        print("\n--- Klienti ---")
        self.db.cursor.execute("SELECT * FROM klienti")
        dati = self.db.cursor.fetchall()

        if not dati:
            print("Nav klientu.")

        for k in dati:
            print(f"[{k[0]}] {k[1]} | {k[2]}")

    # --- GALDIŅI ---
    def pievienot_galdinu(self):
        try:
            vietas = int(input("Ievadi vietu skaitu: "))
            if vietas <= 0:
                print("❌ Kļūda: jābūt pozitīvam skaitlim!")
                return

            self.db.cursor.execute("INSERT INTO galdini (vietas) VALUES (?)", (vietas,))
            self.db.commit()
            print("✅ Galdiņš pievienots!")
        except:
            print("❌ Kļūda: ievadi skaitli!")

    def dzest_galdinu(self):
        self.paradit_galdinus()
        galdins_id = input("Ievadi galdiņa ID, ko dzēst: ")

        if not self.eksiste("galdini", galdins_id):
            print("❌ Kļūda: galdiņš neeksistē!")
            return

        self.db.cursor.execute("DELETE FROM galdini WHERE id=?", (galdins_id,))
        self.db.cursor.execute("DELETE FROM rezervacijas WHERE galdins_id=?", (galdins_id,))
        self.db.commit()
        print("✅ Galdiņš un rezervācijas dzēstas!")

    def paradit_galdinus(self):
        print("\n--- Galdiņi ---")
        self.db.cursor.execute("SELECT * FROM galdini")
        dati = self.db.cursor.fetchall()

        if not dati:
            print("Nav galdiņu.")

        for g in dati:
            print(f"[{g[0]}] Vietas: {g[1]}")

    # --- REZERVĀCIJAS ---
    def rezervet(self):
        self.paradit_klientus()
        klients_id = input("Izvēlies klienta ID: ")

        if not self.eksiste("klienti", klients_id):
            print("❌ Kļūda: klients neeksistē!")
            return

        self.paradit_galdinus()
        galdins_id = input("Izvēlies galdiņa ID: ")

        if not self.eksiste("galdini", galdins_id):
            print("❌ Kļūda: galdiņš neeksistē!")
            return

        datums = input("Ievadi datumu (YYYY-MM-DD): ")
        if not self.derigs_datums(datums):
            print("❌ Kļūda: nepareizs vai pagātnes datums!")
            return

        laiks = input("Ievadi laiku (HH:MM): ")
        if not self.derigs_laiks(datums, laiks):
            print("❌ Kļūda: nevar rezervēt pagātnes laiku!")
            return

        jaunais_sakums = datetime.strptime(f"{datums} {laiks}", "%Y-%m-%d %H:%M")
        jaunais_beigas = jaunais_sakums + timedelta(hours=3)

        self.db.cursor.execute(
            "SELECT datums, laiks FROM rezervacijas WHERE galdins_id=? AND datums=?",
            (galdins_id, datums)
        )
        rezervacijas = self.db.cursor.fetchall()

        for rez in rezervacijas:
            vecais_sakums = datetime.strptime(f"{rez[0]} {rez[1]}", "%Y-%m-%d %H:%M")
            vecais_beigas = vecais_sakums + timedelta(hours=3)

            if jaunais_sakums < vecais_beigas and jaunais_beigas > vecais_sakums:
                print("❌ Šis galdiņš ir aizņemts (3h rezervācija)!")
                return

        self.db.cursor.execute(
            "INSERT INTO rezervacijas (klients_id, galdins_id, datums, laiks) VALUES (?, ?, ?, ?)",
            (klients_id, galdins_id, datums, laiks)
        )
        self.db.commit()
        print("✅ Rezervācija veikta uz 3 stundām!")

    def dzest_rezervaciju(self):
        self.paradit_rezervacijas()
        rez_id = input("Ievadi rezervācijas ID: ")

        if not self.eksiste("rezervacijas", rez_id):
            print("❌ Kļūda: rezervācija neeksistē!")
            return

        self.db.cursor.execute("DELETE FROM rezervacijas WHERE id=?", (rez_id,))
        self.db.commit()
        print("✅ Rezervācija dzēsta!")

    def paradit_rezervacijas(self):
        print("\n--- Rezervācijas ---")
        self.db.cursor.execute("""
        SELECT rezervacijas.id, klienti.vards, klienti.telefons, galdini.vietas, datums, laiks
        FROM rezervacijas
        JOIN klienti ON rezervacijas.klients_id = klienti.id
        JOIN galdini ON rezervacijas.galdins_id = galdini.id
        """)

        dati = self.db.cursor.fetchall()

        if not dati:
            print("Nav rezervāciju.")

        for r in dati:
            print(f"[{r[0]}] {r[1]} ({r[2]}) | {r[3]} vietas | {r[4]} {r[5]}")

    # MENU (IDENTISKS!)
    def menu(self):
        while True:
            print("\n===== RESTORĀNS =====")
            print("1 - Pievienot klientu")
            print("2 - Dzēst klientu")
            print("3 - Pievienot galdiņu")
            print("4 - Dzēst galdiņu")
            print("5 - Rezervēt galdiņu")
            print("6 - Dzēst rezervāciju")
            print("7 - Parādīt rezervācijas")
            print("8 - Parādīt ēdienkarti (API)")
            print("0 - Iziet")

            izvēle = input("Izvēlies darbību: ")

            if izvēle == "1":
                self.pievienot_klientu()
            elif izvēle == "2":
                self.dzest_klientu()
            elif izvēle == "3":
                self.pievienot_galdinu()
            elif izvēle == "4":
                self.dzest_galdinu()
            elif izvēle == "5":
                self.rezervet()
            elif izvēle == "6":
                self.dzest_rezervaciju()
            elif izvēle == "7":
                self.paradit_rezervacijas()
            elif izvēle == "8":
                self.paradit_edienkarti()
            elif izvēle == "0":
                print("Programma beidzas.")
                break
            else:
                print("❌ Nepareiza izvēle!")


# ------------------------
# START
# ------------------------
if __name__ == "__main__":
    db = Database()

    auth = AuthGUI(db)
    auth.login_gui()

    app = RestaurantSystem(db)
    app.menu()

    db.close()



    