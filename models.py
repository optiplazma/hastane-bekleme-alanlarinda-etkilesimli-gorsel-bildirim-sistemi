from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    sira = db.Column(db.Integer, nullable=False)
    isim = db.Column(db.String(100), nullable=False)
    # ── YENİ: hangi doktora ait ──
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'sira': self.sira,
            'isim': self.isim
        }

class Screen(db.Model):
    __tablename__ = 'screens'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    # Ekranlar ortaktır, doctor_id yok

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'type': self.type,
            'content': json.loads(self.content),
            'order': self.order
        }

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(255), nullable=False)
    # ── YENİ: hangi doktora ait ──
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # key + doctor_id birlikte unique olmalı
    __table_args__ = (
        db.UniqueConstraint('key', 'doctor_id', name='uq_setting_key_doctor'),
    )

    @staticmethod
    def get_value(key, doctor_id, default=''):
        s = Setting.query.filter_by(key=key, doctor_id=doctor_id).first()
        return s.value if s else default

    @staticmethod
    def set_value(key, value, doctor_id):
        s = Setting.query.filter_by(key=key, doctor_id=doctor_id).first()
        if s:
            s.value = value
        else:
            db.session.add(Setting(key=key, value=value, doctor_id=doctor_id))
        db.session.commit()

    @staticmethod
    def get_all_for_doctor(doctor_id):
        """Bir doktorun tüm ayarlarını dict olarak döndürür."""
        rows = Setting.query.filter_by(doctor_id=doctor_id).all()
        return {r.key: r.value for r in rows}


class CallQueue(db.Model):
    """Hasta çağırma kuyruğu — admin butona basınca buraya yazılır,
       Pi3 ekranı okuyup gösterir."""
    __tablename__ = 'call_queue'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    patient_sira = db.Column(db.Integer, nullable=False)
    patient_isim = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending / done
    created_at = db.Column(db.DateTime, default=datetime.utcnow)