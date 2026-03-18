import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import sqlite3
import os
import urllib.request
import urllib.error
import json

RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
BILDIRIM_EMAIL = 'info@trustedutm.com'

def mail_gonder(isim, telefon, ulke, vize_ulke, mesaj, tarih):
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY ayarlanmamis, mail gonderilmedi.")
        return False
    try:
        html_icerik = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f0f7ff;padding:20px;">
        <div style="max-width:520px;margin:auto;background:white;border-radius:12px;
                    padding:24px;border-top:4px solid #2271b1;">
            <h2 style="color:#2271b1;">&#x2709; Yeni Site Mesaji — Trust Consulting</h2>
            <table style="width:100%;border-collapse:collapse;">
                <tr>
                    <td style="padding:8px;color:#666;width:110px;"><strong>Isim:</strong></td>
                    <td style="padding:8px;">{isim}</td>
                </tr>
                <tr style="background:#f5f9fd;">
                    <td style="padding:8px;color:#666;"><strong>Telefon/WA:</strong></td>
                    <td style="padding:8px;"><a href="tel:{telefon}">{telefon}</a></td>
                </tr>
                <tr>
                    <td style="padding:8px;color:#666;"><strong>Nereli:</strong></td>
                    <td style="padding:8px;">{ulke}</td>
                </tr>
                <tr style="background:#f5f9fd;">
                    <td style="padding:8px;color:#666;"><strong>Hangi Vize:</strong></td>
                    <td style="padding:8px;">{vize_ulke}</td>
                </tr>
                <tr>
                    <td style="padding:8px;color:#666;"><strong>Tarih:</strong></td>
                    <td style="padding:8px;">{tarih}</td>
                </tr>
                <tr style="background:#f5f9fd;">
                    <td style="padding:8px;color:#666;vertical-align:top;"><strong>Mesaj:</strong></td>
                    <td style="padding:8px;">{mesaj if mesaj else '—'}</td>
                </tr>
            </table>
            <p style="margin-top:16px;font-size:12px;color:#aaa;">trustedutm.com site formu</p>
        </div></body></html>
        """
        veri = {
            "from": "Trust Consulting <noreply@trustedutm.com>",
            "to": [BILDIRIM_EMAIL],
            "subject": f"Yeni Mesaj: {isim} ({vize_ulke}) — Trust Consulting",
            "html": html_icerik
        }
        istek = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(veri).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(istek, timeout=10) as yanit:
            sonuc = json.loads(yanit.read().decode())
            logging.info(f"Resend mail gonderildi: {sonuc}")
            return True
    except urllib.error.HTTPError as e:
        hata = e.read().decode()
        logging.error(f"Resend HTTP hatasi: {e.code} — {hata}")
        return False
    except Exception as e:
        logging.error(f"Resend hatasi: {e}")
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
        'index_yorumlar_baslik': '⭐ Müşteri Yorumları',
        'index_sss_baslik': '❓ Sık Sorulan Sorular',
        'index_cta2_baslik': '🚀 Vize Sürecinizi Başlatın',
        'index_cta2_alt': 'Ücretsiz ön değerlendirme için hemen iletişime geçin.',
        'index_cta2_btn': '📞 Ücretsiz Ön Görüşme Al',
        'hakkimizda_baslik': 'Hakkımızda',
        'hakkimizda_metin': 'Trust Consulting olarak, Türkmenistan\'dan dünyanın dört bir yanına vize ve seyahat danışmanlığı hizmetleri sunuyoruz. Türkiye ve İstanbul ofislerimizle, müşterilerimize en hızlı ve güvenilir vize çözümlerini sağlıyoruz.',
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
        'iletisim_form_isim': 'Ad Soyadınız',
        'iletisim_form_telefon': 'Telefon / WhatsApp Numaranız',
        'iletisim_form_ulke': 'Nereden? (Şehir / Ülke)',
        'iletisim_form_vize_ulke': 'Hangi Ülkeye Vize İstiyorsunuz?',
        'iletisim_form_mesaj': 'Eklemek İstedikleriniz (İsteğe Bağlı)',
        'iletisim_form_gonder': '📤 Gönder',
        'iletisim_adres_baslik': '📍 Adreslerimiz',
        'iletisim_whatsapp': 'WhatsApp\'tan Yaz',
        'mesaj_basarili': '✅ Mesajınız alındı! En kısa sürede sizi arayacağız.',
        'mesajlar_baslik': 'Gelen Mesajlar',
        'mesajlar_isim': 'İsim',
        'mesajlar_telefon': 'Telefon',
        'mesajlar_ulke': 'Nereli',
        'mesajlar_vize': 'Hangi Vize',
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
        'index_yorumlar_baslik': '⭐ Отзывы клиентов',
        'index_sss_baslik': '❓ Часто задаваемые вопросы',
        'index_cta2_baslik': '🚀 Начните визовый процесс',
        'index_cta2_alt': 'Свяжитесь с нами для бесплатной предварительной оценки.',
        'index_cta2_btn': '📞 Получить бесплатную консультацию',
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
        'iletisim_form_isim': 'Ваше имя и фамилия',
        'iletisim_form_telefon': 'Телефон / WhatsApp',
        'iletisim_form_ulke': 'Откуда вы? (Город / Страна)',
        'iletisim_form_vize_ulke': 'В какую страну нужна виза?',
        'iletisim_form_mesaj': 'Дополнительная информация (необязательно)',
        'iletisim_form_gonder': '📤 Отправить',
        'iletisim_adres_baslik': '📍 Наши адреса',
        'iletisim_whatsapp': 'Написать в WhatsApp',
        'mesaj_basarili': '✅ Ваше сообщение принято! Мы свяжемся с вами в ближайшее время.',
        'mesajlar_baslik': 'Входящие сообщения',
        'mesajlar_isim': 'Имя',
        'mesajlar_telefon': 'Телефон',
        'mesajlar_ulke': 'Откуда',
        'mesajlar_vize': 'Какая виза',
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
        'index_yorumlar_baslik': '⭐ Müşderi teswirler',
        'index_sss_baslik': '❓ Köp soralýan soraglar',
        'index_cta2_baslik': '🚀 Wiza prosesiňizi başlatyň',
        'index_cta2_alt': 'Mugt baha beriş üçin biz bilen habarlaşyň.',
        'index_cta2_btn': '📞 Mugt maslahat al',
        'hakkimizda_baslik': 'Biz hakda',
        'hakkimizda_metin': 'Trust Consulting hökmünde, Türkmenistandan dünýäniň dört künjüne wiza we syýahat maslahat hyzmatlaryny hödürleýäris.',
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
        'iletisim_form_isim': 'Adyňyz we familiýaňyz',
        'iletisim_form_telefon': 'Telefon / WhatsApp belgiňiz',
        'iletisim_form_ulke': 'Nireden? (Şäher / Ýurt)',
        'iletisim_form_vize_ulke': 'Haýsy ýurda wiza gerek?',
        'iletisim_form_mesaj': 'Goşmaça maglumat (islege görä)',
        'iletisim_form_gonder': '📤 Ibermek',
        'iletisim_adres_baslik': '📍 Salgymyz',
        'iletisim_whatsapp': 'WhatsApp-dan ýaz',
        'mesaj_basarili': '✅ Habaraňyz alyndy! Iň gysga wagtda sizi jaňlarys.',
        'mesajlar_baslik': 'Gelen habarlar',
        'mesajlar_isim': 'At',
        'mesajlar_telefon': 'Telefon',
        'mesajlar_ulke': 'Nireli',
        'mesajlar_vize': 'Haýsy wiza',
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
                    telefon TEXT,
                    email TEXT,
                    ulke TEXT,
                    vize_ulke TEXT,
                    mesaj TEXT,
                    tarih TEXT NOT NULL
                )
            ''')
            # Mevcut tabloya yeni sütunlar ekle (varsa hata vermez)
            for col in ['telefon TEXT', 'ulke TEXT', 'vize_ulke TEXT']:
                try:
                    db.execute(f'ALTER TABLE mesajlar ADD COLUMN {col}')
                except:
                    pass
            db.commit()
            logging.info("Veritabanı hazır.")
        except Exception as e:
            logging.error(f"Tablo oluşturma hatası: {e}")
        finally:
            db.close()

init_db()

@app.route('/')
def index():
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
        isim      = request.form.get('isim', '').strip()
        telefon   = request.form.get('telefon', '').strip()
        ulke      = request.form.get('ulke', '').strip()
        vize_ulke = request.form.get('vize_ulke', '').strip()
        mesaj     = request.form.get('mesaj', '').strip()
        tarih     = datetime.now().strftime('%d.%m.%Y %H:%M')
        dil       = session.get('dil', 'tr')
        db = get_db()
        if db:
            try:
                db.execute(
                    'INSERT INTO mesajlar (isim, telefon, ulke, vize_ulke, mesaj, tarih) VALUES (?, ?, ?, ?, ?, ?)',
                    (isim, telefon, ulke, vize_ulke, mesaj, tarih)
                )
                db.commit()
                mail_gonder(isim, telefon, ulke, vize_ulke, mesaj, tarih)
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