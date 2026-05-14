import os
from flask import Flask,render_template,request,redirect,url_for,flash,send_file
from models import db,SalesPerson,Customer,REGION_MAPPING,CHANNELS,PROVINCES
from config import Config
from datetime import datetime,timedelta
from sqlalchemy import func
from io import BytesIO

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def get_region(prov):
    for r,ps in REGION_MAPPING.items():
        if prov in ps:
            return r
    return "\u5176\u4ed6"

def assign(prov):
    region = get_region(prov)
    sl = SalesPerson.query.filter_by(region=region,is_active=True).all()
    if not sl:
        sl = SalesPerson.query.filter_by(region="\u5168\u56fd",is_active=True).all()
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
            flash("\u8bf7\u586b\u5199\u6240\u6709\u5fc5\u586b\u9879","error")
            return redirect(url_for("customer_form"))
        s = assign(d["province"])
        c = Customer(**{k:d[k] for k in fields}, assigned_to=s.id if s else None)
        db.session.add(c)
        db.session.commit()
        flash("\u63d0\u4ea4\u6210\u529f\uff01\u6211\u4eec\u4f1a\u5c3d\u5feb\u8054\u7cfb\u60a8","success")
        return redirect(url_for("customer_form"))
    return render_template("form.html",channels=CHANNELS,provinces=PROVINCES,is_internal=False)


@app.route("/c", methods=["GET","POST"])
def customer_only():
    if request.method=="POST":
        fields = ["company_name","contact_name","phone","email","province","city","channel","product_interest","note"]
        d = {k:request.form.get(k,"").strip() for k in fields}
        if not all([d["company_name"],d["contact_name"],d["phone"],d["province"],d["channel"]]):
            flash("\u8bf7\u586b\u5199\u6240\u6709\u5fc5\u586b\u9879","error")
            return redirect(url_for("customer_only"))
        s = assign(d["province"])
        c = Customer(**{k:d[k] for k in fields}, assigned_to=s.id if s else None)
        db.session.add(c)
        db.session.commit()
        flash("\u63d0\u4ea4\u6210\u529f\uff01\u6211\u4eec\u4f1a\u5c3d\u5feb\u8054\u7cfb\u60a8","success")
        return redirect(url_for("customer_only"))
    return render_template("customer_only.html",channels=CHANNELS,provinces=PROVINCES)

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
            flash(f"\u5df2\u5206\u914d\u7ed9 {s.name}({s.region})","success")
        else:
            flash("\u5f55\u5165\u6210\u529f\uff0c\u672a\u627e\u5230\u9500\u552e","warning")
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
@app.route("/smart", methods=["GET","POST"])
def smart_input():
    if request.method=="POST":
        fields = ["company_name","contact_name","phone","email","province","city","channel","product_interest","note"]
        d = {k:request.form.get(k,"").strip() for k in fields}
        s = assign(d["province"])
        c = Customer(**{k:d[k] for k in fields}, assigned_to=s.id if s else None)
        db.session.add(c)
        db.session.commit()
        if s:
            flash(f"\u5df2\u5206\u914d\u7ed9 {s.name}({s.region})","success")
        else:
            flash("\u5f55\u5165\u6210\u529f","success")
        return redirect(url_for("smart_input"))
    return render_template("smart.html",channels=CHANNELS,provinces=PROVINCES)

@app.route("/export")
def export_excel():
    from openpyxl import Workbook
    custs = Customer.query.order_by(Customer.created_at.desc()).all()
    wb = Workbook()
    ws = wb.active
    ws.append(["公司","联系人","电话","省份","渠道","销售","状态","时间"])
    for c in custs:
        sn = c.sales_person.name if c.sales_person else "未分配"
        ws.append([c.company_name, c.contact_name, c.phone, c.province, c.channel, sn, c.status, c.created_at.strftime("%Y-%m-%d %H:%M")])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="customers.xlsx")

@app.route("/sales",methods=["GET","POST"])
def sales_manage():
    if request.method=="POST":
        s = SalesPerson(name=request.form["name"],phone=request.form.get("phone",""),wechat=request.form.get("wechat",""),region=request.form["region"])
        db.session.add(s)
        db.session.commit()
        flash(f"{s.name} \u6dfb\u52a0\u6210\u529f","success")
        return redirect(url_for("sales_manage"))
    return render_template("sales.html",sales_list=SalesPerson.query.filter_by(is_active=True).all(),regions=list(REGION_MAPPING.keys())+["\u5168\u56fd"])

if __name__=="__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 9999))
    app.run(debug=False,host="0.0.0.0",port=port)
