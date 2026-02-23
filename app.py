from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'trustconsulting_gizli_anahtar'

# Dil dosyaları
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
        'index_duyuru1': 'Yeni ofisimiz açıldı. Sizi İstanbul ofisimizde ağırlamaktan mutluluk duyarız.',
        'index_duyuru2': 'Online danışmanlık hizmetlerimiz başladı. Artık online randevu alarak hizmet alabilirsiniz.',
        'hakkimizda_baslik': 'Hakkımızda',
        'hakkimizda_icerik': 'Trust Consulting olarak, işletmenizin güven yönetimi ve danışmanlık ihtiyaçlarına profesyonel çözümler sunuyoruz. Ekibimiz, sektörde uzun yıllara dayanan deneyimiyle yanınızda.',
        'hizmetler_baslik': 'Hizmetlerimiz',
        'hizmet1_baslik': 'Kurumsal Danışmanlık',
        'hizmet1_aciklama': 'Şirketinizin yönetim, organizasyon ve stratejik planlama ihtiyaçları için profesyonel destek.',
        'hizmet2_baslik': 'Dijital Dönüşüm',
        'hizmet2_aciklama': 'İş süreçlerinizi dijitalleştirerek verimliliğinizi artırın.',
        'hizmet3_baslik': 'Finansal Danışmanlık',
        'hizmet3_aciklama': 'Bütçe yönetimi, nakit akışı analizi, yatırım planlaması ve risk yönetimi.',
        'hizmet4_baslik': 'Eğitim ve Gelişim',
        'hizmet4_aciklama': 'Çalışanlarınızın yetkinliklerini artıracak kurumsal eğitim programları.',
        'hero_baslik': 'Geleceğinizi birlikte inşa edelim.',
	'hero_alt': 'Eğitim danışmanlığı, üniversite kayıtları ve dil kurslarında güvenilir ortağınız.',
	'hero_buton1': 'Ücretsiz Danışmanlık',
	'hero_buton2': 'Hizmetlerimiz',
	'ozet_hizmet1_baslik': 'Üniversite Danışmanlığı',
	'ozet_hizmet1_aciklama': 'Hayalinizdeki üniversiteye yerleşmeniz için rehberlik.',
	'ozet_hizmet2_aciklama': 'Yurt dışında dil eğitimi için en iyi seçenekler.',
	'ozet_hizmet3_baslik': 'Vize ve Kayıt İşlemleri',
	'ozet_hizmet3_aciklama': 'Vize başvurusundan okul kaydına kadar tüm süreçler.',
	'duyuru_baslik': 'Duyurular',
	'duyuru1': 'Yeni ofisimiz İstanbul’da açıldı.',
	'duyuru2': 'Online danışmanlık hizmeti başlamıştır.',
	'hakkimizda_baslik': 'Hakkımızda',
	'hakkimizda_icerik': 'Trust Consulting, 2010 yılından bu yana eğitim danışmanlığı alanında hizmet vermektedir. Amacımız, öğrencilerin hayallerindeki eğitime ulaşmalarına yardımcı olmaktır. Ekibimiz, alanında uzman danışmanlardan oluşmaktadır.',
	'hizmetler_baslik': 'Hizmetlerimiz',
	'hizmet1_baslik': 'Üniversite Danışmanlığı',
	'hizmet1_aciklama': 'Lisans, yüksek lisans ve doktora programları için başvuru süreçlerinde rehberlik.',
	'hizmet2_baslik': 'Dil Kursları',
	'hizmet2_aciklama': 'İngilizce, Almanca, Fransızca ve diğer dillerde kurs imkanları.',
	'hizmet3_baslik': 'Vize Danışmanlığı',
	'hizmet3_aciklama': 'Öğrenci vizesi başvurularında profesyonel destek.',
	'hizmet4_baslik': 'Kariyer Planlama',
	'hizmet4_aciklama': 'Mezuniyet sonrası kariyer fırsatları hakkında danışmanlık.',
	'iletisim_baslik': 'İletişim',
	'iletisim_form_isim': 'İsim',
	'iletisim_form_email': 'E-posta',
	'iletisim_form_mesaj': 'Mesaj',
	'iletisim_form_gonder': 'Gönder',
	'mesaj_basarili': 'Mesajınız gönderildi!',
    },
    'ru': {
        'ana_baslik': 'Trust Consulting',
        'menu_anasayfa': 'Главная',
        'menu_hakkimizda': 'О нас',
        'menu_hizmetler': 'Услуги',
        'menu_iletisim': 'Контакты',
        'footer_telif': '© 2026 Trust Consulting. Все права защищены.',
        'index_baslik': 'Консультирование по вопросам доверительного управления',
        'index_alt_baslik': 'Выводим ваш бизнес на новый уровень.',
        'index_duyuru1': 'Наш новый офис открылся. Мы будем рады приветствовать вас в нашем офисе в Стамбуле.',
        'index_duyuru2': 'Запущены онлайн-консультационные услуги. Теперь вы можете получить услуги, записавшись на прием онлайн.',
        'hakkimizda_baslik': 'О нас',
        'hakkimizda_icerik': 'Trust Consulting - это профессиональные решения для вашего бизнеса в области доверительного управления и консалтинга. Наша команда обладает многолетним опытом в отрасли.',
        'hizmetler_baslik': 'Наши услуги',
        'hizmet1_baslik': 'Корпоративный консалтинг',
        'hizmet1_aciklama': 'Профессиональная поддержка в управлении, организации и стратегическом планировании вашей компании.',
        'hizmet2_baslik': 'Цифровая трансформация',
        'hizmet2_aciklama': 'Повысьте эффективность, оцифровав бизнес-процессы.',
        'hizmet3_baslik': 'Финансовый консалтинг',
        'hizmet3_aciklama': 'Управление бюджетом, анализ денежных потоков, инвестиционное планирование и управление рисками.',
        'hizmet4_baslik': 'Обучение и развитие',
        'hizmet4_aciklama': 'Корпоративные программы обучения для повышения квалификации ваших сотрудников.',
        'iletisim_baslik': 'Контакты',
        'iletisim_form_isim': 'Имя',
        'iletisim_form_email': 'Email',
        'iletisim_form_mesaj': 'Сообщение',
        'iletisim_form_gonder': 'Отправить',
        'mesaj_basarili': 'Ваше сообщение отправлено!',
    },
    'tk': {
        'ana_baslik': 'Trust Consulting',
        'menu_anasayfa': 'Baş sahypa',
        'menu_hakkimizda': 'Biz barada',
        'menu_hizmetler': 'Hyzmatlar',
        'menu_iletisim': 'Habarlaşmak',
        'footer_telif': '© 2026 Trust Consulting. Ähli hukuklary goralan.',
        'index_baslik': 'Ynamdar dolandyryş boýunça maslahat',
        'index_alt_baslik': 'Işiňizi täze derejä çykarýarys.',
        'index_duyuru1': 'Täze ofisimiz açyldy. Sizi Stambul ofisimizde kabul etmekden hoşal bolarys.',
        'index_duyuru2': 'Onlaýn maslahat hyzmatlarymyz başlandy. Indi onlaýn görüş beläp hyzmat alyp bilersiňiz.',
        'hakkimizda_baslik': 'Biz barada',
        'hakkimizda_icerik': 'Trust Consulting, işleriňiziň ynamdar dolandyryşy we maslahat hyzmatlary üçin professional çözgütleri hödürleýär. Toparymyz pudakda köp ýyllyk tejribä eýe.',
        'hizmetler_baslik': 'Hyzmatlarymyz',
        'hizmet1_baslik': 'Kurumsal maslahat',
        'hizmet1_aciklama': 'Şirketiňiziň dolandyryş, gurama we strategiki meýilnamalaşdyrma ihtyjaçlary üçin professional goldaw.',
        'hizmet2_baslik': 'Sanly öwrülişik',
        'hizmet2_aciklama': 'Iş prosesleriňizi sanlaşdyryp netijeliligi artdyryň.',
        'hizmet3_baslik': 'Maliýe maslahaty',
        'hizmet3_aciklama': 'Býudjet dolandyryşy, nagt akymynyň analizi, maýa goýum meýilnamalaşdyrmasy we töwekgelçilik dolandyryşy.',
        'hizmet4_baslik': 'Okuw we ösüş',
        'hizmet4_aciklama': 'Işgärleriňiziň başarnyklaryny artdyrjak korporatiw okuw programmalary.',
        'iletisim_baslik': 'Habarlaşmak',
        'iletisim_form_isim': 'Ady',
        'iletisim_form_email': 'E-poçta',
        'iletisim_form_mesaj': 'Hat',
        'iletisim_form_gonder': 'Ugrat',
        'mesaj_basarili': 'Hatyňyz ugradyldy!',
    }
}

@app.before_request
def dil_ayarla():
    if 'dil' not in session:
        session['dil'] = 'tr'  # varsayılan türkçe
    if request.args.get('dil'):
        session['dil'] = request.args.get('dil')
        return redirect(request.path)

@app.context_processor
def aktar_dil():
    return dict(dil_kodu=session.get('dil', 'tr'), diller=diller)

# Veritabanı bağlantısı
def get_db():
    conn = sqlite3.connect('site.db')
    conn.row_factory = sqlite3.Row
    return conn

# Veritabanını başlat
def init_db():
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS mesajlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isim TEXT NOT NULL,
                email TEXT NOT NULL,
                mesaj TEXT NOT NULL,
                tarih TEXT NOT NULL
            )
        ''')

# Ana sayfa
@app.route('/test')
def test():
    return "Test çalışıyor"

@app.route('/')
def index():
    return render_template('index.html', baslik='Ana Sayfa')

# Hakkımızda
@app.route('/hakkimizda')
def hakkimizda():
    return render_template('hakkimizda.html', baslik='Hakkımızda')

# Hizmetler
@app.route('/hizmetler')
def hizmetler():
    return render_template('hizmetler.html', baslik='Hizmetlerimiz')

# İletişim
@app.route('/iletisim', methods=['GET', 'POST'])
def iletisim():
    if request.method == 'POST':
        isim = request.form['isim']
        email = request.form['email']
        mesaj = request.form['mesaj']
        tarih = datetime.now().strftime('%d.%m.%Y %H:%M')
        
        with get_db() as db:
            db.execute(
                'INSERT INTO mesajlar (isim, email, mesaj, tarih) VALUES (?, ?, ?, ?)',
                (isim, email, mesaj, tarih)
            )
        flash(diller[session.get('dil', 'tr')]['mesaj_basarili'], 'success')
        return redirect(url_for('iletisim'))
    
    return render_template('iletisim.html', baslik='İletişim')

# Mesajları listeleme (admin için)
@app.route('/mesajlar')
def mesajlar():
    with get_db() as db:
        mesajlar = db.execute('SELECT * FROM mesajlar ORDER BY id DESC').fetchall()
    return render_template('mesajlar.html', mesajlar=mesajlar)

if __name__ == '__main__':
    if not os.path.exists('site.db'):
        init_db()
    app.run(debug=True)