# routes/transactions.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from db import get_db
from decorators import login_and_active_required, admin_required
from forms import TransferForm
import uuid

transactions = Blueprint('transactions', __name__, url_prefix='/transactions')

@transactions.route('/transfer', methods=['GET', 'POST'])
@login_and_active_required
def transfer():
    form = TransferForm()
    # Fetch current user's balance
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT balance FROM user WHERE id = ?", (session['user_id'],))
    row = cursor.fetchone()
    balance = row['balance'] if row else 0
    if form.validate_on_submit():
        db = get_db()
        cursor = db.cursor()
        sender_id = session['user_id']
        recipient_id = form.recipient_id.data
        amount = form.amount.data

        # Validate recipient exists
        cursor.execute("SELECT id FROM user WHERE id = ?", (recipient_id,))
        if not cursor.fetchone():
            flash('수신인이 존재하지 않습니다.', 'danger')
            return redirect(url_for('transactions.transfer'))

        # Prevent sending to self
        if recipient_id == sender_id:
            flash('본인에게는 송금할 수 없습니다.', 'danger')
            return redirect(url_for('transactions.transfer'))

        # Check sender balance
        cursor.execute("SELECT balance FROM user WHERE id = ?", (sender_id,))
        sender = cursor.fetchone()
        if sender['balance'] < amount:
            flash('잔액이 부족합니다.', 'danger')
            return redirect(url_for('transactions.transfer'))

        # Perform atomic transfer
        cursor.execute("UPDATE user SET balance = balance - ? WHERE id = ?", (amount, sender_id))
        cursor.execute("UPDATE user SET balance = balance + ? WHERE id = ?", (amount, recipient_id))

        # Record transaction
        transaction_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO transactions (id, sender_id, recipient_id, amount, status) VALUES (?, ?, ?, ?, 'completed')",
            (transaction_id, sender_id, recipient_id, amount)
        )
        db.commit()

        flash('송금이 완료되었습니다.', 'success')
        return redirect(url_for('transactions.history'))

    return render_template('transactions/transfer.html', form=form, balance=balance)

@transactions.route('/history')
@login_and_active_required
def history():
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']

    # Fetch both transfers and deposits in one union query, ordered by timestamp
    cursor.execute("""
        SELECT
          CASE WHEN sender_id = ? THEN '송금' ELSE '입금' END AS type,
          id,
          sender_id,
          recipient_id,
          amount,
          timestamp,
          status
        FROM transactions
        WHERE sender_id = ? OR recipient_id = ?
        UNION ALL
        SELECT
          '충전' AS type,
          id,
          NULL AS sender_id,
          user_id AS recipient_id,
          amount,
          timestamp,
          status
        FROM deposit_requests
        WHERE user_id = ? AND status = 'approved'
        ORDER BY timestamp DESC
    """, (user_id, user_id, user_id, user_id))
    records = cursor.fetchall()
    return render_template('transactions/history.html', transactions=records)

@transactions.route('/all')
@login_and_active_required
@admin_required
def all_transactions():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id, sender_id, recipient_id, amount, timestamp, status
        FROM transactions
        ORDER BY timestamp DESC
        """
    )
    records = cursor.fetchall()
    return render_template('admin/transactions.html', transactions=records)