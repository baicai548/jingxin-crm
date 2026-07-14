#!/usr/bin/env bash
python -c "
from app import app, db
from models import User, SalesPerson

with app.app_context():
    db.create_all()
    print('Tables ready!')

    # 自动创建管理员（如果不存在）
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', display_name='管理员', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print('Admin created: admin/admin')
    else:
        print('Admin already exists')

    # 自动初始化销售（如果没有销售数据）
    if SalesPerson.query.count() == 0:
        from models import SALES_MAP, REGION_MAPPING
        count = 0
        added = set()
        def get_region(prov):
            for r, ps in REGION_MAPPING.items():
                if prov in ps:
                    return r
            return '其他'
        for prov, depts in SALES_MAP.items():
            for dept, name in depts.items():
                key = f'{name}_{dept}'
                if key not in added:
                    region = get_region(prov)
                    s = SalesPerson(name=name, phone='', region=region, department=dept)
                    db.session.add(s)
                    count += 1
                    added.add(key)
        db.session.commit()
        print(f'Sales initialized: {count} people')
    else:
        print('Sales data already exists')
"
gunicorn app:app --bind 0.0.0.0:$PORT
