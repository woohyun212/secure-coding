import uuid
from flask import Blueprint, render_template, redirect, url_for, session, flash
from forms import ReportForm
from db import get_db

# Blueprint for report-related routes
report = Blueprint('report', __name__, url_prefix='/report')

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
