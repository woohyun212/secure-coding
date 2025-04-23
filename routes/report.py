from decorators import login_and_active_required, admin_required
import uuid
from flask import Blueprint, render_template, redirect, url_for, session, flash
from flask import request, abort
from forms import ReportForm
from db import get_db
from utils import get_username_by_id

# Blueprint for report-related routes
report = Blueprint('report', __name__, url_prefix='/report')

@report.route('/list')
@login_and_active_required
@admin_required
def report_list():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM report WHERE status = 'pending'")
    reports = cursor.fetchall()
    # Enrich with reporter and target usernames
    enriched = []
    for r in reports:
        reporter = get_username_by_id(r['reporter_id'])
        target = get_username_by_id(r['target_id'])
        enriched.append({
            'id': r['id'],
            'reporter': reporter,
            'target': target,
            'reason': r['reason']
        })
    return render_template('report_list.html', reports=enriched)

@report.route('/process/<report_id>', methods=['POST'])
@login_and_active_required
@admin_required
def process_report(report_id):
    db = get_db()
    cursor = db.cursor()
    # Fetch report
    cursor.execute("SELECT * FROM report WHERE id = ?", (report_id,))
    rpt = cursor.fetchone()
    if not rpt:
        flash('신고를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('report.report_list'))
    # Mark report as resolved
    cursor.execute("UPDATE report SET status = 'resolved' WHERE id = ?", (report_id,))
    # Suspend user or deactivate product
    target_id = rpt['target_id']
    # Check if target is user
    cursor.execute("SELECT id FROM user WHERE id = ?", (target_id,))
    if cursor.fetchone():
        cursor.execute("UPDATE user SET is_active = 0 WHERE id = ?", (target_id,))
        flash('신고된 사용자가 휴면 처리되었습니다.', 'success')
    else:
        cursor.execute("UPDATE product SET is_active = 0 WHERE id = ?", (target_id,))
        flash('신고된 상품이 비활성화되었습니다.', 'success')
    db.commit()
    return redirect(url_for('report.report_list'))

@report.route('/', methods=['GET', 'POST'])
def report_item():
    # Ensure user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    form = ReportForm()
    if form.validate_on_submit():
        db = get_db()
        cursor = db.cursor()
        report_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO report (id, reporter_id, target_id, reason) VALUES (?, ?, ?, ?)",
            (report_id, session['user_id'], form.target_id.data, form.reason.data)
        )
        db.commit()
        flash('신고가 접수되었습니다.', 'success')
        return redirect(url_for('user.dashboard'))
    return render_template('report.html', form=form)
