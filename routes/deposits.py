# routes/deposits.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, abort
from db import get_db
from decorators import login_and_active_required, admin_required
from forms import DepositRequestForm
import uuid

deposits = Blueprint('deposits', __name__, url_prefix='/deposits')

@deposits.route('/request', methods=['GET', 'POST'])
@login_and_active_required
def request_deposit():
    form = DepositRequestForm()
    if form.validate_on_submit():
        db = get_db()
        cursor = db.cursor()
        request_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO deposit_requests (id, user_id, amount) VALUES (?, ?, ?)",
            (request_id, session['user_id'], form.amount.data)
        )
        db.commit()
        flash('충전 요청이 접수되었습니다.', 'success')
        return redirect(url_for('deposits.my_requests'))
    return render_template('deposits/request.html', form=form)

@deposits.route('/my_requests')
@login_and_active_required
def my_requests():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, amount, timestamp, status FROM deposit_requests WHERE user_id = ? ORDER BY timestamp DESC",
        (session['user_id'],)
    )
    requests = cursor.fetchall()
    return render_template('deposits/my_requests.html', requests=requests)

@deposits.route('/admin')
@login_and_active_required
@admin_required
def admin_requests():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, user_id, amount, timestamp, status FROM deposit_requests ORDER BY timestamp DESC"
    )
    requests = cursor.fetchall()
    return render_template('admin/deposits.html', requests=requests)

@deposits.route('/admin/approve/<request_id>', methods=['POST'])
@login_and_active_required
@admin_required
def approve_request(request_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM deposit_requests WHERE id = ?", (request_id,))
    req = cursor.fetchone()
    if not req:
        flash('충전 요청을 찾을 수 없습니다.', 'danger')
        return redirect(url_for('deposits.admin_requests'))
    if req['status'] != 'pending':
        flash('이미 처리된 요청입니다.', 'warning')
        return redirect(url_for('deposits.admin_requests'))
    # Update request status
    cursor.execute("UPDATE deposit_requests SET status = 'approved' WHERE id = ?", (request_id,))
    # Credit user balance
    cursor.execute("UPDATE user SET balance = balance + ? WHERE id = ?", (req['amount'], req['user_id']))
    db.commit()
    flash('충전 요청이 승인되어 계정에 포인트가 충전되었습니다.', 'success')
    return redirect(url_for('deposits.admin_requests'))

@deposits.route('/admin/reject/<request_id>', methods=['POST'])
@login_and_active_required
@admin_required
def reject_request(request_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM deposit_requests WHERE id = ?", (request_id,))
    req = cursor.fetchone()
    if not req:
        flash('충전 요청을 찾을 수 없습니다.', 'danger')
        return redirect(url_for('deposits.admin_requests'))
    if req['status'] != 'pending':
        flash('이미 처리된 요청입니다.', 'warning')
        return redirect(url_for('deposits.admin_requests'))
    # Update request status
    cursor.execute("UPDATE deposit_requests SET status = 'rejected' WHERE id = ?", (request_id,))
    db.commit()
    flash('충전 요청이 거절되었습니다.', 'info')
    return redirect(url_for('deposits.admin_requests'))