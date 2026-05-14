# This script adds customer-only route to app.py
import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

new_route = '''
@app.route("/c", methods=["GET","POST"])
def customer_only():
    if request.method=="POST":
        fields = ["company_name","contact_name","phone","email","province","city","channel","product_interest","note"]
        d = {k:request.form.get(k,"").strip() for k in fields}
        if not all([d["company_name"],d["contact_name"],d["phone"],d["province"],d["channel"]]):
            flash("\\u8bf7\\u586b\\u5199\\u6240\\u6709\\u5fc5\\u586b\\u9879","error")
            return redirect(url_for("customer_only"))
        s = assign(d["province"])
        c = Customer(**{k:d[k] for k in fields}, assigned_to=s.id if s else None)
        db.session.add(c)
        db.session.commit()
        flash("\\u63d0\\u4ea4\\u6210\\u529f\\uff01\\u6211\\u4eec\\u4f1a\\u5c3d\\u5feb\\u8054\\u7cfb\\u60a8","success")
        return redirect(url_for("customer_only"))
    return render_template("customer_only.html",channels=CHANNELS,provinces=PROVINCES)

'''

# Insert before internal_add route
content = content.replace('@app.route("/internal/add"', new_route + '@app.route("/internal/add"')

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("[OK] Customer-only route added!")
print("Customer page: http://127.0.0.1:9999/c")