import os
def w(p, c):
    d = os.path.dirname(p)
    if d:
        os.makedirs(d, exist_ok=True)
    open(p, "w", encoding="utf-8").write(c)
    print(f"  [OK] {p}")

print("Creating files...")
os.makedirs("templates", exist_ok=True)

w("config.py", "import os\nclass Config:\n    SECRET_KEY='jingxin2026'\n    SQLALCHEMY_DATABASE_URI='sqlite:///crm.db'\n    SQLALCHEMY_TRACK_MODIFICATIONS=False\n")

w("models.py", '''from flask_sqlalchemy import SQLAlchemy
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
    status = db.Column(db.String(20), default="\\u65b0\\u7ebf\\u7d22")
    created_at = db.Column(db.DateTime, default=datetime.now)
    assigned_to = db.Column(db.Integer, db.ForeignKey("sales_person.id"))

REGION_MAPPING = {"\\u534e\\u4e1c":["\\u4e0a\\u6d77","\\u6c5f\\u82cf","\\u6d59\\u6c5f","\\u5b89\\u5fbd","\\u5c71\\u4e1c","\\u798f\\u5efa","\\u6c5f\\u897f"],"\\u534e\\u5357":["\\u5e7f\\u4e1c","\\u5e7f\\u897f","\\u6d77\\u5357","\\u6e56\\u5357","\\u6e56\\u5317"],"\\u534e\\u5317":["\\u5317\\u4eac","\\u5929\\u6d25","\\u6cb3\\u5317","\\u5c71\\u897f","\\u5185\\u8499\\u53e4"],"\\u4e1c\\u5317":["\\u8fbd\\u5b81","\\u5409\\u6797","\\u9ed1\\u9f99\\u6c5f"],"\\u897f\\u5357":["\\u56db\\u5ddd","\\u91cd\\u5e86","\\u8d35\\u5dde","\\u4e91\\u5357","\\u897f\\u85cf"],"\\u897f\\u5317":["\\u9655\\u897f","\\u7518\\u8083","\\u9752\\u6d77","\\u5b81\\u590f","\\u65b0\\u7586"],"\\u6cb3\\u5357":["\\u6cb3\\u5357"]}
CHANNELS = ["\\u767e\\u5ea6\\u63a8\\u5e7f","\\u6296\\u97f3","\\u5fae\\u4fe1\\u516c\\u4f17\\u53f7","\\u5b98\\u7f51\\u8868\\u5355","\\u5c55\\u4f1a","\\u8001\\u5ba2\\u6237\\u8f6c\\u4ecb\\u7ecd","\\u7535\\u8bdd\\u54a8\\u8be2","1688","\\u5c0f\\u7ea2\\u4e66","\\u77e5\\u4e4e","\\u5176\\u4ed6"]
PROVINCES = ["\\u4e0a\\u6d77","\\u5317\\u4eac","\\u5929\\u6d25","\\u91cd\\u5e86","\\u6c5f\\u82cf","\\u6d59\\u6c5f","\\u5e7f\\u4e1c","\\u5c71\\u4e1c","\\u6cb3\\u5317","\\u6cb3\\u5357","\\u6e56\\u5317","\\u6e56\\u5357","\\u56db\\u5ddd","\\u798f\\u5efa","\\u5b89\\u5fbd","\\u8fbd\\u5b81","\\u6c5f\\u897f","\\u9655\\u897f","\\u5c71\\u897f","\\u5e7f\\u897f","\\u4e91\\u5357","\\u8d35\\u5dde","\\u5409\\u6797","\\u9ed1\\u9f99\\u6c5f","\\u7518\\u8083","\\u6d77\\u5357","\\u5185\\u8499\\u53e4","\\u65b0\\u7586","\\u897f\\u85cf","\\u9752\\u6d77","\\u5b81\\u590f"]
''')

w("app.py", '''from flask import Flask,render_template,request,redirect,url_for,flash,send_file
from models import db,SalesPerson,Customer,REGION_MAPPING,CHANNELS,PROVINCES
from config import Config
from datetime import datetime,timedelta
from sqlalchemy import func
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def get_region(prov):
    for r,ps in REGION_MAPPING.items():
        if prov in ps:
            return r
    return "\\u5176\\u4ed6"

def assign(prov):
    region = get_region(prov)
    sl = SalesPerson.query.filter_by(region=region,is_active=True).all()
    if not sl:
        sl = SalesPerson.query.filter_by(region="\\u5168\\u56fd",is_active=True).all()
    if not sl:
        return None
    res = [(s, Customer.query.filter_by(assigned_to=s.id).count()) for s in sl]
    res.sort(key=lambda x:x[1])
    return res[0][0]

@app.route("/")
@app.route("/form",methods=["GET","POST"])
def customer_form():
    if request.method=="POST":
        fields = ["company_name","contact_name","phone","email","province","city","channel","product_interest","note"]
        d = {k:request.form.get(k,"").strip() for k in fields}
        if not all([d["company_name"],d["contact_name"],d["phone"],d["province"],d["channel"]]):
            flash("\\u8bf7\\u586b\\u5199\\u6240\\u6709\\u5fc5\\u586b\\u9879","error")
            return redirect(url_for("customer_form"))
        s = assign(d["province"])
        c = Customer(**{k:d[k] for k in fields}, assigned_to=s.id if s else None)
        db.session.add(c)
        db.session.commit()
        flash("\\u63d0\\u4ea4\\u6210\\u529f\\uff01\\u6211\\u4eec\\u4f1a\\u5c3d\\u5feb\\u8054\\u7cfb\\u60a8","success")
        return redirect(url_for("customer_form"))
    return render_template("form.html",channels=CHANNELS,provinces=PROVINCES,is_internal=False)

@app.route("/internal/add",methods=["GET","POST"])
def internal_add():
    if request.method=="POST":
        fields = ["company_name","contact_name","phone","email","province","city","channel","product_interest","note"]
        d = {k:request.form.get(k,"").strip() for k in fields}
        s = assign(d["province"])
        c = Customer(**{k:d[k] for k in fields}, assigned_to=s.id if s else None)
        db.session.add(c)
        db.session.commit()
        if s:
            flash(f"\\u5df2\\u5206\\u914d\\u7ed9 {s.name}({s.region})","success")
        else:
            flash("\\u5f55\\u5165\\u6210\\u529f\\uff0c\\u672a\\u627e\\u5230\\u9500\\u552e","warning")
        return redirect(url_for("internal_add"))
    return render_template("form.html",channels=CHANNELS,provinces=PROVINCES,is_internal=True)

@app.route("/dashboard")
def dashboard():
    total = Customer.query.count()
    td = datetime.now().date()
    td_c = Customer.query.filter(func.date(Customer.created_at)==td).count()
    ws = td - timedelta(days=td.weekday())
    wk_c = Customer.query.filter(Customer.created_at>=datetime.combine(ws,datetime.min.time())).count()
    ch = db.session.query(Customer.channel,func.count(Customer.id)).group_by(Customer.channel).order_by(func.count(Customer.id).desc()).all()
    rg = {}
    for cu in Customer.query.all():
        r = get_region(cu.province)
        rg[r] = rg.get(r,0)+1
    ss = db.session.query(SalesPerson.name,SalesPerson.region,func.count(Customer.id)).join(Customer,Customer.assigned_to==SalesPerson.id).group_by(SalesPerson.id).order_by(func.count(Customer.id).desc()).all()
    return render_template("dashboard.html",total_customers=total,today_count=td_c,week_count=wk_c,channel_stats=ch,region_stats=rg,sales_stats=ss)

@app.route("/customers")
def customer_list():
    ch = request.args.get("channel","")
    pv = request.args.get("province","")
    q = Customer.query
    if ch: q = q.filter(Customer.channel==ch)
    if pv: q = q.filter(Customer.province==pv)
    return render_template("customers.html",customers=q.order_by(Customer.created_at.desc()).all(),channels=CHANNELS,provinces=PROVINCES)

@app.route("/export")
def export_excel():
    data = []
    for c in Customer.query.order_by(Customer.created_at.desc()).all():
        sn = c.sales_person.name if c.sales_person else "\\u672a\\u5206\\u914d"
        data.append({"\\u516c\\u53f8":c.company_name,"\\u8054\\u7cfb\\u4eba":c.contact_name,"\\u7535\\u8bdd":c.phone,"\\u7701\\u4efd":c.province,"\\u6e20\\u9053":c.channel,"\\u9500\\u552e":sn,"\\u65f6\\u95f4":c.created_at.strftime("%Y-%m-%d %H:%M")})
    buf = BytesIO()
    pd.DataFrame(data).to_excel(buf,index=False,engine="openpyxl")
    buf.seek(0)
    return send_file(buf,mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",as_attachment=True,download_name="customers.xlsx")

@app.route("/sales",methods=["GET","POST"])
def sales_manage():
    if request.method=="POST":
        s = SalesPerson(name=request.form["name"],phone=request.form.get("phone",""),wechat=request.form.get("wechat",""),region=request.form["region"])
        db.session.add(s)
        db.session.commit()
        flash(f"{s.name} \\u6dfb\\u52a0\\u6210\\u529f","success")
        return redirect(url_for("sales_manage"))
    return render_template("sales.html",sales_list=SalesPerson.query.filter_by(is_active=True).all(),regions=list(REGION_MAPPING.keys())+["\\u5168\\u56fd"])

if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True,host="0.0.0.0",port=5000)
''')

w("templates/base.html",'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>净信科技CRM</title>
<link href="https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
<style>
.navbar{background:linear-gradient(135deg,#1a73e8,#0d47a1)}
.sc{border-radius:12px;padding:20px;color:#fff;margin-bottom:15px}
.sc h3{font-size:2.5rem;margin:0}
.g1{background:linear-gradient(135deg,#667eea,#764ba2)}
.g2{background:linear-gradient(135deg,#f093fb,#f5576c)}
.g3{background:linear-gradient(135deg,#4facfe,#00f2fe)}
.g4{background:linear-gradient(135deg,#43e97b,#38f9d7)}
</style>
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark">
<div class="container">
<a class="navbar-brand fw-bold" href="/">净信科技 CRM</a>
<button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#nv"><span class="navbar-toggler-icon"></span></button>
<div class="collapse navbar-collapse" id="nv">
<div class="navbar-nav ms-auto">
<a class="nav-link" href="/form">客户登记</a>
<a class="nav-link" href="/internal/add">内部录入</a>
<a class="nav-link" href="/dashboard">数据看板</a>
<a class="nav-link" href="/customers">客户列表</a>
<a class="nav-link" href="/sales">销售管理</a>
<a class="nav-link" href="/export">导出Excel</a>
</div></div></div></nav>
<div class="container mt-4">
{% with messages = get_flashed_messages(with_categories=true) %}
{% for cat, msg in messages %}
<div class="alert alert-{{ 'success' if cat == 'success' else 'warning' if cat == 'warning' else 'danger' }} alert-dismissible fade show">{{ msg }}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>
{% endfor %}{% endwith %}
{% block content %}{% endblock %}
</div>
<script src="https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
</body></html>''')

w("templates/form.html",'''{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center"><div class="col-md-8"><div class="card shadow">
<div class="card-header bg-primary text-white text-center">
<h4>{% if is_internal %}内部客户录入{% else %}上海净信 - 产品咨询登记{% endif %}</h4>
{% if not is_internal %}<p class="mb-0">请填写以下信息，我们将安排专业人员与您对接</p>{% endif %}
</div>
<div class="card-body p-4"><form method="POST">
<div class="row">
<div class="col-md-6 mb-3"><label class="form-label">公司名称 <span class="text-danger">*</span></label><input type="text" name="company_name" class="form-control" required placeholder="例：XX大学"></div>
<div class="col-md-6 mb-3"><label class="form-label">联系人 <span class="text-danger">*</span></label><input type="text" name="contact_name" class="form-control" required></div></div>
<div class="row">
<div class="col-md-6 mb-3"><label class="form-label">手机号 <span class="text-danger">*</span></label><input type="tel" name="phone" class="form-control" required></div>
<div class="col-md-6 mb-3"><label class="form-label">邮箱</label><input type="email" name="email" class="form-control"></div></div>
<div class="row">
<div class="col-md-6 mb-3"><label class="form-label">省份 <span class="text-danger">*</span></label><select name="province" class="form-select" required><option value="">请选择</option>{% for p in provinces %}<option value="{{ p }}">{{ p }}</option>{% endfor %}</select></div>
<div class="col-md-6 mb-3"><label class="form-label">城市</label><input type="text" name="city" class="form-control"></div></div>
<div class="row">
<div class="col-md-6 mb-3"><label class="form-label">渠道 <span class="text-danger">*</span></label><select name="channel" class="form-select" required><option value="">请选择</option>{% for c in channels %}<option value="{{ c }}">{{ c }}</option>{% endfor %}</select></div>
<div class="col-md-6 mb-3"><label class="form-label">感兴趣的产品</label><input type="text" name="product_interest" class="form-control" placeholder="例：组织研磨仪"></div></div>
<div class="mb-3"><label class="form-label">备注</label><textarea name="note" class="form-control" rows="3"></textarea></div>
<button type="submit" class="btn btn-primary btn-lg w-100">{% if is_internal %}录入客户{% else %}提交信息{% endif %}</button>
</form></div></div></div></div>
{% endblock %}''')

w("templates/dashboard.html",'''{% extends "base.html" %}
{% block content %}
<h3 class="mb-4">数据看板</h3>
<div class="row">
<div class="col-md-3"><div class="sc g1"><p class="mb-1">总客户数</p><h3>{{ total_customers }}</h3></div></div>
<div class="col-md-3"><div class="sc g2"><p class="mb-1">今日新增</p><h3>{{ today_count }}</h3></div></div>
<div class="col-md-3"><div class="sc g3"><p class="mb-1">本周新增</p><h3>{{ week_count }}</h3></div></div>
<div class="col-md-3"><div class="sc g4"><p class="mb-1">渠道数</p><h3>{{ channel_stats|length }}</h3></div></div>
</div>
<div class="row mt-4">
<div class="col-md-6"><div class="card"><div class="card-header"><b>渠道来源统计</b></div><div class="card-body">
<table class="table table-striped"><thead><tr><th>渠道</th><th>数量</th><th>占比</th></tr></thead>
<tbody>{% for c,n in channel_stats %}<tr><td>{{ c }}</td><td>{{ n }}</td><td>{{ "%.1f"|format(n/total_customers*100 if total_customers else 0) }}%</td></tr>{% endfor %}</tbody></table>
</div></div></div>
<div class="col-md-6"><div class="card"><div class="card-header"><b>区域分布</b></div><div class="card-body">
<table class="table table-striped"><thead><tr><th>区域</th><th>数量</th><th>占比</th></tr></thead>
<tbody>{% for r,n in region_stats.items() %}<tr><td>{{ r }}</td><td>{{ n }}</td><td>{{ "%.1f"|format(n/total_customers*100 if total_customers else 0) }}%</td></tr>{% endfor %}</tbody></table>
</div></div></div></div>
<div class="row mt-4"><div class="col-md-12"><div class="card"><div class="card-header"><b>销售分配</b></div><div class="card-body">
<table class="table table-striped"><thead><tr><th>销售</th><th>区域</th><th>客户数</th></tr></thead>
<tbody>{% for nm,rg,ct in sales_stats %}<tr><td>{{ nm }}</td><td>{{ rg }}</td><td>{{ ct }}</td></tr>{% endfor %}</tbody></table>
</div></div></div></div>
{% endblock %}''')

w("templates/sales.html",'''{% extends "base.html" %}
{% block content %}
<h3 class="mb-4">销售人员管理</h3>
<div class="row">
<div class="col-md-5"><div class="card"><div class="card-header"><b>添加销售</b></div><div class="card-body">
<form method="POST">
<div class="mb-3"><label class="form-label">姓名</label><input type="text" name="name" class="form-control" required></div>
<div class="mb-3"><label class="form-label">手机</label><input type="text" name="phone" class="form-control"></div>
<div class="mb-3"><label class="form-label">微信</label><input type="text" name="wechat" class="form-control"></div>
<div class="mb-3"><label class="form-label">负责区域</label><select name="region" class="form-select" required>{% for r in regions %}<option value="{{ r }}">{{ r }}</option>{% endfor %}</select></div>
<button type="submit" class="btn btn-primary w-100">添加</button>
</form></div></div></div>
<div class="col-md-7"><div class="card"><div class="card-header"><b>销售列表</b></div><div class="card-body">
<table class="table"><thead><tr><th>姓名</th><th>手机</th><th>微信</th><th>区域</th></tr></thead>
<tbody>{% for s in sales_list %}<tr><td>{{ s.name }}</td><td>{{ s.phone }}</td><td>{{ s.wechat }}</td><td>{{ s.region }}</td></tr>{% endfor %}</tbody></table>
</div></div></div></div>
{% endblock %}''')

w("templates/customers.html",'''{% extends "base.html" %}
{% block content %}
<h3 class="mb-4">客户列表</h3>
<form class="row g-3 mb-4" method="GET">
<div class="col-md-3"><select name="channel" class="form-select"><option value="">全部渠道</option>{% for c in channels %}<option value="{{ c }}">{{ c }}</option>{% endfor %}</select></div>
<div class="col-md-3"><select name="province" class="form-select"><option value="">全部省份</option>{% for p in provinces %}<option value="{{ p }}">{{ p }}</option>{% endfor %}</select></div>
<div class="col-md-2"><button type="submit" class="btn btn-primary">筛选</button></div>
</form>
<div class="table-responsive"><table class="table table-striped table-hover">
<thead><tr><th>公司</th><th>联系人</th><th>电话</th><th>省份</th><th>渠道</th><th>销售</th><th>状态</th><th>时间</th></tr></thead>
<tbody>{% for c in customers %}<tr><td>{{ c.company_name }}</td><td>{{ c.contact_name }}</td><td>{{ c.phone }}</td><td>{{ c.province }}</td><td>{{ c.channel }}</td><td>{{ c.sales_person.name if c.sales_person else "未分配" }}</td><td><span class="badge bg-info">{{ c.status }}</span></td><td>{{ c.created_at.strftime("%m-%d %H:%M") }}</td></tr>{% endfor %}</tbody>
</table></div>
{% endblock %}''')

print("\n" + "=" * 50)
print("  ALL FILES CREATED SUCCESSFULLY!")
print("=" * 50)
print("\nNow run:  python app.py")