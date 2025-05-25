from flask import Flask, render_template, redirect, request, url_for, session
from datetime import datetime
import sqlite3
import json

app = Flask(__name__)
app.secret_key = "chatdev-krdnz-2025"

users_db = {}

@app.route('/')
def index():
    return redirect(url_for('login')) 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        if form_type == 'login':
            cursor.execute("SELECT * FROM kullanicilar WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()
            if user:
                session['username'] = username
                if username == "admin":
                    return redirect('/admin') 
                return redirect('/dashboard')
            else:
                return "Giriş hatalı! Kullanıcı adı veya şifre yanlış.", 400

        elif form_type == 'register':
            email = request.form.get('email')
            telefon = request.form.get('telefon')

            cursor.execute("SELECT * FROM kullanicilar WHERE username = ?", (username,))
            existing = cursor.fetchone()
            if existing:
                return "Bu kullanıcı adı zaten var!", 400

            cursor.execute("""
                INSERT INTO kullanicilar (username, password, email, telefon)
                VALUES (?, ?, ?, ?)
            """, (username, password, email, telefon))
            conn.commit()

            session['username'] = username
            if username == "admin":
                return redirect('/admin') 
            return redirect('/dashboard')

    return render_template('login.html')
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    today = datetime.today().date()
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT arac, MAX(bitis_tarihi)
        FROM kiralamalar
        GROUP BY arac
    """)
    bitisler = cursor.fetchall()

    for arac, bitis in bitisler:
        try:
            bitis_tarih = datetime.strptime(bitis, "%Y-%m-%d").date()
            if bitis_tarih < today:
                cursor.execute("UPDATE araclar SET durum = 'Müsait' WHERE model = ?", (arac,))
        except:
            pass

    conn.commit()


    model_filter = request.args.get('model', '').strip()
    if model_filter:
        cursor.execute("SELECT * FROM araclar WHERE durum = 'Müsait' AND model LIKE ?", (f"%{model_filter}%",))
    else:
        cursor.execute("SELECT * FROM araclar WHERE durum = 'Müsait'")
    araclar = cursor.fetchall()


    if request.method == 'POST':
        car = request.form['car']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        kullanici = session.get('username', 'Anonim')

        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        if start < today or end < today or end < start:
            conn.close()
            return "Geçersiz tarih seçimi!", 400

        gun_sayisi = max((end - start).days, 1)
        cursor.execute("SELECT fiyat FROM araclar WHERE model = ?", (car,))
        sonuc = cursor.fetchone()
        fiyat = sonuc[0] if sonuc else 0
        toplam_fiyat = gun_sayisi * fiyat

        conn.close()
        return render_template('confirmation.html', car=car, start_date=start_date, end_date=end_date, toplam_fiyat=toplam_fiyat)

    conn.close()
    return render_template('dashboard.html', araclar=araclar)

@app.route('/confirmation', methods=['POST'])
def confirmation():
    if 'username' not in session:
        return redirect('/login')
    car = request.form['car']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    return render_template('confirmation.html', car=car, start_date=start_date, end_date=end_date)

@app.route('/payment', methods=['POST'])
def payment():
    if 'username' not in session:
        return redirect('/login')

    car = request.form['car']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    toplam_fiyat = request.form['toplam_fiyat']

    return render_template('odeme.html',
                           car=car,
                           start_date=start_date,
                           end_date=end_date,
                           toplam_fiyat=toplam_fiyat)

@app.route('/complete', methods=['POST'])
def complete():
    if 'username' not in session:
        return redirect('/login')
    car = request.form['car']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    toplam_fiyat = float(request.form['toplam_fiyat'])
    kullanici = session.get('username', 'Anonim')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO kiralamalar (kullanici, arac, baslangic_tarihi, bitis_tarihi, toplam_fiyat)
        VALUES (?, ?, ?, ?, ?)
    """, (kullanici, car, start_date, end_date, toplam_fiyat))
    cursor.execute("UPDATE araclar SET durum = 'Kirada' WHERE TRIM(model) = ?", (car.strip(),))
    conn.commit()
    conn.close()

    return render_template('complete.html')

@app.route("/arac-ekle", methods=["GET", "POST"])
def arac_ekle():
    if session.get('username') != 'admin': 
        return "Bu sayfa sadece admin kullanıcıya özeldir.", 403

    if request.method == "POST":
        model = request.form["model"]
        plaka = request.form["plaka"]
        durum = request.form["durum"]
        fiyat = request.form["fiyat"]
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO araclar (model, plaka, durum, fiyat) VALUES (?, ?, ?, ?)",
                       (model, plaka, durum, fiyat))
        conn.commit()
        conn.close()
        return redirect("/arac-ekle")

    return render_template("arac_ekle.html")

@app.route("/arac-listesi")
def arac_listesi():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM araclar")
    araclar = cursor.fetchall()
    conn.close()
    return render_template("arac_listesi.html", araclar=araclar)

@app.route("/kiralama-listesi")
def kiralama_listesi():
    if session.get('username') != 'admin':
        return "Bu sayfa sadece admin tarafından görüntülenebilir.", 403

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    today = datetime.today().date()


    cursor.execute("SELECT * FROM kiralamalar WHERE bitis_tarihi < ?", (today,))
    gecmis_kiralamalar = cursor.fetchall()

    cursor.execute("SELECT * FROM kiralamalar WHERE bitis_tarihi >= ?", (today,))
    aktif_kiralamalar = cursor.fetchall()

    conn.close()
    return render_template(
        "kiralama_listesi.html",
        gecmis_kiralamalar=gecmis_kiralamalar,
        aktif_kiralamalar=aktif_kiralamalar
    )

@app.route("/arac-sil/<int:id>")
def arac_sil(id):
    if session.get('username') != 'admin':
        return "Bu işlem sadece admin tarafından yapılabilir.", 403

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM araclar WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/arac-listesi")


@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if session.get('username') != 'admin':
        return "Yetkisiz erişim!", 403

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == 'POST':
        model = request.form['model']
        plaka = request.form['plaka']
        durum = request.form['durum']
        fiyat = request.form['fiyat']
        image_url = request.form.get('image_url', '')
        cursor.execute(
            "INSERT INTO araclar (model, plaka, durum, fiyat, image_url) VALUES (?, ?, ?, ?, ?)",
            (model, plaka, durum, fiyat, image_url)
        )
        conn.commit()

    cursor.execute("SELECT * FROM araclar")
    araclar = cursor.fetchall()
    conn.close()
    return render_template("admin_panel.html", araclar=araclar)

@app.route("/admin-arac-sil/<int:id>")
def admin_arac_sil(id):
    if session.get('username') != 'admin':
        return "Yetkisiz erişim!", 403

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM araclar WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/kiralama-sil/<int:id>")
def kiralama_sil(id):
    if session.get('username') != 'admin':
        return "Bu işlem sadece admin tarafından yapılabilir.", 403

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kiralamalar WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/kiralama-listesi")

@app.route('/json-veri-aktar')
def json_veri_aktar():
    if session.get('username') != 'admin':
        return "Bu işlem sadece admin tarafından yapılabilir.", 403

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT kullanici, arac, baslangic_tarihi, bitis_tarihi, toplam_fiyat FROM kiralamalar")
    kiralamalar = cursor.fetchall()
    conn.close()

    kiralama_listesi = []
    for k in kiralamalar:
        kiralama_listesi.append({
            "kullanici": k[0],
            "arac": k[1],
            "baslangic_tarihi": k[2],
            "bitis_tarihi": k[3],
            "toplam_fiyat": k[4]
        })

    with open("kiralamalar.json", "w", encoding="utf-8") as f:
        json.dump(kiralama_listesi, f, ensure_ascii=False, indent=4)

    return "Kiralama verileri JSON formatında 'kiralamalar.json' dosyasına başarıyla aktarıldı."

@app.route('/kazanc')
def kazanc_raporu():
    if session.get('username') != 'admin':
        return "Bu sayfa sadece admin tarafından görüntülenebilir.", 403

    today = datetime.today().date()
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

 
    cursor.execute("SELECT * FROM kiralamalar WHERE bitis_tarihi < ?", (today,))
    gecmis_kiralamalar = cursor.fetchall()
    cursor.execute("SELECT SUM(toplam_fiyat) FROM kiralamalar WHERE bitis_tarihi < ?", (today,))
    gecmis_gelir = cursor.fetchone()[0] or 0

   
    cursor.execute("SELECT * FROM kiralamalar WHERE bitis_tarihi >= ?", (today,))
    aktif_kiralamalar = cursor.fetchall()
    cursor.execute("SELECT SUM(toplam_fiyat) FROM kiralamalar WHERE bitis_tarihi >= ?", (today,))
    aktif_gelir = cursor.fetchone()[0] or 0

    toplam = gecmis_gelir + aktif_gelir

    conn.close()

    return render_template("kazanc.html",
                           gecmis_kiralamalar=gecmis_kiralamalar,
                           aktif_kiralamalar=aktif_kiralamalar,
                           gecmis_gelir=gecmis_gelir,
                           aktif_gelir=aktif_gelir,
                           toplam=toplam)

@app.route('/kullanicilar')
def kullanici_listesi():
    if session.get('username') != 'admin':
        return "Yetkisiz erişim!", 403

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, email, telefon FROM kullanicilar")
    kullanicilar = cursor.fetchall()
    conn.close()

    return render_template("kullanicilar.html", kullanicilar=kullanicilar)

@app.route('/kullanici-sil/<string:username>')
def kullanici_sil(username):
    if session.get('username') != 'admin':
        return "Yetkisiz erişim!", 403
    if username == "admin":
        return "Admin hesabı silinemez!", 400

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kullanicilar WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return redirect("/kullanicilar")

@app.route("/arac-durum-guncelle/<int:id>")
def arac_durum_guncelle(id):
    if session.get('username') != 'admin':
        return "Yetkisiz erişim!", 403

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE araclar SET durum = 'Müsait' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")


#if __name__ == '__main__':
#    app.run(debug=True)
    
import os
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
