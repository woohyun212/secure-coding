# product.py
import uuid
import os
from flask import Blueprint, render_template, redirect, url_for, session, flash, current_app, request
from werkzeug.utils import secure_filename
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
        # Handle image upload
        image_file = form.image.data
        image_url = None
        if image_file:
            # Generate a unique filename using UUID and preserve extension
            ext = os.path.splitext(image_file.filename)[1]
            filename = f"{uuid.uuid4().hex}{ext}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image_file.save(upload_path)
            image_url = filename

        db = get_db()
        cursor = db.cursor()
        product_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO product (id, title, description, price, seller_id, image_url) VALUES (?, ?, ?, ?, ?, ?)",
            (product_id, form.title.data, form.description.data, int(form.price.data), session['user_id'], image_url)
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

    existing_image = product_data.get('image_url')

    # Pre-populate form
    form = ProductForm(data={
        'title': product_data['title'],
        'description': product_data['description'],
        'price': product_data['price']
    })

    if form.validate_on_submit():
        # Handle new image upload
        image_file = form.image.data
        image_url = existing_image
        if image_file:
            # Generate a unique filename using UUID and preserve extension
            ext = os.path.splitext(image_file.filename)[1]
            filename = f"{uuid.uuid4().hex}{ext}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image_file.save(upload_path)
            image_url = filename

        cursor.execute(
            "UPDATE product SET title = ?, description = ?, price = ?, image_url = ? WHERE id = ?",
            (form.title.data, form.description.data, int(form.price.data), image_url, product_id)
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

    # Delete image file from server
    image_url = product_data['image_url']
    if image_url:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_url)
        try:
            os.remove(file_path)
        except OSError:
            pass
    # Delete the product
    cursor.execute("DELETE FROM product WHERE id = ?", (product_id,))
    db.commit()
    flash('상품이 삭제되었습니다.', 'success')
    return redirect(url_for('user.dashboard'))
