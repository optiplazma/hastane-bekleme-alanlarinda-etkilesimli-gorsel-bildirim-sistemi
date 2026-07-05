from flask import Flask
from models import db, User, Patient, Screen, Setting
import json
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def init_database():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ── KULLANICILAR ──────────────────────────────────────
        admin1 = User(username='admin', full_name='Dr. Mehmet Özkan')
        admin1.set_password(os.environ.get('ADMIN_PASSWORD', 'changeme'))
        db.session.add(admin1)

        admin2 = User(username='admin2', full_name='Dr. Ayşe Kaya')
        admin2.set_password(os.environ.get('ADMIN2_PASSWORD', 'changeme2'))
        db.session.add(admin2)

        db.session.flush()  # id'leri almak için

        # ── DOKTOR 1 HASTALARI ────────────────────────────────
        for i, isim in enumerate(['Ahmet Yılmaz', 'Ayşe Demir', 'Mehmet Kaya', 'Fatma Şahin', 'Ali Öztürk'], 1):
            db.session.add(Patient(sira=i, isim=isim, doctor_id=admin1.id))

        # ── DOKTOR 2 HASTALARI ────────────────────────────────
        for i, isim in enumerate(['Zeynep Arslan', 'Hasan Çelik', 'Emine Yıldız', 'Mustafa Doğan'], 1):
            db.session.add(Patient(sira=i, isim=isim, doctor_id=admin2.id))

        # ── ORTAK EKRANLAR ────────────────────────────────────
        yemek = Screen(
            title='📅 Haftalık Yemek Menüsü',
            type='yemekhane',
            content=json.dumps([
                {'day': 'Pazartesi', 'meal': 'Mercimek Çorbası, Tavuk Sote, Pilav'},
                {'day': 'Salı',      'meal': 'Ezogelin Çorbası, Karnıyarık, Bulgur Pilavı'},
                {'day': 'Çarşamba', 'meal': 'Domates Çorbası, İzmir Köfte, Makarna'},
                {'day': 'Perşembe', 'meal': 'Yayla Çorbası, Tas Kebabı, Bulgur Pilavı'},
                {'day': 'Cuma',     'meal': 'Mercimek Çorbası, Tavuk Şinitzel, Pilav'}
            ], ensure_ascii=False),
            order=1
        )
        db.session.add(yemek)

        duyuru = Screen(
            title='📢 Önemli Duyurular',
            type='duyuru',
            content=json.dumps([
                {'title': 'Ziyaret Saatleri', 'text': 'Hasta ziyaretleri 14:00-16:00 arası yapılmaktadır.'},
                {'title': 'Randevu Sistemi',  'text': 'MHRS üzerinden randevu alabilirsiniz.'},
                {'title': 'Acil Durum',       'text': '112 Acil Sağlık Hizmetleri 7/24 hizmetinizdedir.'}
            ], ensure_ascii=False),
            order=2
        )
        db.session.add(duyuru)

        otobus = Screen(
            title='🚌 Servis Saatleri',
            type='otobus',
            content=json.dumps([
                {'time': '08:00', 'route': 'Merkez → Hastane'},
                {'time': '10:00', 'route': 'Merkez → Hastane'},
                {'time': '12:00', 'route': 'Hastane → Merkez'},
                {'time': '14:00', 'route': 'Merkez → Hastane'},
                {'time': '16:00', 'route': 'Hastane → Merkez'},
                {'time': '18:00', 'route': 'Hastane → Merkez'}
            ], ensure_ascii=False),
            order=3
        )
        db.session.add(otobus)

        # ── DOKTOR 1 AYARLARI ────────────────────────────────
        for key, value in [
            ('hospital_name',   'Şehir Devlet Hastanesi'),
            ('doctor_name',     'Prof. Dr. Mehmet Özkan'),
            ('department',      'Kardiyoloji Polikliniği'),
            ('currency_usd',    '32.45'),
            ('currency_eur',    '35.20'),
            ('currency_gold',   '2.458'),
            ('currency_silver', '15.20'),
            ('weather_temp',    '24'),
            ('weather_desc',    'Güneşli'),
        ]:
            db.session.add(Setting(key=key, value=value, doctor_id=admin1.id))

        # ── DOKTOR 2 AYARLARI ────────────────────────────────
        for key, value in [
            ('hospital_name',   'Şehir Devlet Hastanesi'),
            ('doctor_name',     'Dr. Ayşe Kaya'),
            ('department',      'Dahiliye Polikliniği'),
            ('currency_usd',    '32.45'),
            ('currency_eur',    '35.20'),
            ('currency_gold',   '2.458'),
            ('currency_silver', '15.20'),
            ('weather_temp',    '24'),
            ('weather_desc',    'Güneşli'),
        ]:
            db.session.add(Setting(key=key, value=value, doctor_id=admin2.id))

        db.session.commit()

        print("✅ Veritabanı oluşturuldu!")
        print()
        print("👤 Doktor 1  : admin   / (ADMIN_PASSWORD ortam değişkeni)")
        print("👤 Doktor 2  : admin2  / (ADMIN2_PASSWORD ortam değişkeni)")
        print()
        print("🖥️  Ekran 1  : localhost:5000/")
        print("🖥️  Ekran 2  : localhost:5000/screen/2")

if __name__ == '__main__':
    init_database()