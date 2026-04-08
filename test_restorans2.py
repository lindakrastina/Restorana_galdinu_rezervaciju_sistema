import pytest
from datetime import datetime, timedelta
from cafe import Database, RestaurantSystem  # nomaini uz savu faila nosaukumu


@pytest.fixture
def system():
    db = Database()
    sys = RestaurantSystem(db)
    yield sys
    db.close()


# ------------------------
# 1. TESTS: derigs_datums
# ------------------------
def test_derigs_datums(system):
    # Pozitīvie gadījumi
    sodien = datetime.now().strftime("%Y-%m-%d")
    nakotne = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    assert system.derigs_datums(sodien) == True
    assert system.derigs_datums(nakotne) == True

    # Negatīvie gadījumi
    vakar = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert system.derigs_datums(vakar) == False

    assert system.derigs_datums("2023-99-99") == False   # nepareizs datuma formāts
    assert system.derigs_datums("") == False             # tukšs datums
    assert system.derigs_datums("abc") == False          # pilnīgi nederīgs teksts


# ------------------------
# 2. TESTS: derigs_laiks
# ------------------------
def test_derigs_laiks(system):
    # Pozitīvais gadījums
    nakotne = datetime.now() + timedelta(hours=1)
    datums = nakotne.strftime("%Y-%m-%d")
    assert system.derigs_laiks(datums, nakotne.strftime("%H:%M")) == True

    # Negatīvie gadījumi
    pagatne = datetime.now() - timedelta(hours=1)
    assert system.derigs_laiks(datums, pagatne.strftime("%H:%M")) == False

    assert system.derigs_laiks(datums, "99:99") == False  # nepareizs laiks
    assert system.derigs_laiks("2023-99-99", "12:00") == False  # nederīgs datums
    assert system.derigs_laiks("", "") == False          # tukšs ievads


# ------------------------
# 3. TESTS: eksiste
# ------------------------
def test_eksiste(system):
    # Pozitīvais gadījums
    system.db.cursor.execute(
        "INSERT INTO klienti (vards, telefons) VALUES (?, ?)",
        ("Tests", "12345678")
    )
    system.db.commit()

    system.db.cursor.execute("SELECT id FROM klienti WHERE vards=?", ("Tests",))
    klienta_id = system.db.cursor.fetchone()[0]

    assert system.eksiste("klienti", klienta_id) == True

    # Negatīvie gadījumi
    assert system.eksiste("klienti", 99999) == False       # ID neeksistē
    assert system.eksiste("klienti", None) == False        # None kā ID
    assert system.eksiste("klienti", "abc") == False       # nederīgs tips