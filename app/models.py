from flask_login import UserMixin # type: ignore
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import LONGTEXT
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
DB_NAME = "database.db"

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False) # the password hash, not plaintext
    name = db.Column(db.String(150), nullable=False)
    websites = db.relationship('Website')

class Plan(db.Model):
    __tablename__ = 'plans'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    type = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    storage_in_mb = db.Column(db.Integer, nullable=False)
    ram_in_mb = db.Column(db.Integer, nullable=False)
    cpu_cores = db.Column(db.Integer, nullable=False)
    has_redis = db.Column(db.Boolean, nullable=False)
    has_mysql = db.Column(db.Boolean, nullable=False)
    monthly_fee_in_usd = db.Column(db.Float, nullable=False)
    websites = db.relationship('Website')

class NovaVM(db.Model):
    __tablename__ = 'nova_vms'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    floating_ip = db.Column(db.String(100), nullable=True) # nullable until the VM is assigned a floating IP
    openstack_nova_vm_id = db.Column(db.String(255), unique=True, nullable=False)
    websites = db.relationship('Website')


class Website(db.Model):
    __tablename__ = 'websites'
    __table_args__ = (
        db.UniqueConstraint('nova_vm_port', 'nova_vm_id', name='unique_nova_vm_port_id'),
    )

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id', onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    public_port = db.Column(db.Integer, unique=True, nullable=False)
    nova_vm_port = db.Column(db.Integer, nullable=False)
    nova_vm_id = db.Column(db.Integer, db.ForeignKey('nova_vms.id', onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False)
    created_at = db.Column(db.BigInteger, nullable=False) # seconds since epoch

    user = db.relationship('User')
    plan = db.relationship('Plan')
    nova_vm = db.relationship('NovaVM')
