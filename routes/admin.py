# admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_db
from decorators import login_and_active_required, admin_required
import uuid
from forms import AdminUserForm

admin = Blueprint('admin', __name__, url_prefix='/admin')

# 사용자 관리 목록
@admin.route('/users')
@login_and_active_required
@admin_required
def manage_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user")
    users = cursor.fetchall()
    return render_template('admin/manage_users.html', users=users)

# 사용자 삭제
@admin.route('/users/delete/<user_id>', methods=['POST'])
@login_and_active_required
@admin_required
def delete_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
    db.commit()
    flash("사용자가 삭제되었습니다.", "success")
    return redirect(url_for('admin.manage_users'))

# 사용자 추가
@admin.route('/users/add', methods=['GET', 'POST'])
@login_and_active_required
@admin_required
def add_user():
    form = AdminUserForm()
    if form.validate_on_submit():
        db = get_db()
        cursor = db.cursor()
        user_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO user (id, username, password, bio, is_active, is_admin) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, form.username.data, form.password.data, form.bio.data, 1, 0)
        )
        db.commit()
        flash("사용자가 추가되었습니다.", "success")
        return redirect(url_for('admin.manage_users'))
    return render_template('admin/add_user.html', form=form)

# 사용자 수정
@admin.route('/users/edit/<user_id>', methods=['GET', 'POST'])
@login_and_active_required
@admin_required
def edit_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        flash("사용자를 찾을 수 없습니다.", "danger")
        return redirect(url_for('admin.manage_users'))

    form = AdminUserForm()
    if request.method == 'GET':
        form.username.data = user['username']
        form.bio.data = user['bio']
    elif request.method == 'POST':
        form.username.data = request.form.get('username', '').strip()
        form.bio.data = request.form.get('bio', '').strip()
        password = request.form.get('password', '').strip()

        # Validation: username required
        if not form.username.data:
            flash("사용자명은 필수 항목입니다.", "danger")
        elif password and len(password) < 8:
            flash("비밀번호는 8자 이상이어야 합니다.", "danger")
        else:
            if password:
                cursor.execute(
                    "UPDATE user SET username = ?, password = ?, bio = ? WHERE id = ?",
                    (form.username.data, password, form.bio.data, user_id)
                )
            else:
                cursor.execute(
                    "UPDATE user SET username = ?, bio = ? WHERE id = ?",
                    (form.username.data, form.bio.data, user_id)
                )
            db.commit()
            flash("사용자 정보가 수정되었습니다.", "success")
            return redirect(url_for('admin.manage_users'))

    return render_template('admin/edit_user.html', form=form, user=user)

# 상품 관리 목록
@admin.route('/products')
@login_and_active_required
@admin_required
def manage_products():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM product")
    products = cursor.fetchall()
    return render_template('admin/manage_products.html', products=products)

# 상품 삭제
@admin.route('/products/delete/<product_id>', methods=['POST'])
@login_and_active_required
@admin_required
def delete_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM product WHERE id = ?", (product_id,))
    db.commit()
    flash("상품이 삭제되었습니다.", "success")
    return redirect(url_for('admin.manage_products'))
