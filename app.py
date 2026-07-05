from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import bcrypt
import json
import os

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-degistir')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ========================
# MODELLER
# ========================

class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name     = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

class Patient(db.Model):
    __tablename__ = 'queue'
    id        = db.Column(db.Integer, primary_key=True)
    sira      = db.Column(db.Integer, nullable=False)
    isim      = db.Column(db.String(100), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'sira': self.sira, 'isim': self.isim, 'doctor_id': self.doctor_id}

class Screen(db.Model):
    __tablename__ = 'screens'
    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(100), nullable=False)
    content_json = db.Column(db.Text, nullable=False)
    type         = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            'id':      self.id,
            'title':   self.title,
            'content': json.loads(self.content_json),
            'type':    self.type
        }

class Setting(db.Model):
    __tablename__ = 'settings'
    # ── DÜZELTME: key yerine id primary key ──
    id        = db.Column(db.Integer, primary_key=True)
    key       = db.Column(db.String(50), nullable=False)
    value     = db.Column(db.String(255), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # key + doctor_id birlikte unique
    __table_args__ = (
        db.UniqueConstraint('key', 'doctor_id', name='uq_setting_key_doctor'),
    )

    @staticmethod
    def get(key, doctor_id=None, default=''):
        s = Setting.query.filter_by(key=key, doctor_id=doctor_id).first()
        return s.value if s else default

    @staticmethod
    def set(key, value, doctor_id=None):
        s = Setting.query.filter_by(key=key, doctor_id=doctor_id).first()
        if s:
            s.value = value
        else:
            db.session.add(Setting(key=key, value=value, doctor_id=doctor_id))
        db.session.commit()

    @staticmethod
    def get_all_for_doctor(doctor_id):
        results = {}
        for s in Setting.query.filter(
            (Setting.doctor_id == doctor_id) | (Setting.doctor_id == None)
        ).all():
            if s.key not in results or s.doctor_id is not None:
                results[s.key] = s.value
        return results

class CallQueue(db.Model):
    __tablename__ = 'call_queue'
    id            = db.Column(db.Integer, primary_key=True)
    patient_id    = db.Column(db.Integer, nullable=False)
    patient_sira  = db.Column(db.Integer, nullable=False)
    patient_isim  = db.Column(db.String(100), nullable=False)
    doctor_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status        = db.Column(db.String(20), default='pending')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

# ========================
# LOGIN
# ========================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('Kullanıcı adı veya şifre hatalı!', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ========================
# PI3 EKRANLARI
# ========================

@app.route('/')
def index():
    return render_template('index.html', doctor_id=1)

@app.route('/screen/<int:doctor_id>')
def index_doctor(doctor_id):
    doctor = User.query.get_or_404(doctor_id)
    return render_template('index.html', doctor_id=doctor_id, doctor=doctor)

# ========================
# API (Pi3 için)
# ========================

@app.route('/api/queue', methods=['GET'])
def get_queue():
    doctor_id = request.args.get('doctor_id', 1, type=int)
    patients = Patient.query.filter_by(doctor_id=doctor_id).order_by(Patient.sira).all()
    return jsonify([p.to_dict() for p in patients])

@app.route('/api/queue', methods=['POST'])
def add_to_queue():
    data = request.json
    doctor_id = data.get('doctor_id', 1)
    last = Patient.query.filter_by(doctor_id=doctor_id).order_by(Patient.sira.desc()).first()
    sira = (last.sira + 1) if last else 1
    p = Patient(sira=sira, isim=data.get('isim', 'Bilinmeyen'), doctor_id=doctor_id)
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict()), 201

@app.route('/api/queue/<int:qid>', methods=['DELETE'])
def delete_from_queue(qid):
    p = Patient.query.get_or_404(qid)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/screens', methods=['GET'])
def get_screens():
    screens = Screen.query.order_by(Screen.id).all()
    return jsonify([s.to_dict() for s in screens])

@app.route('/api/settings', methods=['GET'])
def get_settings():
    doctor_id = request.args.get('doctor_id', type=int)
    if doctor_id:
        return jsonify(Setting.get_all_for_doctor(doctor_id))
    return jsonify({s.key: s.value for s in Setting.query.filter_by(doctor_id=None).all()})

@app.route('/api/settings', methods=['POST'])
def update_settings_api():
    doctor_id = request.args.get('doctor_id', type=int)
    for key, value in request.json.items():
        Setting.set(key, str(value), doctor_id=doctor_id)
    return jsonify({'success': True})

# ========================
# ÇAĞRI API
# ========================

@app.route('/api/call/trigger', methods=['POST'])
@login_required
def trigger_call():
    doctor_id = current_user.id

    pending = CallQueue.query.filter_by(status='pending', doctor_id=doctor_id).first()
    if pending:
        return jsonify({'error': 'Zaten bekleyen bir çağrı var!'}), 400

    patient = Patient.query.filter_by(doctor_id=doctor_id).order_by(Patient.sira).first()
    if not patient:
        return jsonify({'error': 'Sırada hasta yok!'}), 400

    call = CallQueue(
        patient_id   = patient.id,
        patient_sira = patient.sira,
        patient_isim = patient.isim,
        doctor_id    = doctor_id,
        status       = 'pending'
    )
    db.session.add(call)
    db.session.commit()

    return jsonify({
        'success': True,
        'patient': {'id': patient.id, 'sira': patient.sira, 'isim': patient.isim}
    })

@app.route('/api/call/pending', methods=['GET'])
def get_pending_call():
    doctor_id = request.args.get('doctor_id', 1, type=int)

    call = CallQueue.query.filter_by(
        status='pending', doctor_id=doctor_id
    ).order_by(CallQueue.id.desc()).first()

    if call:
        return jsonify({
            'pending':      True,
            'call_id':      call.id,
            'patient_id':   call.patient_id,
            'patient_sira': call.patient_sira,
            'patient_isim': call.patient_isim
        })

    return jsonify({'pending': False})

@app.route('/api/call/complete/<int:call_id>', methods=['POST'])
def complete_call(call_id):
    call = CallQueue.query.get_or_404(call_id)
    patient = Patient.query.get(call.patient_id)
    if patient:
        db.session.delete(patient)
    db.session.delete(call)
    db.session.commit()
    return jsonify({'success': True})

# ========================
# ADMIN PANEL
# ========================

@app.route('/admin')
@login_required
def admin_dashboard():
    doctor_id = current_user.id
    settings = Setting.get_all_for_doctor(doctor_id)
    return render_template('admin.html',
        patients = Patient.query.filter_by(doctor_id=doctor_id).order_by(Patient.sira).all(),
        screens  = Screen.query.order_by(Screen.id).all(),
        settings = settings,
        user     = current_user
    )

@app.route('/admin/patient/add', methods=['POST'])
@login_required
def add_patient():
    isim = request.form.get('isim', '').strip()
    if not isim:
        flash('İsim boş olamaz!', 'danger')
        return redirect(url_for('admin_dashboard'))
    doctor_id = current_user.id
    last = Patient.query.filter_by(doctor_id=doctor_id).order_by(Patient.sira.desc()).first()
    sira = (last.sira + 1) if last else 1
    db.session.add(Patient(sira=sira, isim=isim, doctor_id=doctor_id))
    db.session.commit()
    flash(f'✅ {isim} eklendi! (Sıra: {sira})', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/patient/delete/<int:pid>', methods=['POST'])
@login_required
def delete_patient(pid):
    p = Patient.query.get_or_404(pid)
    if p.doctor_id != current_user.id:
        flash('Bu hastayı silme yetkiniz yok!', 'danger')
        return redirect(url_for('admin_dashboard'))
    name = p.isim
    db.session.delete(p)
    db.session.commit()
    flash(f'🗑️ {name} silindi!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/screen/edit/<int:sid>', methods=['POST'])
@login_required
def edit_screen(sid):
    screen = Screen.query.get_or_404(sid)
    screen.title = request.form.get('title', screen.title)

    if screen.type == 'yemekhane':
        days  = request.form.getlist('day[]')
        meals = request.form.getlist('meal[]')
        screen.content_json = json.dumps(
            [{'day': d, 'meal': m} for d, m in zip(days, meals)],
            ensure_ascii=False
        )
    elif screen.type == 'duyuru':
        titles = request.form.getlist('ann_title[]')
        texts  = request.form.getlist('ann_text[]')
        screen.content_json = json.dumps(
            [{'title': t, 'text': x} for t, x in zip(titles, texts)],
            ensure_ascii=False
        )
    elif screen.type == 'otobus':
        times  = request.form.getlist('time[]')
        routes = request.form.getlist('route[]')
        screen.content_json = json.dumps(
            [{'time': t, 'route': r} for t, r in zip(times, routes)],
            ensure_ascii=False
        )

    db.session.commit()
    flash('✅ İçerik güncellendi!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/settings/update', methods=['POST'])
@login_required
def update_settings():
    doctor_id = current_user.id
    for key, value in request.form.items():
        Setting.set(key, value, doctor_id=doctor_id)
    flash('✅ Ayarlar güncellendi!', 'success')
    return redirect(url_for('admin_dashboard'))

# ========================
# BAŞLATMA
# ========================

def init_db():
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', full_name='Dr. Mehmet Özkan')
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'changeme'))
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin (Doktor 1) oluşturuldu!")

        if not User.query.filter_by(username='admin2').first():
            admin2 = User(username='admin2', full_name='Dr. Ayşe Kaya')
            admin2.set_password(os.environ.get('ADMIN2_PASSWORD', 'changeme2'))
            db.session.add(admin2)
            db.session.commit()
            print("✅ Admin2 (Doktor 2) oluşturuldu!")

        if Patient.query.count() == 0:
            doktor1_id = User.query.filter_by(username='admin').first().id
            doktor2_id = User.query.filter_by(username='admin2').first().id

            for sira, isim in [
                (1,"Ahmet Yılmaz"),(2,"Ayşe Demir"),(3,"Mehmet Kaya"),
                (4,"Fatma Şahin"),(5,"Ali Çelik"),(6,"Zeynep Arslan"),
                (7,"Mustafa Öztürk"),(8,"Emine Yıldız"),(9,"Hüseyin Aydın")
            ]:
                db.session.add(Patient(sira=sira, isim=isim, doctor_id=doktor1_id))

            for sira, isim in [
                (1,"Elif Kılıç"),(2,"İbrahim Doğan"),(3,"Hatice Aksoy"),
                (4,"Mustafa Yılmaz"),(5,"Ayşe Kaya"),(6,"Mehmet Demir"),
                (7,"Fatma Öztürk"),(8,"Ali Yıldız"),(9,"Zeynep Aydın")
            ]:
                db.session.add(Patient(sira=sira, isim=isim, doctor_id=doktor2_id))

            db.session.commit()

        if Screen.query.count() == 0:
            yemekhane = [
                {"day":"Pazartesi","meal":"Mercimek Çorbası, Tavuk Sote, Pilav, Ayran"},
                {"day":"Salı","meal":"Tarhana Çorbası, Köfte, Makarna, Cacık"},
                {"day":"Çarşamba","meal":"Ezogelin Çorbası, Tavuk Izgara, Bulgur Pilavı"},
                {"day":"Perşembe","meal":"Yayla Çorbası, Balık, Patates Kızartması"},
                {"day":"Cuma","meal":"Domates Çorbası, Etli Kuru Fasulye, Pilav"},
                {"day":"Cumartesi","meal":"Şehriye Çorbası, Tavuk Şinitzel, Patates Püresi"},
                {"day":"Pazar","meal":"Düğün Çorbası, Kuzu Tandır, Pilav, Ayran"}
            ]
            duyuru = [
                {"title":"Ziyaret Saatleri","text":"Hafta içi 13:00-15:00 ve 18:00-20:00 arası ziyaretçi kabul edilmektedir."},
                {"title":"Park Alanı","text":"Hastanemiz otopark alanı genişletme çalışması devam etmektedir."},
                {"title":"Randevu Sistemi","text":"Online randevu sistemi aktif edilmiştir. Web sitemizden randevu alabilirsiniz."},
                {"title":"Yeni Bölüm","text":"Fizik Tedavi ve Rehabilitasyon bölümümüz hizmete açılmıştır."},
                {"title":"Acil Servis","text":"Acil olmayan durumlar için lütfen poliklinik randevusu alınız."},
                {"title":"Laboratuvar","text":"Kan tahlili sonuçlarınızı aynı gün öğleden sonra alabilirsiniz."},
                {"title":"Eczane","text":"Hastane eczanemiz 7/24 hizmetinizdedir."}
            ]
            otobus = [
                {"time":"08:00","route":"Merkez - Hastane"},
                {"time":"09:00","route":"Merkez - Hastane"},
                {"time":"10:00","route":"Merkez - Hastane"},
                {"time":"11:00","route":"Merkez - Hastane"},
                {"time":"12:00","route":"Hastane - Merkez"},
                {"time":"13:00","route":"Merkez - Hastane"},
                {"time":"14:00","route":"Merkez - Hastane"},
                {"time":"15:00","route":"Hastane - Merkez"},
                {"time":"16:00","route":"Hastane - Merkez"},
                {"time":"17:00","route":"Merkez - Hastane"},
                {"time":"18:00","route":"Hastane - Merkez"},
                {"time":"19:00","route":"Hastane - Merkez"}
            ]
            db.session.add(Screen(id=1, title="Yemekhane Planı",
                content_json=json.dumps(yemekhane, ensure_ascii=False), type="yemekhane"))
            db.session.add(Screen(id=2, title="Hastane Duyuruları",
                content_json=json.dumps(duyuru, ensure_ascii=False), type="duyuru"))
            db.session.add(Screen(id=3, title="Otobüs Saatleri",
                content_json=json.dumps(otobus, ensure_ascii=False), type="otobus"))
            db.session.commit()

        if Setting.query.count() == 0:
            doktor1_id = User.query.filter_by(username='admin').first().id
            doktor2_id = User.query.filter_by(username='admin2').first().id

            global_settings = [
                ('hospital_name', 'Şehir Devlet Hastanesi'),
                ('currency_usd', '32.45'),
                ('currency_eur', '35.20'),
                ('currency_gold', '2.458'),
                ('currency_silver', '28.50'),
                ('weather_temp', '24'),
                ('weather_desc', 'Güneşli')
            ]
            for k, v in global_settings:
                db.session.add(Setting(key=k, value=v, doctor_id=None))

            for k, v in [('doctor_name', 'Prof. Dr. Mehmet Özkan'), ('department', 'Kardiyoloji Polikliniği')]:
                db.session.add(Setting(key=k, value=v, doctor_id=doktor1_id))

            for k, v in [('doctor_name', 'Dr. Ayşe Kaya'), ('department', 'Nöroloji Polikliniği')]:
                db.session.add(Setting(key=k, value=v, doctor_id=doktor2_id))

            db.session.commit()

if __name__ == '__main__':
    init_db()
    print("✅ Server başlatılıyor: http://localhost:5000")
    print("👨‍⚕️ Doktor 1 admin : http://localhost:5000/login  (admin / ADMIN_PASSWORD)")
    print("👩‍⚕️ Doktor 2 admin : http://localhost:5000/login  (admin2 / ADMIN2_PASSWORD)")
    print("🖥️  Doktor 1 ekranı: http://localhost:5000/")
    print("🖥️  Doktor 2 ekranı: http://localhost:5000/screen/2")
    app.run(host='0.0.0.0', port=5000, debug=True)