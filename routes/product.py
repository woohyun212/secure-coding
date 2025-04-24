# product.py
import uuid
from flask import Blueprint, render_template, redirect, url_for, session, flash
from forms import ProductForm
from db import get_db
from decorators import login_and_active_required
from decorators import admin_required

# Blueprint for product-related routes
product = Blueprint('product', __name__, url_prefix='/product')

@login_and_active_required
@product.route('/new', methods=['GET', 'POST'])
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        db = get_db()
        cursor = db.cursor()
        product_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO product (id, title, description, price, seller_id) VALUES (?, ?, ?, ?, ?)",
            (product_id, form.title.data, form.description.data, form.price.data, session['user_id'])
        )
        db.commit()
        flash('상품이 등록되었습니다.', 'success')
        return redirect(url_for('user.dashboard'))
    return render_template('product/new_product.html', form=form)

@product.route('/<product_id>')
def view_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM product WHERE id = ?", (product_id,))
    product_data = cursor.fetchone()
    if not product_data:
        flash('상품을 찾을 수 없습니다.', 'danger')
        return redirect(url_for('user.dashboard'))
    cursor.execute("SELECT * FROM user WHERE id = ?", (product_data['seller_id'],))
    seller = cursor.fetchone()
    return render_template('product/view_product.html', product=product_data, seller=seller)

@login_and_active_required
@product.route('/edit/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    db = get_db()
    cursor = db.cursor()
    # Fetch product
    cursor.execute("SELECT * FROM product WHERE id = ?", (product_id,))
    product_data = cursor.fetchone()
    if not product_data:
        flash('상품을 찾을 수 없습니다.', 'danger')
        return redirect(url_for('user.dashboard'))
    if product_data['seller_id'] != session['user_id'] and not session.get('is_admin'):
        flash('수정 권한이 없습니다.', 'danger')
        return redirect(url_for('user.dashboard'))

    # Pre-populate form
    form = ProductForm(data={
        'title': product_data['title'],
        'description': product_data['description'],
        'price': product_data['price']
    })

    if form.validate_on_submit():
        cursor.execute(
            "UPDATE product SET title = ?, description = ?, price = ? WHERE id = ?",
            (form.title.data, form.description.data, form.price.data, product_id)
        )
        db.commit()
        flash('상품이 수정되었습니다.', 'success')
        return redirect(url_for('product.view_product', product_id=product_id))

    return render_template('product/edit_product.html', form=form, product=product_data)

@product.route('/delete/<product_id>', methods=['POST'])
@login_and_active_required
def delete_product(product_id):
    db = get_db()
    cursor = db.cursor()
    # Verify the product exists and belongs to the current user
    cursor.execute("SELECT * FROM product WHERE id = ?", (product_id,))
    product_data = cursor.fetchone()
    if not product_data:
        flash('상품을 찾을 수 없습니다.', 'danger')
        return redirect(url_for('user.dashboard'))
    if product_data['seller_id'] != session['user_id']:
        flash('삭제 권한이 없습니다.', 'danger')
        return redirect(url_for('user.dashboard'))

    # Delete the product
    cursor.execute("DELETE FROM product WHERE id = ?", (product_id,))
    db.commit()
    flash('상품이 삭제되었습니다.', 'success')
    return redirect(url_for('user.dashboard'))
