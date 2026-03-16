import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'trustconsulting_gizli_anahtar'

# Dil dosyaları (kısaltılmış, sadece tr ile test edelim)
diller = {
    'tr': {
        'ana_baslik': 'Trust Consulting',
        'menu_anasayfa': 'Ana Sayfa',
        'menu_hakkimizda': 'Hakkımızda',
        'menu_hizmetler': 'Hizmetler',
        'menu_iletisim': 'İletişim',
        'footer_telif': '© 2026 Trust Consulting. Tüm hakları saklıdır.',
        'index_baslik': 'Güven Yönetimi Danışmanlığı',
        'index_alt_baslik': 'İşinizi bir üst seviyeye taşıyoruz.',
        'index_duyuru1': 'Yeni ofisimiz açıldı.',
        'index_duyuru2': 'Online danışmanlık başladı.',
        'hakkimizda_baslik': 'Hakkımızda',
        'hakkimizda_icerik': 'Trust Consulting olarak...',
        'hizmetler_baslik': 'Hizmetlerimiz',
        'hizmet1_baslik': 'Kurumsal Danışmanlık',
        'hizmet1_aciklama': 'Profesyonel destek.',
        'hizmet2_baslik': 'Dijital Dönüşüm',
        'hizmet2_aciklama': 'Verimlilik artışı.',
        'hizmet3_baslik': 'Finansal Danışmanlık',
        'hizmet3_aciklama': 'Bütçe yönetimi.',
        'hizmet4_baslik': 'Eğitim ve Gelişim',
        'hizmet4_aciklama': 'Kurumsal eğitim.',
        'iletisim_baslik': 'İletişim',
        'iletisim_form_isim': 'İsim',
        'iletisim_form_email': 'E-posta',
        'iletisim_form_mesaj': 'Mesaj',
        'iletisim_form_gonder': 'Gönder',
        'mesaj_basarili': 'Mesajınız gönderildi!',
    },
    # ru ve tk kısımlarını geçici olarak kaldırdım, sorun çözülünce ekleriz
}

@app.before_request
def dil_ayarla():
    if 'dil' not in session:
        session['dil'] = 'tr'
    if request.args.get('dil'):
        session['dil'] = request.args.get('dil')
        return redirect(request.path)

@app.context_processor
def aktar_dil():
    return dict(dil_kodu=session.get('dil', 'tr'), diller=diller)

# Veritabanı bağlantısı (hata yakalama ile)
def get_db():
    try:
        conn = sqlite3.connect('site.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"Veritabanı bağlantı hatası: {e}")
        return None

def init_db():
    db = get_db()
    if db:
        try:
            db.execute('''
                CREATE TABLE IF NOT EXISTS mesajlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    isim TEXT NOT NULL,
                    email TEXT NOT NULL,
                    mesaj TEXT NOT NULL,
                    tarih TEXT NOT NULL
                )
            ''')
            db.commit()
            logging.info("Veritabanı tablosu oluşturuldu/var.")
        except Exception as e:
            logging.error(f"Tablo oluşturma hatası: {e}")
        finally:
            db.close()

# Uygulama başlarken veritabanını oluştur
init_db()

@app.route('/')
def index():
    logging.debug("Ana sayfa çağrıldı")
    try:
        return render_template('index.html', baslik='Ana Sayfa')
    except Exception as e:
        logging.error(f"index hatası: {e}")
        return "Bir hata oluştu", 500

@app.route('/hakkimizda')
def hakkimizda():
    return render_template('hakkimizda.html', baslik='Hakkımızda')

@app.route('/hizmetler')
def hizmetler():
    return render_template('hizmetler.html', baslik='Hizmetlerimiz')

@app.route('/iletisim', methods=['GET', 'POST'])
def iletisim():
    if request.method == 'POST':
        isim = request.form['isim']
        email = request.form['email']
        mesaj = request.form['mesaj']
        tarih = datetime.now().strftime('%d.%m.%Y %H:%M')
        
        db = get_db()
        if db:
            try:
                db.execute(
                    'INSERT INTO mesajlar (isim, email, mesaj, tarih) VALUES (?, ?, ?, ?)',
                    (isim, email, mesaj, tarih)
                )
                db.commit()
                flash(diller[session.get('dil', 'tr')]['mesaj_basarili'], 'success')
            except Exception as e:
                logging.error(f"Mesaj kayıt hatası: {e}")
                flash("Bir hata oluştu.", 'error')
            finally:
                db.close()
        else:
            flash("Veritabanı bağlantı hatası.", 'error')
        return redirect(url_for('iletisim'))
    
    return render_template('iletisim.html', baslik='İletişim')

@app.route('/mesajlar')
def mesajlar():
    db = get_db()
    if db:
        mesajlar = db.execute('SELECT * FROM mesajlar ORDER BY id DESC').fetchall()
        db.close()
        return render_template('mesajlar.html', mesajlar=mesajlar)
    else:
        return "Veritabanı hatası", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)