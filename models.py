from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

class SalesPerson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    wechat = db.Column(db.String(50))
    region = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    customers = db.relationship("Customer", backref="sales_person", lazy=True)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    contact_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    province = db.Column(db.String(30), nullable=False)
    city = db.Column(db.String(30))
    channel = db.Column(db.String(50), nullable=False)
    product_interest = db.Column(db.String(200))
    note = db.Column(db.Text)
    status = db.Column(db.String(20), default="\u65b0\u7ebf\u7d22")
    created_at = db.Column(db.DateTime, default=datetime.now)
    assigned_to = db.Column(db.Integer, db.ForeignKey("sales_person.id"))

REGION_MAPPING = {"\u534e\u4e1c":["\u4e0a\u6d77","\u6c5f\u82cf","\u6d59\u6c5f","\u5b89\u5fbd","\u5c71\u4e1c","\u798f\u5efa","\u6c5f\u897f"],"\u534e\u5357":["\u5e7f\u4e1c","\u5e7f\u897f","\u6d77\u5357","\u6e56\u5357","\u6e56\u5317"],"\u534e\u5317":["\u5317\u4eac","\u5929\u6d25","\u6cb3\u5317","\u5c71\u897f","\u5185\u8499\u53e4"],"\u4e1c\u5317":["\u8fbd\u5b81","\u5409\u6797","\u9ed1\u9f99\u6c5f"],"\u897f\u5357":["\u56db\u5ddd","\u91cd\u5e86","\u8d35\u5dde","\u4e91\u5357","\u897f\u85cf"],"\u897f\u5317":["\u9655\u897f","\u7518\u8083","\u9752\u6d77","\u5b81\u590f","\u65b0\u7586"],"\u6cb3\u5357":["\u6cb3\u5357"]}
CHANNELS = ["\u767e\u5ea6\u63a8\u5e7f","\u6296\u97f3","\u5fae\u4fe1\u516c\u4f17\u53f7","\u5b98\u7f51\u8868\u5355","\u5c55\u4f1a","\u8001\u5ba2\u6237\u8f6c\u4ecb\u7ecd","\u7535\u8bdd\u54a8\u8be2","1688","\u5c0f\u7ea2\u4e66","\u77e5\u4e4e","\u5176\u4ed6"]
PROVINCES = ["\u4e0a\u6d77","\u5317\u4eac","\u5929\u6d25","\u91cd\u5e86","\u6c5f\u82cf","\u6d59\u6c5f","\u5e7f\u4e1c","\u5c71\u4e1c","\u6cb3\u5317","\u6cb3\u5357","\u6e56\u5317","\u6e56\u5357","\u56db\u5ddd","\u798f\u5efa","\u5b89\u5fbd","\u8fbd\u5b81","\u6c5f\u897f","\u9655\u897f","\u5c71\u897f","\u5e7f\u897f","\u4e91\u5357","\u8d35\u5dde","\u5409\u6797","\u9ed1\u9f99\u6c5f","\u7518\u8083","\u6d77\u5357","\u5185\u8499\u53e4","\u65b0\u7586","\u897f\u85cf","\u9752\u6d77","\u5b81\u590f"]
