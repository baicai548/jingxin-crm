import os

# 修复 Render PostgreSQL URL
database_url = os.environ.get('DATABASE_URL', '')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    os.environ['DATABASE_URL'] = database_url

from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, SalesPerson, Customer, REGION_MAPPING, CHANNELS, PROVINCES, DEPARTMENTS, SALES_MAP
from config import Config
from datetime import datetime, timedelta
from sqlalchemy import func
from io import BytesIO
import requests as http_requests
import base64

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# 初始化 Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def get_region(prov):
    for r, ps in REGION_MAPPING.items():
        if prov in ps:
            return r
    return "其他"


def assign(prov, dept):
    if prov in SALES_MAP and dept in SALES_MAP[prov]:
        name = SALES_MAP[prov][dept]
        s = SalesPerson.query.filter_by(name=name, department=dept, is_active=True).first()
        if s:
            return s
    return None


# ==================== 登录相关 ====================

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("smart_input"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("请输入用户名和密码", "error")
            return redirect(url_for("login"))
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active_user:
            login_user(user)
            flash(f"欢迎回来，{user.display_name or user.username}！", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("smart_input"))
        else:
            flash("用户名或密码错误", "error")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("已退出登录", "success")
    return redirect(url_for("login"))


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_pwd = request.form.get("old_password", "").strip()
        new_pwd = request.form.get("new_password", "").strip()
        confirm_pwd = request.form.get("confirm_password", "").strip()
        if not all([old_pwd, new_pwd, confirm_pwd]):
            flash("请填写所有字段", "error")
        elif not current_user.check_password(old_pwd):
            flash("原密码错误", "error")
        elif new_pwd != confirm_pwd:
            flash("两次密码不一致", "error")
        elif len(new_pwd) < 4:
            flash("新密码至少4位", "error")
        else:
            current_user.set_password(new_pwd)
            db.session.commit()
            flash("密码修改成功", "success")
            return redirect(url_for("smart_input"))
    return render_template("change_password.html")


# ==================== 用户管理（仅管理员） ====================

@app.route("/users")
@login_required
def user_manage():
    if not current_user.is_admin:
        flash("没有权限", "error")
        return redirect(url_for("smart_input"))
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("users.html", users=users)


@app.route("/users/add", methods=["POST"])
@login_required
def user_add():
    if not current_user.is_admin:
        flash("没有权限", "error")
        return redirect(url_for("smart_input"))
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    display_name = request.form.get("display_name", "").strip()
    is_admin = request.form.get("is_admin") == "on"
    if not username or not password:
        flash("用户名和密码必填", "error")
        return redirect(url_for("user_manage"))
    if User.query.filter_by(username=username).first():
        flash("用户名已存在", "error")
        return redirect(url_for("user_manage"))
    user = User(username=username, display_name=display_name or username, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f"用户 {username} 创建成功", "success")
    return redirect(url_for("user_manage"))


@app.route("/users/<int:id>/delete", methods=["POST"])
@login_required
def user_delete(id):
    if not current_user.is_admin:
        flash("没有权限", "error")
        return redirect(url_for("smart_input"))
    if id == current_user.id:
        flash("不能删除自己", "error")
        return redirect(url_for("user_manage"))
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash(f"用户 {user.username} 已删除", "success")
    return redirect(url_for("user_manage"))


@app.route("/users/<int:id>/reset", methods=["POST"])
@login_required
def user_reset_password(id):
    if not current_user.is_admin:
        flash("没有权限", "error")
        return redirect(url_for("smart_input"))
    user = User.query.get_or_404(id)
    new_pwd = request.form.get("new_password", "").strip()
    if not new_pwd or len(new_pwd) < 4:
        flash("密码至少4位", "error")
        return redirect(url_for("user_manage"))
    user.set_password(new_pwd)
    db.session.commit()
    flash(f"用户 {user.username} 密码已重置", "success")
    return redirect(url_for("user_manage"))


# ==================== 业务功能 ====================

@app.route("/")
@app.route("/smart", methods=["GET", "POST"])
@login_required
def smart_input():
    if request.method == "POST":
        fields = ["company_name", "contact_name", "phone", "email", "province", "city", "channel", "department", "product_interest", "note"]
        d = {k: request.form.get(k, "").strip() for k in fields}
        if not all([d["contact_name"], d["phone"], d["province"], d["channel"], d["department"]]):
            flash("请填写必填项", "error")
            return redirect(url_for("smart_input"))
        s = assign(d["province"], d["department"])
        c = Customer(
            company_name=d["company_name"], contact_name=d["contact_name"],
            phone=d["phone"], email=d["email"], province=d["province"],
            city=d["city"], channel=d["channel"], department=d["department"],
            product_interest=d["product_interest"], note=d["note"],
            assigned_to=s.id if s else None,
            created_by=current_user.id
        )
        db.session.add(c)
        db.session.commit()
        if s:
            flash(f"已分配给 {s.name}({s.department}-{d['province']})", "success")
        else:
            flash("录入成功，未找到对应销售", "warning")
        return redirect(url_for("smart_input"))
    return render_template("smart.html", channels=CHANNELS, provinces=PROVINCES, departments=DEPARTMENTS)


@app.route("/dashboard")
@login_required
def dashboard():
    total = Customer.query.count()
    td = datetime.now().date()
    td_c = Customer.query.filter(func.date(Customer.created_at) == td).count()
    ws = td - timedelta(days=td.weekday())
    wk_c = Customer.query.filter(Customer.created_at >= datetime.combine(ws, datetime.min.time())).count()
    ch = db.session.query(Customer.channel, func.count(Customer.id)).group_by(Customer.channel).order_by(func.count(Customer.id).desc()).all()
    dp = db.session.query(Customer.department, func.count(Customer.id)).group_by(Customer.department).order_by(func.count(Customer.id).desc()).all()
    rg = {}
    for cu in Customer.query.all():
        r = get_region(cu.province)
        rg[r] = rg.get(r, 0) + 1
    ss = db.session.query(SalesPerson.name, SalesPerson.department, func.count(Customer.id)).join(Customer, Customer.assigned_to == SalesPerson.id).group_by(SalesPerson.id).order_by(func.count(Customer.id).desc()).all()
    return render_template("dashboard.html", total_customers=total, today_count=td_c, week_count=wk_c, channel_stats=ch, dept_stats=dp, region_stats=rg, sales_stats=ss)


@app.route("/customers")
@login_required
def customer_list():
    ch = request.args.get("channel", "")
    pv = request.args.get("province", "")
    dp = request.args.get("department", "")
    q = Customer.query
    if ch:
        q = q.filter(Customer.channel == ch)
    if pv:
        q = q.filter(Customer.province == pv)
    if dp:
        q = q.filter(Customer.department == dp)
    return render_template("customers.html", customers=q.order_by(Customer.created_at.desc()).all(), channels=CHANNELS, provinces=PROVINCES, departments=DEPARTMENTS)


@app.route("/customer/<int:id>/delete", methods=["GET", "POST"])
@login_required
def delete_customer(id):
    c = Customer.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash("已删除", "success")
    return redirect(url_for("customer_list"))


@app.route("/export")
@login_required
def export_excel():
    from openpyxl import Workbook
    custs = Customer.query.order_by(Customer.created_at.desc()).all()
    wb = Workbook()
    ws = wb.active
    ws.append(["公司", "联系人", "电话", "省份", "城市", "客户来源", "产品归属", "咨询产品", "销售", "录入人", "状态", "时间"])
    for c in custs:
        sn = c.sales_person.name if c.sales_person else "未分配"
        creator_name = c.creator.display_name if c.creator else "未知"
        ws.append([c.company_name, c.contact_name, c.phone, c.province, c.city, c.channel, c.department, c.product_interest, sn, creator_name, c.status, c.created_at.strftime("%Y-%m-%d %H:%M")])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="customers.xlsx")


@app.route("/sales", methods=["GET", "POST"])
@login_required
def sales_manage():
    if request.method == "POST":
        s = SalesPerson(name=request.form["name"], phone=request.form.get("phone", ""), wechat=request.form.get("wechat", ""), region=request.form.get("region", ""), department=request.form["department"])
        db.session.add(s)
        db.session.commit()
        flash(f"{s.name} 添加成功", "success")
        return redirect(url_for("sales_manage"))
    return render_template("sales.html", sales_list=SalesPerson.query.filter_by(is_active=True).order_by(SalesPerson.department).all(), regions=list(REGION_MAPPING.keys()), departments=DEPARTMENTS)


@app.route("/init_sales")
def init_sales():
    SalesPerson.query.delete()
    db.session.commit()
    count = 0
    added = set()
    for prov, depts in SALES_MAP.items():
        for dept, name in depts.items():
            key = f"{name}_{dept}"
            if key not in added:
                region = get_region(prov)
                s = SalesPerson(name=name, phone="", region=region, department=dept)
                db.session.add(s)
                count += 1
                added.add(key)
    db.session.commit()
    return f"Done! Added {count} sales people. <a href='/sales'>View Sales</a> | <a href='/'>Home</a>"


# ==================== 初始化管理员账号 ====================

@app.route("/init_admin")
def init_admin():
    if User.query.filter_by(username="admin").first():
        return "管理员账号已存在！<a href='/login'>去登录</a>"
    admin = User(username="admin", display_name="管理员", is_admin=True)
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    return "管理员账号创建成功！<br>用户名：admin<br>密码：admin123<br><a href='/login'>去登录</a>"


# ==================== 百度OCR接口 ====================

def get_baidu_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": app.config.get("BAIDU_OCR_API_KEY", ""),
        "client_secret": app.config.get("BAIDU_OCR_SECRET_KEY", "")
    }
    resp = http_requests.post(url, params=params)
    return resp.json().get("access_token")


@app.route("/ocr", methods=["POST"])
@login_required
def ocr_recognize():
    file = request.files.get("image")
    if not file:
        return {"success": False, "error": "没有上传图片"}
    try:
        img_data = base64.b64encode(file.read()).decode("utf-8")
        token = get_baidu_token()
        url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={token}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"image": img_data, "language_type": "CHN_ENG"}
        resp = http_requests.post(url, headers=headers, data=data)
        result = resp.json()
        if "words_result" in result:
            lines = [item["words"] for item in result["words_result"]]
            text = " ".join(lines)
            return {"success": True, "text": text}
        else:
            return {"success": False, "error": result.get("error_msg", "识别失败")}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 9999))
    app.run(debug=False, host="0.0.0.0", port=port)
