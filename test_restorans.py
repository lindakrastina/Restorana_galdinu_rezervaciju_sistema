import pytest
from datetime import datetime, timedelta
from cafe import Database, RestaurantSystem  # <-- nomaini uz savu faila nosaukumu


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
    sodien = datetime.now().strftime("%Y-%m-%d")
    vakar = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    assert system.derigs_datums(sodien) == True
    assert system.derigs_datums(vakar) == False
    assert system.derigs_datums("2023-99-99") == False


# ------------------------
# 2. TESTS: derigs_laiks
# ------------------------
def test_derigs_laiks(system):
    nakotne = datetime.now() + timedelta(hours=1)
    pagatne = datetime.now() - timedelta(hours=1)

    datums = nakotne.strftime("%Y-%m-%d")

    assert system.derigs_laiks(datums, nakotne.strftime("%H:%M")) == True
    assert system.derigs_laiks(datums, pagatne.strftime("%H:%M")) == False
    assert system.derigs_laiks(datums, "99:99") == False


# ------------------------
# 3. TESTS: eksiste
# ------------------------
def test_eksiste(system):
    # ievietojam testdatus
    system.db.cursor.execute(
        "INSERT INTO klienti (vards, telefons) VALUES (?, ?)",
        ("Tests", "12345678")
    )
    system.db.commit()

    # paņemam ID
    system.db.cursor.execute("SELECT id FROM klienti WHERE vards=?", ("Tests",))
    klienta_id = system.db.cursor.fetchone()[0]

    assert system.eksiste("klienti", klienta_id) == True
    assert system.eksiste("klienti", 99999) == False

    