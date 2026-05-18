from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(50), default='')
    is_admin = db.Column(db.Boolean, default=False)
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    created_customers = db.relationship("Customer", backref="creator", lazy=True, foreign_keys="Customer.created_by")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class SalesPerson(db.Model):
    __tablename__ = 'sales_person'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(50), default='')
    wechat = db.Column(db.String(50), default='')
    region = db.Column(db.String(50), nullable=False, default='')
    department = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    customers = db.relationship("Customer", backref="sales_person", lazy=True, foreign_keys="Customer.assigned_to")


class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), default='')
    contact_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), default='')
    province = db.Column(db.String(30), nullable=False)
    city = db.Column(db.String(30), default='')
    channel = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(20), default='')
    product_interest = db.Column(db.String(200), default='')
    note = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default="新线索")
    created_at = db.Column(db.DateTime, default=datetime.now)
    assigned_to = db.Column(db.Integer, db.ForeignKey("sales_person.id"))
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))


REGION_MAPPING = {
    "华东": ["上海", "江苏", "浙江", "安徽", "山东", "福建", "江西"],
    "华南": ["广东", "广西", "海南", "湖南", "湖北"],
    "华北": ["北京", "天津", "河北", "山西", "内蒙古"],
    "东北": ["辽宁", "吉林", "黑龙江"],
    "西南": ["四川", "重庆", "贵州", "云南", "西藏"],
    "西北": ["陕西", "甘肃", "青海", "宁夏", "新疆"],
    "河南": ["河南"],
    "港澳台": ["港澳台"],
}

CHANNELS = ["丁香通", "仪器信息网", "拓赫化工", "微信好友", "QQ好友", "电询", "净信商桥", "拓赫商桥", "雷萌商桥", "测博商桥", "拓赫电询", "其他"]

DEPARTMENTS = ["线下一部", "线下二部", "线上", "ibidi"]

PROVINCES = ["上海", "北京", "天津", "重庆", "江苏", "浙江", "广东", "山东", "河北", "河南", "湖北", "湖南", "四川", "福建", "安徽", "辽宁", "江西", "陕西", "山西", "广西", "云南", "贵州", "吉林", "黑龙江", "甘肃", "海南", "内蒙古", "新疆", "西藏", "青海", "宁夏", "港澳台"]

SALES_MAP = {
    "上海": {"线下一部": "张厚艺", "线下二部": "张厚艺", "线上": "林赛", "ibidi": "王凡凡"},
    "江苏": {"线下一部": "张厚艺", "线下二部": "张厚艺", "线上": "徐文理", "ibidi": "方美琴"},
    "福建": {"线下一部": "李晨", "线下二部": "李晨", "线上": "胡莉莉", "ibidi": "胡莉莉"},
    "安徽": {"线下一部": "张厚艺", "线下二部": "张厚艺", "线上": "刘贤泽", "ibidi": "徐文理"},
    "浙江": {"线下一部": "徐彦华", "线下二部": "姚嘉玮", "线上": "胡莉莉", "ibidi": "胡莉莉"},
    "西藏": {"线下一部": "张厚艺", "线下二部": "张厚艺", "线上": "林赛", "ibidi": "林赛"},
    "江西": {"线下一部": "廖海春", "线下二部": "廖海春", "线上": "吴强", "ibidi": "戴晨晓"},
    "湖南": {"线下一部": "叶志波", "线下二部": "叶志波", "线上": "徐伟杰", "ibidi": "方美琴"},
    "云南": {"线下一部": "杨梅", "线下二部": "杨梅", "线上": "邵先生", "ibidi": "方美琴"},
    "北京": {"线下一部": "王军士", "线下二部": "李静娴", "线上": "叶琴", "ibidi": "方美琴"},
    "内蒙古": {"线下一部": "季应许", "线下二部": "季应许", "线上": "戴晨晓", "ibidi": "方美琴"},
    "天津": {"线下一部": "祁晓康", "线下二部": "祁晓康", "线上": "戴晨晓", "ibidi": "方美琴"},
    "河北": {"线下一部": "孟彪", "线下二部": "孟彪", "线上": "邵先生", "ibidi": "邵琴"},
    "河南": {"线下一部": "李蔚蔚", "线下二部": "李蔚蔚", "线上": "魏天宇", "ibidi": "魏天宇"},
    "山西": {"线下一部": "赵文庆", "线下二部": "赵文庆", "线上": "赵桧丽", "ibidi": "赵桧丽"},
    "广东": {"线下一部": "张厚艺", "线下二部": "齐长学", "线上": "王凡凡", "ibidi": "方美琴"},
    "海南": {"线下一部": "王梦可", "线下二部": "王梦可", "线上": "王凡凡", "ibidi": "方美琴"},
    "广西": {"线下一部": "林奕全", "线下二部": "林奕全", "线上": "周秋伟", "ibidi": "方美琴"},
    "贵州": {"线下一部": "杨梅", "线下二部": "孙佳琴", "线上": "周秋伟", "ibidi": "方美琴"},
    "重庆": {"线下一部": "张厚艺", "线下二部": "张厚艺", "线上": "封婷婷", "ibidi": "封婷婷"},
    "四川": {"线下一部": "张厚艺", "线下二部": "徐艺梦", "线上": "封婷婷", "ibidi": "方美琴"},
    "湖北": {"线下一部": "徐足珍", "线下二部": "徐足珍", "线上": "徐伟杰", "ibidi": "徐足珍"},
    "陕西": {"线下一部": "闫静", "线下二部": "闫静", "线上": "徐文理", "ibidi": "徐文理"},
    "甘肃": {"线下一部": "何小丽", "线下二部": "何小丽", "线上": "赵桧丽", "ibidi": "方美琴"},
    "宁夏": {"线下一部": "闫静", "线下二部": "闫静", "线上": "林赛", "ibidi": "方美琴"},
    "新疆": {"线下一部": "张战江", "线下二部": "张战江", "线上": "李辰俊", "ibidi": "方美琴"},
    "青海": {"线下一部": "何小丽", "线下二部": "何小丽", "线上": "李辰俊", "ibidi": "方美琴"},
    "山东": {"线下一部": "刘珄", "线下二部": "孟彪", "线上": "刘贤泽", "ibidi": "方美琴"},
    "辽宁": {"线下一部": "王军士", "线下二部": "王军士", "线上": "魏天宇", "ibidi": "方美琴"},
    "黑龙江": {"线下一部": "张洁", "线下二部": "张洁", "线上": "吴强", "ibidi": "方美琴"},
    "吉林": {"线下一部": "张洁", "线下二部": "张洁", "线上": "叶琴", "ibidi": "叶琴"},
    "港澳台": {"线下一部": "吴强", "线下二部": "吴强", "线上": "吴强", "ibidi": "吴强"},
}
