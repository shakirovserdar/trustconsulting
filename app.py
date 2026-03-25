from dotenv import load_dotenv
load_dotenv()
import anthropic
import os
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import sqlite3
import urllib.request
import urllib.error
import json

RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
BILDIRIM_EMAIL = 'shakirovserdar7@gmail.com'

def mail_gonder(isim, telefon, ulke, vize_ulke, mesaj, tarih):
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY ayarlanmamis, mail gonderilmedi.")
        return False
    try:
        html_icerik = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f0f7ff;padding:20px;">
        <div style="max-width:520px;margin:auto;background:white;border-radius:12px;
                    padding:24px;border-top:4px solid #2271b1;">
            <h2 style="color:#2271b1;">Yeni Site Mesaji - Trust Consulting</h2>
            <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:8px;color:#666;"><strong>Isim:</strong></td><td>{isim}</td></tr>
                <tr><td style="padding:8px;color:#666;"><strong>Telefon:</strong></td><td>{telefon}</td></tr>
                <tr><td style="padding:8px;color:#666;"><strong>Nereli:</strong></td><td>{ulke}</td></tr>
                <tr><td style="padding:8px;color:#666;"><strong>Vize:</strong></td><td>{vize_ulke}</td></tr>
                <tr><td style="padding:8px;color:#666;"><strong>Tarih:</strong></td><td>{tarih}</td></tr>
                <tr><td style="padding:8px;color:#666;"><strong>Mesaj:</strong></td><td>{mesaj if mesaj else '-'}</td></tr>
            </table>
        </div></body></html>
        """
        veri = {
            "from": "Trust Consulting <noreply@trustedutm.com>",
            "to": [BILDIRIM_EMAIL],
            "subject": f"Yeni Mesaj: {isim} ({vize_ulke}) - Trust Consulting",
            "html": html_icerik
        }
        istek = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(veri).encode("utf-8"),
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(istek, timeout=10) as yanit:
            sonuc = json.loads(yanit.read().decode())
            logging.info(f"Resend mail gonderildi: {sonuc}")
            return True
    except Exception as e:
        logging.error(f"Resend hatasi: {e}")
        return False

app = Flask(__name__)
app.secret_key = 'trustconsulting_gizli_anahtar'

# ══ CHATBOT ══
CHATBOT_SYSTEM_PROMPT = """Sen Trust Consulting sirketinin sanal danismanisın.
Trust Consulting, Turkmenistan merkezli bir vize ve egitim danismanlik sirketidir.

HAKKINDA BILGI:
- 500den fazla basarili basvuru, %92 onay orani
- 8 fiziksel ofis: 7 Turkmenistanda + 1 Istanbul (Fatih/Aksaray)
- 3 dilde hizmet: Turkce, Rusca, Turkmence
- 20den fazla ulkeye vize

TURKIYE VIZE TURLERI:
- Ogrenci Vizesi (universite kabulu dahil)
- Turkce Ogrenim Vizesi (TOMER)
- Calisma Vizesi
- Turist Vizesi (30 gunluk)
- Turist Ikamet (90 gunluk)
- Aile Birlesimleri
- Saglik Vizesi

DIGER ULKELER:
- Rusya: E-viza $80, Turist 30gun $330, 90gun $380, Is 1yil $480, Is 3yil $520
- Ozbekistan: 10gun 1600TMT, 20gun 1900TMT, 30gun 2200TMT, 90gun $260
- Azerbaycan: 30gun E-viza $60, VIP $100
- Kazakistan: 30gun E-viza $250
- Dubai/BAE: 30gun $180, 60gun $280, Is vizesi $3000
- Almanya, Belcika, Romanya turist ve ogrenci vizeleri

EGITIM HIZMETLERI:
- Turk universitelerine kabul (depozitsiz)
- Istanbul universiteleri (depozitli)
- Lisans/Onlisans: $1200-1600 (Tem-Kas arasi)
- Yuksek Lisans: $1750-2500 (Oca-Mar arasi)

CALISMA VIZESI UCRETLERI (baslangic $500 + onay sonrasi):
- Antalya otel/garson/resepsiyon: $500+$1000
- Antalya mobilya fabrikasi: $500+$1000
- Mersin insaat/kaynakci: $500+$1000
- Istanbul tekstil: $500+$1300
- Istanbul ev hizmetleri: $500+$1300

OFIS HIZMETLERI (TMT):
- Mosaic randevu: 100 TMT
- Tercume TKM-TR: 15-30 TMT
- Tercume TKM-ING-RU: 20-40 TMT
- Otel rezervasyonu: 200 TMT
- Sponsor: 800 TMT

ILETISIM:
- Turkmenistan: +993 64 48 89 20 / +993 61 95 09 20
- Istanbul: +90 552 425 46 97 (WhatsApp)
- E-posta: info@trustedutm.com
- Instagram: @trusttmconsulting

KURALLAR:
- Kisa ve net cevap ver (3-5 cumle maksimum)
- Turkce, Rusca veya Turkmence - kullanici hangi dilde yazarsa o dilde cevap ver
- Bilmedigin sorular icin: "Bu konuda WhatsApp'tan yazmanizi oneririm: +90 552 425 46 97"
- Asla baska vize sirketi onerme
- Fiyatlari net soyle"""

@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        data = request.get_json()
        mesajlar = data.get('mesajlar', [])
        if len(mesajlar) > 20:
            mesajlar = mesajlar[-20:]
        if not mesajlar or not mesajlar[-1].get('content', '').strip():
            return jsonify({'cevap': 'Lutfen sorunuzu yazin.'})
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        yanit = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=400,
            system=CHATBOT_SYSTEM_PROMPT,
            messages=mesajlar
        )
        cevap = yanit.content[0].text
        return jsonify({'cevap': cevap})
    except anthropic.AuthenticationError:
        return jsonify({'cevap': 'API anahtari hatasi. Lutfen yoneticiye bildirin.'})
    except Exception as e:
        app.logger.error(f'Chatbot hatasi: {e}')
        return jsonify({'cevap': 'Bir hata olustu. WhatsApp: +90 552 425 46 97'})
# ══ CHATBOT SONU ══

diller = {
    'tr': {
        'lang_attr': 'tr',
        'menu_anasayfa': 'Ana Sayfa',
        'menu_hakkimizda': 'Hakkimizda',
        'menu_hizmetler': 'Hizmetler',
        'menu_iletisim': 'Iletisim',
        'footer_telif': '© 2026 Trust Consulting. Tum haklari saklidir.',
        'footer_iletisim': 'Iletisim',
        'index_baslik': '✈️ Vize & Seyahat Danismanligi',
        'index_alt_baslik': "Turkmenistan'dan dunyaya acilan kapiiniz.",
        'index_ulkeler_baslik': '🌍 Hizmet Verdigimiz Ulkeler',
        'index_hizmet_baslik': '⚡ Hizli Hizmetler',
        'index_cta': 'Ucretsiz Danismanlik Al',
        'index_yorumlar_baslik': '⭐ Musteri Yorumlari',
        'index_sss_baslik': '❓ Sik Sorulan Sorular',
        'index_cta2_baslik': '🚀 Vize Sureci Baslatin',
        'index_cta2_alt': 'Ucretsiz on degerlendirme icin hemen iletisime gecin.',
        'index_cta2_btn': '📞 Ucretsiz On Gorusme Al',
        'hakkimizda_baslik': 'Hakkimizda',
        'hakkimizda_metin': "Trust Consulting olarak, Turkmenistan'dan dunyanin dort bir yanina vize ve seyahat danismanligi hizmetleri sunuyoruz.",
        'hakkimizda_misyon': 'Misyonumuz',
        'hakkimizda_misyon_metin': "Turkmenistan'daki insanlara istedikleri ulkeye guvenli, hizli ve uygun fiyatli vize almasinda yardimci olmak.",
        'hakkimizda_ofis1': '🇹🇲 Turkmenistan Ofisi',
        'hakkimizda_ofis2': '🇹🇷 Istanbul Ofisi',
        'hizmetler_baslik': '✈️ Hizmetlerimiz',
        'hizmetler_turkiye_baslik': '🇹🇷 Turkiye Vize Turleri',
        'hizmetler_diger_baslik': '🌍 Diger Ulkeler',
        'hizmetler_ek_baslik': '➕ Ek Hizmetler',
        'hizmetler_egitim_baslik': "🎓 Turkiye'de Egitim",
        'iletisim_baslik': '📞 Iletisim',
        'iletisim_form_baslik': 'Bize Yazin',
        'iletisim_form_isim': 'Ad Soyadiniz',
        'iletisim_form_telefon': 'Telefon / WhatsApp Numaraniz',
        'iletisim_form_ulke': 'Nereden? (Sehir / Ulke)',
        'iletisim_form_vize_ulke': 'Hangi Ulkeye Vize Istiyorsunuz?',
        'iletisim_form_mesaj': 'Eklemek Istedikleriniz (Istege Bagli)',
        'iletisim_form_gonder': '📤 Gonder',
        'iletisim_adres_baslik': '📍 Adreslerimiz',
        'iletisim_whatsapp': "WhatsApp'tan Yaz",
        'mesaj_basarili': '✅ Mesajiniz alindi! En kisa surede sizi arayacagiz.',
        'mesajlar_baslik': 'Gelen Mesajlar',
        'mesajlar_isim': 'Isim',
        'mesajlar_telefon': 'Telefon',
        'mesajlar_ulke': 'Nereli',
        'mesajlar_vize': 'Hangi Vize',
        'mesajlar_mesaj': 'Mesaj',
        'mesajlar_tarih': 'Tarih',
        'mesajlar_yok': 'Henuz mesaj yok.',
    },
    'ru': {
        'lang_attr': 'ru',
        'menu_anasayfa': 'Glavnaya',
        'menu_hakkimizda': 'O nas',
        'menu_hizmetler': 'Uslugi',
        'menu_iletisim': 'Kontakty',
        'footer_telif': '© 2026 Trust Consulting. Vse prava zashchishcheny.',
        'footer_iletisim': 'Kontakty',
        'index_baslik': '✈️ Vizovye & Turisticheskie Uslugi',
        'index_alt_baslik': 'Vashi vorota iz Turkmenistana v mir.',
        'index_ulkeler_baslik': '🌍 Strany, s kotorymi my rabotaem',
        'index_hizmet_baslik': '⚡ Bystye uslugi',
        'index_cta': 'Poluchit besplatnuyu konsultaciyu',
        'index_yorumlar_baslik': '⭐ Otzyvy klientov',
        'index_sss_baslik': '❓ Chasto zadavaemye voprosy',
        'index_cta2_baslik': '🚀 Nachite vizovyy process',
        'index_cta2_alt': 'Svjazhites s nami dlya besplatnoy ocenki.',
        'index_cta2_btn': '📞 Poluchit besplatnuyu konsultaciyu',
        'hakkimizda_baslik': 'O nas',
        'hakkimizda_metin': 'Trust Consulting predostavlyaet vizovye uslugi iz Turkmenistana po vsemu miru.',
        'hakkimizda_misyon': 'Nasha missiya',
        'hakkimizda_misyon_metin': 'Pomoch lyudyam v Turkmenistane bystro i dostupno poluchit vizu v lyubuyu stranu.',
        'hakkimizda_ofis1': '🇹🇲 Ofis v Turkmenistane',
        'hakkimizda_ofis2': '🇹🇷 Ofis v Stambule',
        'hizmetler_baslik': '✈️ Nashi uslugi',
        'hizmetler_turkiye_baslik': '🇹🇷 Tipy viz v Turciyu',
        'hizmetler_diger_baslik': '🌍 Drugie strany',
        'hizmetler_ek_baslik': '➕ Dopolnitelnye uslugi',
        'hizmetler_egitim_baslik': '🎓 Obrazovanie v Turcii',
        'iletisim_baslik': '📞 Kontakty',
        'iletisim_form_baslik': 'Napishite nam',
        'iletisim_form_isim': 'Vashe imya i familiya',
        'iletisim_form_telefon': 'Telefon / WhatsApp',
        'iletisim_form_ulke': 'Otkuda vy?',
        'iletisim_form_vize_ulke': 'V kakuyu stranu nuzhna viza?',
        'iletisim_form_mesaj': 'Dopolnitelnaya informaciya',
        'iletisim_form_gonder': '📤 Otpravit',
        'iletisim_adres_baslik': '📍 Nashi adresa',
        'iletisim_whatsapp': 'Napisat v WhatsApp',
        'mesaj_basarili': '✅ Vashe soobshchenie prinyato!',
        'mesajlar_baslik': 'Vkhodyashchie soobshcheniya',
        'mesajlar_isim': 'Imya',
        'mesajlar_telefon': 'Telefon',
        'mesajlar_ulke': 'Otkuda',
        'mesajlar_vize': 'Kakaya viza',
        'mesajlar_mesaj': 'Soobshchenie',
        'mesajlar_tarih': 'Data',
        'mesajlar_yok': 'Soobshcheniy poka net.',
    },
    'tk': {
        'lang_attr': 'tk',
        'menu_anasayfa': 'Bas sahypa',
        'menu_hakkimizda': 'Biz hakda',
        'menu_hizmetler': 'Hyzmatlar',
        'menu_iletisim': 'Habarlasmak',
        'footer_telif': '© 2026 Trust Consulting. Ahli hukuklar goralyar.',
        'footer_iletisim': 'Habarlasmak',
        'index_baslik': '✈️ Wiza & Syyyahat Maslahat Hyzmaty',
        'index_alt_baslik': 'Turkmenistandan dunya acylyan derwezaniz.',
        'index_ulkeler_baslik': '🌍 Hyzmat beryan yurtlarymyz',
        'index_hizmet_baslik': '⚡ Calt hyzmatlar',
        'index_cta': 'Mugt maslahat al',
        'index_yorumlar_baslik': '⭐ Musderi teswirler',
        'index_sss_baslik': '❓ Kop soralyan soraglar',
        'index_cta2_baslik': '🚀 Wiza prosesini baslatyng',
        'index_cta2_alt': 'Mugt baha beriş ucin biz bilen habarlasynng.',
        'index_cta2_btn': '📞 Mugt maslahat al',
        'hakkimizda_baslik': 'Biz hakda',
        'hakkimizda_metin': 'Trust Consulting hkmunde, Turkmenistandan dunyanin dort kunjune wiza hyzmatlaryny hödürleyaris.',
        'hakkimizda_misyon': 'Bizin wezipamiz',
        'hakkimizda_misyon_metin': 'Turkmenistanky adamlara islan yurduna howpsuz, calt we elyaterli bahadan wiza almagyna komek etmek.',
        'hakkimizda_ofis1': '🇹🇲 Turkmenistan ofisi',
        'hakkimizda_ofis2': '🇹🇷 Stambul ofisi',
        'hizmetler_baslik': '✈️ Hyzmatlarymyz',
        'hizmetler_turkiye_baslik': '🇹🇷 Turkiye wiza gornusleri',
        'hizmetler_diger_baslik': '🌍 Beyleki yurtlar',
        'hizmetler_ek_baslik': '➕ Gosmaca hyzmatlar',
        'hizmetler_egitim_baslik': '🎓 Turkiyede okuw',
        'iletisim_baslik': '📞 Habarlasmak',
        'iletisim_form_baslik': 'Bize yazyn',
        'iletisim_form_isim': 'Adynyz we familyanyz',
        'iletisim_form_telefon': 'Telefon / WhatsApp belginiz',
        'iletisim_form_ulke': 'Nireden?',
        'iletisim_form_vize_ulke': 'Haysy yurda wiza gerek?',
        'iletisim_form_mesaj': 'Gosmaca maglumat',
        'iletisim_form_gonder': '📤 Ibermek',
        'iletisim_adres_baslik': '📍 Salgymyz',
        'iletisim_whatsapp': "WhatsApp-dan yaz",
        'mesaj_basarili': '✅ Habaranyz alyndy!',
        'mesajlar_baslik': 'Gelen habarlar',
        'mesajlar_isim': 'At',
        'mesajlar_telefon': 'Telefon',
        'mesajlar_ulke': 'Nireli',
        'mesajlar_vize': 'Haysy wiza',
        'mesajlar_mesaj': 'Habar',
        'mesajlar_tarih': 'Senesi',
        'mesajlar_yok': 'Heniz habar yok.',
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
        conn = sqlite3.connect('/tmp/site.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"Veritabani baglanti hatasi: {e}")
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
            for col in ['telefon TEXT', 'ulke TEXT', 'vize_ulke TEXT']:
                try:
                    db.execute(f'ALTER TABLE mesajlar ADD COLUMN {col}')
                except:
                    pass
            db.commit()
            db.execute('''
                CREATE TABLE IF NOT EXISTS yorumlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    isim TEXT NOT NULL,
                    sehir TEXT,
                    yildiz INTEGER DEFAULT 5,
                    metin TEXT NOT NULL,
                    onaylandi INTEGER DEFAULT 0,
                    tarih TEXT NOT NULL
                )
            ''')
            db.commit()
            logging.info("Veritabani hazir.")
        except Exception as e:
            logging.error(f"Tablo olusturma hatasi: {e}")
        finally:
            db.close()

try:
    init_db()
except:
    pass

@app.route('/')
def index():
    yorumlar = []
    try:
        db = get_db()
        if db:
            try:
                yorumlar = db.execute('SELECT * FROM yorumlar WHERE onaylandi=1 ORDER BY id DESC').fetchall()
            except:
                pass
            finally:
                db.close()
    except:
        pass
    return render_template('index.html', baslik='Ana Sayfa', onaylanan_yorumlar=yorumlar)

@app.route('/hakkimizda')
def hakkimizda():
    return render_template('hakkimizda.html', baslik='Hakkimizda')

@app.route('/sss')
def sss():
    return render_template('sss.html', baslik='SSS')

@app.route('/yorumlar')
def yorumlar_sayfa():
    yorumlar = []
    try:
        db = get_db()
        if db:
            try:
                yorumlar = db.execute('SELECT * FROM yorumlar WHERE onaylandi=1 ORDER BY id DESC').fetchall()
            except:
                pass
            finally:
                db.close()
    except:
        pass
    return render_template('yorumlar.html', baslik='Yorumlar', onaylanan_yorumlar=yorumlar)

@app.route('/universiteler')
def universiteler():
    return render_template('universiteler.html', baslik='Universiteler')

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
                logging.error(f"Mesaj kayit hatasi: {e}")
                flash("Bir hata olustu.", 'error')
            finally:
                db.close()
        else:
            flash("Veritabani baglanti hatasi.", 'error')
        return redirect(url_for('iletisim'))
    return render_template('iletisim.html', baslik='Iletisim')

@app.route('/kayit-gonder', methods=['POST'])
def kayit_gonder():
    ad_soyad   = request.form.get('ad_soyad', '').strip()
    nereden    = request.form.get('nereden', '').strip()
    telefon    = request.form.get('telefon', '').strip()
    email      = request.form.get('email', '').strip()
    yas        = request.form.get('yas', '').strip()
    universite = request.form.get('universite', '').strip()
    not_       = request.form.get('not', '').strip()
    tarih      = datetime.now().strftime('%d.%m.%Y %H:%M')
    dil        = session.get('dil', 'tr')

    if RESEND_API_KEY and ad_soyad:
        try:
            html_k = (
                "<html><body style=\"font-family:Arial;background:#f0f7ff;padding:20px;\">"
                "<div style=\"max-width:500px;margin:auto;background:white;border-radius:12px;padding:24px;border-top:4px solid #f59e0b;\">"
                "<h2 style=\"color:#f59e0b;\">Yeni Kayit Formu - Trust Consulting</h2>"
                "<table style=\"width:100%;border-collapse:collapse;\">"
                f"<tr><td style=\"padding:8px;color:#666;\"><strong>Ad Soyad:</strong></td><td>{ad_soyad}</td></tr>"
                f"<tr><td style=\"padding:8px;color:#666;\"><strong>Nereden:</strong></td><td>{nereden}</td></tr>"
                f"<tr><td style=\"padding:8px;color:#666;\"><strong>Telefon:</strong></td><td>{telefon}</td></tr>"
                f"<tr><td style=\"padding:8px;color:#666;\"><strong>E-mail:</strong></td><td>{email or '-'}</td></tr>"
                f"<tr><td style=\"padding:8px;color:#666;\"><strong>Yas:</strong></td><td>{yas or '-'}</td></tr>"
                f"<tr><td style=\"padding:8px;color:#666;\"><strong>Universite/Ulke:</strong></td><td>{universite or '-'}</td></tr>"
                f"<tr><td style=\"padding:8px;color:#666;\"><strong>Not:</strong></td><td>{not_ or '-'}</td></tr>"
                f"<tr><td style=\"padding:8px;color:#666;\"><strong>Tarih:</strong></td><td>{tarih}</td></tr>"
                "</table></div></body></html>"
            )
            import urllib.request as ur, json as js
            veri = {
                "from": "Trust Consulting <noreply@trustedutm.com>",
                "to": [BILDIRIM_EMAIL],
                "subject": f"Yeni Kayit: {ad_soyad}",
                "html": html_k
            }
            req = ur.Request(
                "https://api.resend.com/emails",
                data=js.dumps(veri).encode("utf-8"),
                headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                method="POST"
            )
            with ur.urlopen(req, timeout=10): pass
        except Exception as e:
            logging.error(f"Kayit mail hatasi: {e}")

    db = get_db()
    if db and ad_soyad:
        try:
            db.execute("""CREATE TABLE IF NOT EXISTS kayitlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_soyad TEXT, nereden TEXT, telefon TEXT, email TEXT,
                yas TEXT, universite TEXT, not_ TEXT, tarih TEXT)""")
            db.execute("INSERT INTO kayitlar VALUES (NULL,?,?,?,?,?,?,?,?)",
                (ad_soyad, nereden, telefon, email, yas, universite, not_, tarih))
            db.commit()
        except Exception as e:
            logging.error(f"Kayit DB hatasi: {e}")
        finally:
            db.close()

    mesajlar_k = {'tr': 'Kayit formunuz alindi! En kisa surede sizi arayacagiz.',
                  'ru': 'Vasha forma poluchena! Svjazemsja s vami.',
                  'tk': 'Hasaba alys formynyz alyndy! Janlarys.'}
    flash(mesajlar_k.get(dil, mesajlar_k['tr']), 'success')
    return redirect(url_for('index'))

@app.route('/yorum-gonder', methods=['POST'])
def yorum_gonder():
    isim   = request.form.get('isim', '').strip()
    sehir  = request.form.get('sehir', '').strip()
    yildiz = int(request.form.get('yildiz', 5))
    metin  = request.form.get('metin', '').strip()
    tarih  = datetime.now().strftime('%d.%m.%Y %H:%M')
    dil    = session.get('dil', 'tr')
    if isim and metin:
        db = get_db()
        if db:
            try:
                db.execute(
                    'INSERT INTO yorumlar (isim, sehir, yildiz, metin, tarih) VALUES (?, ?, ?, ?, ?)',
                    (isim, sehir, yildiz, metin, tarih)
                )
                db.commit()
            except Exception as e:
                logging.error(f"Yorum kayit hatasi: {e}")
            finally:
                db.close()
    mesaj = {'tr': '✅ Yorumunuz alindi, incelendikten sonra yayinlanacak!',
             'ru': '✅ Otzyv polchen, budet opublikovan posle proverki!',
             'tk': '✅ Teswirlniz alyndy, barlanandan son cap ediler!'}
    flash(mesaj.get(dil, mesaj['tr']), 'success')
    return redirect(url_for('index'))

ADMIN_USER = os.environ.get('ADMIN_USER', 'trust_admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'Trust@2026!')

def admin_giris_gerekli(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_giris'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    hata = None
    if request.method == 'POST':
        kullanici = request.form.get('kullanici', '')
        sifre     = request.form.get('sifre', '')
        if kullanici == ADMIN_USER and sifre == ADMIN_PASS:
            session['admin_giris'] = True
            return redirect(url_for('admin_panel'))
        else:
            hata = 'Kullanici adi veya sifre hatali!'
    return render_template('admin_login.html', hata=hata)

@app.route('/admin/cikis')
def admin_cikis():
    session.pop('admin_giris', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_giris_gerekli
def admin_panel():
    mesajlar = []
    bekleyen = []
    onaylanan = []
    try:
        db = get_db()
        if db:
            try:
                db.execute('''CREATE TABLE IF NOT EXISTS mesajlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT NOT NULL,
                    telefon TEXT, email TEXT, ulke TEXT, vize_ulke TEXT, mesaj TEXT, tarih TEXT NOT NULL)''')
                db.execute('''CREATE TABLE IF NOT EXISTS yorumlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT NOT NULL, sehir TEXT,
                    yildiz INTEGER DEFAULT 5, metin TEXT NOT NULL, onaylandi INTEGER DEFAULT 0, tarih TEXT NOT NULL)''')
                db.commit()
                mesajlar  = db.execute('SELECT * FROM mesajlar ORDER BY id DESC').fetchall()
                bekleyen  = db.execute('SELECT * FROM yorumlar WHERE onaylandi=0 ORDER BY id DESC').fetchall()
                onaylanan = db.execute('SELECT * FROM yorumlar WHERE onaylandi=1 ORDER BY id DESC').fetchall()
            except Exception as e:
                logging.error(f"Admin panel DB hatasi: {e}")
            finally:
                db.close()
    except Exception as e:
        logging.error(f"Admin panel hatasi: {e}")
    return render_template('admin_panel.html',
                           mesajlar=mesajlar,
                           bekleyen=bekleyen,
                           onaylanan=onaylanan)

@app.route('/admin/yorum-onayla/<int:yid>')
@admin_giris_gerekli
def admin_yorum_onayla(yid):
    try:
        db = get_db()
        if db:
            db.execute('UPDATE yorumlar SET onaylandi=1 WHERE id=?', (yid,))
            db.commit()
            db.close()
    except:
        pass
    return redirect(url_for('admin_panel') + '#yorumlar')

@app.route('/admin/yorum-sil/<int:yid>')
@admin_giris_gerekli
def admin_yorum_sil(yid):
    try:
        db = get_db()
        if db:
            db.execute('DELETE FROM yorumlar WHERE id=?', (yid,))
            db.commit()
            db.close()
    except:
        pass
    return redirect(url_for('admin_panel') + '#yorumlar')

@app.route('/admin/mesaj-sil/<int:mid>')
@admin_giris_gerekli
def admin_mesaj_sil(mid):
    try:
        db = get_db()
        if db:
            db.execute('DELETE FROM mesajlar WHERE id=?', (mid,))
            db.commit()
            db.close()
    except:
        pass
    return redirect(url_for('admin_panel') + '#mesajlar')


@app.route('/OneSignalSDKWorker.js')
def onesignal_worker():
    return app.send_static_file('OneSignalSDKWorker.js')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)