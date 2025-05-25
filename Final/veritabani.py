import sqlite3

baglanti = sqlite3.connect("database.db")
imlec = baglanti.cursor()


imlec.execute("""
CREATE TABLE IF NOT EXISTS araclar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model TEXT NOT NULL,
    plaka TEXT NOT NULL,
    durum TEXT NOT NULL,
    fiyat REAL NOT NULL
)
""")

imlec.execute("""
CREATE TABLE IF NOT EXISTS kullanicilar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

imlec.execute("""
CREATE TABLE IF NOT EXISTS kiralamalar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici TEXT NOT NULL,
    arac TEXT NOT NULL,
    baslangic_tarihi TEXT NOT NULL,
    bitis_tarihi TEXT NOT NULL
)
""")
imlec.execute("""
CREATE TABLE IF NOT EXISTS kiralamalar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici TEXT NOT NULL,
    arac TEXT NOT NULL,
    baslangic_tarihi TEXT NOT NULL,
    bitis_tarihi TEXT NOT NULL
)
""")




imlec.execute("INSERT OR IGNORE INTO kullanicilar (username, password) VALUES (?, ?)", ('admin', '1234'))





baglanti.commit()
baglanti.close()
