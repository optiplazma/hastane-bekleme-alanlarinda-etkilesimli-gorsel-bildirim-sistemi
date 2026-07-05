# Hastane Dijital Bilgilendirme ve Sıra Yönetim Sistemi

Raspberry Pi üzerinde çalışan, hastaneler için geliştirilmiş dijital tabela (kiosk) ve
poliklinik sıra yönetim sistemi. Bitirme projesi olarak geliştirilmiştir.

Sistem; her doktor/poliklinik için ayrı hasta sırası tutar, bekleme ekranında
yemekhane menüsü, hastane duyuruları, otobüs saatleri, döviz/altın kurları ve hava
durumu gibi bilgileri döngüsel olarak gösterir. Doktorlar kendi yönetim panelleri
üzerinden hasta ekleyip çağırabilir ve ekran içeriklerini güncelleyebilir.

## Özellikler

- Doktor bazlı ayrı hasta sırası ve çağırma kuyruğu
- Bekleme ekranı için döngüsel bilgi tabelası (yemekhane, duyuru, otobüs saatleri)
- Kullanıcı adı/şifre ile güvenli giriş (bcrypt ile şifre saklama)
- Her doktora özel ayarlar (poliklinik adı, doktor adı vb.) ve ortak ayarlar
- Pi ekranlarının beslenmesi için REST API uç noktaları
- Raspberry Pi'de tam ekran (kiosk) modunda otomatik başlatma script'i

## Kullanılan Teknolojiler

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-CORS
- **Veritabanı:** SQLite
- **Frontend:** HTML, CSS, JavaScript (Jinja2 şablonları)
- **Donanım/Dağıtım:** Raspberry Pi, Chromium kiosk modu

## Kurulum

1. Depoyu bilgisayarınıza indirin.

2. Sanal ortam oluşturup etkinleştirin:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux / macOS:
   source venv/bin/activate
   ```

3. Gerekli kütüphaneleri kurun:
   ```bash
   pip install -r requirements.txt
   ```

4. Uygulamayı başlatın:
   ```bash
   python app.py
   ```

5. Tarayıcıdan aşağıdaki adresleri açın:
   - Bekleme ekranı (Doktor 1): `http://localhost:5000/`
   - Bekleme ekranı (Doktor 2): `http://localhost:5000/screen/2`
   - Yönetim paneli girişi: `http://localhost:5000/login`

## Varsayılan Giriş Bilgileri

Uygulama ilk çalıştığında örnek veriler ve iki test kullanıcısı (`admin`, `admin2`)
otomatik oluşturulur. Kullanıcıların şifreleri ortam değişkenlerinden okunur; ortam
değişkeni tanımlı değilse geçici demo değerleri kullanılır. Gerçek kullanımda mutlaka
kendi güçlü şifrelerinizi tanımlayın.

## Güvenlik ve Ortam Değişkenleri

Gizli bilgiler kodun içine gömülü değildir; aşağıdaki ortam değişkenlerinden okunur.
Gerçek dağıtımda bunları kendi değerlerinizle ayarlayın:

| Ortam Değişkeni   | Açıklama                          |
|-------------------|-----------------------------------|
| `SECRET_KEY`      | Flask oturum güvenlik anahtarı     |
| `ADMIN_PASSWORD`  | Doktor 1 (admin) giriş şifresi     |
| `ADMIN2_PASSWORD` | Doktor 2 (admin2) giriş şifresi    |

Örnek (Linux / macOS):

```bash
export SECRET_KEY="rastgele-uzun-bir-deger"
export ADMIN_PASSWORD="guclu-bir-sifre"
export ADMIN2_PASSWORD="baska-guclu-bir-sifre"
python app.py
```

Örnek (Windows):

```bash
set SECRET_KEY=rastgele-uzun-bir-deger
set ADMIN_PASSWORD=guclu-bir-sifre
set ADMIN2_PASSWORD=baska-guclu-bir-sifre
python app.py
```

## Raspberry Pi Kiosk Modu

`kiosk.sh` script'i, Raspberry Pi açıldığında Chromium'u tam ekran kiosk modunda
başlatıp bekleme ekranını otomatik açar. Script içindeki sunucu IP adresini kendi
ağınıza göre düzenlemeniz gerekir.

## Ekran Görüntüleri

Proje ekran görüntüleri `docs/` (veya `static/`) klasöründe yer almaktadır.
