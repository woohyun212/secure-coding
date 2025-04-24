import uuid
from flask import Blueprint, render_template, redirect, url_for, session, flash
from forms import ProductForm
from db import get_db

# Blueprint for product-related routes
product = Blueprint('product', __name__, url_prefix='/product')

@product.route('/new', methods=['GET', 'POST'])
def new_product():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
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