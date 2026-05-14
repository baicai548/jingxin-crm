import os
from flask import Flask,render_template,request,redirect,url_for,flash,send_file
from models import db,SalesPerson,Customer,REGION_MAPPING,CHANNELS,PROVINCES,DEPARTMENTS,SALES_MAP
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

def assign(prov, dept):
    if prov in SALES_MAP and dept in SALES_MAP[prov]:
        name = SALES_MAP[prov][dept]
        s = SalesPerson.query.filter_by(name=name, department=dept, is_active=True).first()
        if s:
            return s
    return None

@app.route("/")
@app.route("/smart", methods=["GET","POST"])
def smart_input():
    if request.method=="POST":
        fields = ["company_name","contact_name","phone","email","province","city","channel","department","product_interest","note"]
        d = {k:request.form.get(k,"").strip() for k in fields}
        if not all([d["contact_name"],d["phone"],d["province"],d["channel"],d["department"]]):
            flash("\u8bf7\u586b\u5199\u5fc5\u586b\u9879","error")
            return redirect(url_for("smart_input"))
        s = assign(d["province"], d["department"])
        c = Customer(company_name=d["company_name"],contact_name=d["contact_name"],phone=d["phone"],email=d["email"],province=d["province"],city=d["city"],channel=d["channel"],department=d["department"],product_interest=d["product_interest"],note=d["note"],assigned_to=s.id if s else None)
        db.session.add(c)
        db.session.commit()
        if s:
            flash(f"\u5df2\u5206\u914d\u7ed9 {s.name}({s.department}-{d['province']})","success")
        else:
            flash("\u5f55\u5165\u6210\u529f\uff0c\u672a\u627e\u5230\u5bf9\u5e94\u9500\u552e","warning")
        return redirect(url_for("smart_input"))
    return render_template("smart.html",channels=CHANNELS,provinces=PROVINCES,departments=DEPARTMENTS)

@app.route("/dashboard")
def dashboard():
    total = Customer.query.count()
    td = datetime.now().date()
    td_c = Customer.query.filter(func.date(Customer.created_at)==td).count()
    ws = td - timedelta(days=td.weekday())
    wk_c = Customer.query.filter(Customer.created_at>=datetime.combine(ws,datetime.min.time())).count()
    ch = db.session.query(Customer.channel,func.count(Customer.id)).group_by(Customer.channel).order_by(func.count(Customer.id).desc()).all()
    dp = db.session.query(Customer.department,func.count(Customer.id)).group_by(Customer.department).order_by(func.count(Customer.id).desc()).all()
    rg = {}
    for cu in Customer.query.all():
        r = get_region(cu.province)
        rg[r] = rg.get(r,0)+1
    ss = db.session.query(SalesPerson.name,SalesPerson.department,func.count(Customer.id)).join(Customer,Customer.assigned_to==SalesPerson.id).group_by(SalesPerson.id).order_by(func.count(Customer.id).desc()).all()
    return render_template("dashboard.html",total_customers=total,today_count=td_c,week_count=wk_c,channel_stats=ch,dept_stats=dp,region_stats=rg,sales_stats=ss)

@app.route("/customers")
def customer_list():
    ch = request.args.get("channel","")
    pv = request.args.get("province","")
    dp = request.args.get("department","")
    q = Customer.query
    if ch: q = q.filter(Customer.channel==ch)
    if pv: q = q.filter(Customer.province==pv)
    if dp: q = q.filter(Customer.department==dp)
    return render_template("customers.html",customers=q.order_by(Customer.created_at.desc()).all(),channels=CHANNELS,provinces=PROVINCES,departments=DEPARTMENTS)

@app.route("/export")
def export_excel():
    from openpyxl import Workbook
    custs = Customer.query.order_by(Customer.created_at.desc()).all()
    wb = Workbook()
    ws = wb.active
    ws.append(["\u516c\u53f8","\u8054\u7cfb\u4eba","\u7535\u8bdd","\u7701\u4efd","\u57ce\u5e02","\u5ba2\u6237\u6765\u6e90","\u4ea7\u54c1\u5f52\u5c5e","\u54a8\u8be2\u4ea7\u54c1","\u9500\u552e","\u72b6\u6001","\u65f6\u95f4"])
    for c in custs:
        sn = c.sales_person.name if c.sales_person else "\u672a\u5206\u914d"
        ws.append([c.company_name,c.contact_name,c.phone,c.province,c.city,c.channel,c.department,c.product_interest,sn,c.status,c.created_at.strftime("%Y-%m-%d %H:%M")])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf,mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",as_attachment=True,download_name="customers.xlsx")

@app.route("/sales", methods=["GET","POST"])
def sales_manage():
    if request.method=="POST":
        s = SalesPerson(name=request.form["name"],phone=request.form.get("phone",""),wechat=request.form.get("wechat",""),region=request.form.get("region",""),department=request.form["department"])
        db.session.add(s)
        db.session.commit()
        flash(f"{s.name} \u6dfb\u52a0\u6210\u529f","success")
        return redirect(url_for("sales_manage"))
    return render_template("sales.html",sales_list=SalesPerson.query.filter_by(is_active=True).order_by(SalesPerson.department).all(),regions=list(REGION_MAPPING.keys()),departments=DEPARTMENTS)

@app.route("/init_sales")
def init_sales():
    count = 0
    added = set()
    for prov, depts in SALES_MAP.items():
        for dept, name in depts.items():
            key = f"{name}_{dept}"
            if key not in added:
                existing = SalesPerson.query.filter_by(name=name, department=dept).first()
                if not existing:
                    region = get_region(prov)
                    s = SalesPerson(name=name, phone="", region=region, department=dept)
                    db.session.add(s)
                    count += 1
                added.add(key)
    db.session.commit()
    return f"Done! Added {count} sales people. <a href='/sales'>View Sales</a> | <a href='/'>Home</a>"

if __name__=="__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 9999))
    app.run(debug=False,host="0.0.0.0",port=port)
