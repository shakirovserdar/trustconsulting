import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import sqlite3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# E-posta ayarları — Render/hosting'de environment variable olarak set edin
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')        # Gönderen Gmail adresi
SMTP_PASS = os.environ.get('SMTP_PASS', '')        # Gmail App Password
BILDIRIM_EMAIL = 'info@trustedutm.com'             # Mesajların gideceği adres

def mail_gonder(isim, email, mesaj, tarih):
    if not SMTP_USER or not SMTP_PASS:
        logging.warning("SMTP ayarları yapılmamış, mail gönderilmedi.")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Yeni Mesaj: {isim} — Trust Consulting'
        msg['From'] = SMTP_USER
        msg['To'] = BILDIRIM_EMAIL
        msg['Reply-To'] = email
        html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f0f7ff;padding:20px;">
        <div style="max-width:500px;margin:auto;background:white;border-radius:12px;
                    padding:24px;border-top:4px solid #2271b1;">
            <h2 style="color:#2271b1;">Yeni Site Mesaji</h2>
            <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:8px;color:#666;width:100px;"><strong>Isim:</strong></td>
                    <td style="padding:8px;">{isim}</td></tr>
                <tr style="background:#f5f9fd;">
                    <td style="padding:8px;color:#666;"><strong>E-posta:</strong></td>
                    <td style="padding:8px;"><a href="mailto:{email}">{email}</a></td></tr>
                <tr><td style="padding:8px;color:#666;"><strong>Tarih:</strong></td>
                    <td style="padding:8px;">{tarih}</td></tr>
                <tr style="background:#f5f9fd;">
                    <td style="padding:8px;color:#666;vertical-align:top;"><strong>Mesaj:</strong></td>
                    <td style="padding:8px;">{mesaj}</td></tr>
            </table>
            <p style="margin-top:16px;font-size:12px;color:#aaa;">— trustedutm.com site formu</p>
        </div></body></html>
        """
        msg.attach(MIMEText(html, 'html'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, BILDIRIM_EMAIL, msg.as_string())
        logging.info(f"Mail gonderildi: {isim} <{email}>")
        return True
    except Exception as e:
        logging.error(f"Mail gonderme hatasi: {e}")
        return False

app = Flask(__name__)
app.secret_key = 'trustconsulting_gizli_anahtar'

diller = {
    'tr': {
        'lang_attr': 'tr',
        'menu_anasayfa': 'Ana Sayfa',
        'menu_hakkimizda': 'Hakkımızda',
        'menu_hizmetler': 'Hizmetler',
        'menu_iletisim': 'İletişim',
        'footer_telif': '© 2026 Trust Consulting. Tüm hakları saklıdır.',
        'footer_iletisim': 'İletişim',
        'index_baslik': '✈️ Vize & Seyahat Danışmanlığı',
        'index_alt_baslik': 'Türkmenistan\'dan dünyaya açılan kapınız.',
        'index_ulkeler_baslik': '🌍 Hizmet Verdiğimiz Ülkeler',
        'index_hizmet_baslik': '⚡ Hızlı Hizmetler',
        'index_cta': 'Ücretsiz Danışmanlık Al',
        'hakkimizda_baslik': 'Hakkımızda',
        'hakkimizda_metin': 'Trust Consulting olarak, Türkmenistan\'dan dünyanın dört bir yanına vize ve seyahat danışmanlığı hizmetleri sunuyoruz. Türkiye ve İstanbul ofislerimizle, müşterilerimize en hızlı ve güvenilir vize çözümlerini sağlıyoruz. Yıllarca edindiğimiz deneyimle, her vize sürecinde yanınızdayız.',
        'hakkimizda_misyon': 'Misyonumuz',
        'hakkimizda_misyon_metin': 'Türkmenistan\'daki insanlara istedikleri ülkeye güvenli, hızlı ve uygun fiyatlı vize almasında yardımcı olmak.',
        'hakkimizda_ofis1': '🇹🇲 Türkmenistan Ofisi',
        'hakkimizda_ofis2': '🇹🇷 İstanbul Ofisi',
        'hizmetler_baslik': '✈️ Hizmetlerimiz',
        'hizmetler_turkiye_baslik': '🇹🇷 Türkiye Vize Türleri',
        'hizmetler_diger_baslik': '🌍 Diğer Ülkeler',
        'hizmetler_ek_baslik': '➕ Ek Hizmetler',
        'hizmetler_egitim_baslik': '🎓 Türkiye\'de Eğitim',
        'iletisim_baslik': '📞 İletişim',
        'iletisim_form_baslik': 'Bize Yazın',
        'iletisim_form_isim': 'İsminiz',
        'iletisim_form_email': 'E-posta Adresiniz',
        'iletisim_form_mesaj': 'Mesajınız',
        'iletisim_form_gonder': '📤 Gönder',
        'iletisim_adres_baslik': '📍 Adreslerimiz',
        'iletisim_whatsapp': 'WhatsApp\'tan Yaz',
        'mesaj_basarili': '✅ Mesajınız gönderildi! En kısa sürede dönüş yapacağız.',
        'mesajlar_baslik': 'Gelen Mesajlar',
        'mesajlar_isim': 'İsim',
        'mesajlar_email': 'E-posta',
        'mesajlar_mesaj': 'Mesaj',
        'mesajlar_tarih': 'Tarih',
        'mesajlar_yok': 'Henüz mesaj yok.',
    },
    'ru': {
        'lang_attr': 'ru',
        'menu_anasayfa': 'Главная',
        'menu_hakkimizda': 'О нас',
        'menu_hizmetler': 'Услуги',
        'menu_iletisim': 'Контакты',
        'footer_telif': '© 2026 Trust Consulting. Все права защищены.',
        'footer_iletisim': 'Контакты',
        'index_baslik': '✈️ Визовые & Туристические Услуги',
        'index_alt_baslik': 'Ваши ворота из Туркменистана в мир.',
        'index_ulkeler_baslik': '🌍 Страны, с которыми мы работаем',
        'index_hizmet_baslik': '⚡ Быстрые услуги',
        'index_cta': 'Получить бесплатную консультацию',
        'hakkimizda_baslik': 'О нас',
        'hakkimizda_metin': 'Trust Consulting предоставляет визовые и туристические услуги из Туркменистана по всему миру. С офисами в Туркменистане и Стамбуле мы обеспечиваем нашим клиентам самые быстрые и надёжные визовые решения.',
        'hakkimizda_misyon': 'Наша миссия',
        'hakkimizda_misyon_metin': 'Помочь людям в Туркменистане безопасно, быстро и по доступным ценам получить визу в любую страну.',
        'hakkimizda_ofis1': '🇹🇲 Офис в Туркменистане',
        'hakkimizda_ofis2': '🇹🇷 Офис в Стамбуле',
        'hizmetler_baslik': '✈️ Наши услуги',
        'hizmetler_turkiye_baslik': '🇹🇷 Типы виз в Турцию',
        'hizmetler_diger_baslik': '🌍 Другие страны',
        'hizmetler_ek_baslik': '➕ Дополнительные услуги',
        'hizmetler_egitim_baslik': '🎓 Образование в Турции',
        'iletisim_baslik': '📞 Контакты',
        'iletisim_form_baslik': 'Напишите нам',
        'iletisim_form_isim': 'Ваше имя',
        'iletisim_form_email': 'Ваш E-mail',
        'iletisim_form_mesaj': 'Ваше сообщение',
        'iletisim_form_gonder': '📤 Отправить',
        'iletisim_adres_baslik': '📍 Наши адреса',
        'iletisim_whatsapp': 'Написать в WhatsApp',
        'mesaj_basarili': '✅ Ваше сообщение отправлено! Мы ответим вам в ближайшее время.',
        'mesajlar_baslik': 'Входящие сообщения',
        'mesajlar_isim': 'Имя',
        'mesajlar_email': 'E-mail',
        'mesajlar_mesaj': 'Сообщение',
        'mesajlar_tarih': 'Дата',
        'mesajlar_yok': 'Сообщений пока нет.',
    },
    'tk': {
        'lang_attr': 'tk',
        'menu_anasayfa': 'Baş sahypa',
        'menu_hakkimizda': 'Biz hakda',
        'menu_hizmetler': 'Hyzmatlar',
        'menu_iletisim': 'Habarlaşmak',
        'footer_telif': '© 2026 Trust Consulting. Ähli hukuklar goralýar.',
        'footer_iletisim': 'Habarlaşmak',
        'index_baslik': '✈️ Wiza & Syýahat Maslahat Hyzmaty',
        'index_alt_baslik': 'Türkmenistandan dünýä açylýan derwezäňiz.',
        'index_ulkeler_baslik': '🌍 Hyzmat berýän ýurtlarymyz',
        'index_hizmet_baslik': '⚡ Çalt hyzmatlar',
        'index_cta': 'Mugt maslahat al',
        'hakkimizda_baslik': 'Biz hakda',
        'hakkimizda_metin': 'Trust Consulting hökmünde, Türkmenistandan dünýäniň dört künjüne wiza we syýahat maslahat hyzmatlaryny hödürleýäris. Türkmenistan we Stambul ofislerimiz bilen müşderilerimize iň çalt we ygtybarly wiza çözgütlerini hödürleýäris.',
        'hakkimizda_misyon': 'Biziň wezipämiz',
        'hakkimizda_misyon_metin': 'Türkmenistandaky adamlara islän ýurduna howpsuz, çalt we elýeterli bahadan wiza almagyna kömek etmek.',
        'hakkimizda_ofis1': '🇹🇲 Türkmenistan ofisi',
        'hakkimizda_ofis2': '🇹🇷 Stambul ofisi',
        'hizmetler_baslik': '✈️ Hyzmatlarymyz',
        'hizmetler_turkiye_baslik': '🇹🇷 Türkiýe wiza görnüşleri',
        'hizmetler_diger_baslik': '🌍 Beýleki ýurtlar',
        'hizmetler_ek_baslik': '➕ Goşmaça hyzmatlar',
        'hizmetler_egitim_baslik': '🎓 Türkiýede okuw',
        'iletisim_baslik': '📞 Habarlaşmak',
        'iletisim_form_baslik': 'Bize ýazyň',
        'iletisim_form_isim': 'Adyňyz',
        'iletisim_form_email': 'E-poçtaňyz',
        'iletisim_form_mesaj': 'Habaraňyz',
        'iletisim_form_gonder': '📤 Ibermek',
        'iletisim_adres_baslik': '📍 Salgymyz',
        'iletisim_whatsapp': 'WhatsApp-dan ýaz',
        'mesaj_basarili': '✅ Habaraňyz iberildi! Iň gysga wagtda jogap bereris.',
        'mesajlar_baslik': 'Gelen habarlar',
        'mesajlar_isim': 'At',
        'mesajlar_email': 'E-poçta',
        'mesajlar_mesaj': 'Habar',
        'mesajlar_tarih': 'Senesi',
        'mesajlar_yok': 'Heniz habar ýok.',
    },
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
    dil = session.get('dil', 'tr')
    if dil not in diller:
        dil = 'tr'
    return dict(dil_kodu=dil, diller=diller, t=diller[dil])

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
        dil = session.get('dil', 'tr')
        db = get_db()
        if db:
            try:
                db.execute(
                    'INSERT INTO mesajlar (isim, email, mesaj, tarih) VALUES (?, ?, ?, ?)',
                    (isim, email, mesaj, tarih)
                )
                db.commit()
                mail_gonder(isim, email, mesaj, tarih)
                flash(diller[dil]['mesaj_basarili'], 'success')
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
        msgs = db.execute('SELECT * FROM mesajlar ORDER BY id DESC').fetchall()
        db.close()
        return render_template('mesajlar.html', mesajlar=msgs)
    else:
        return "Veritabanı hatası", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)