from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from config import Config
from datetime import date, datetime

resident_bp = Blueprint('resident', __name__, url_prefix='/resident')


def login_required_resident(f):
    """Decorator to ensure only logged-in residents can access routes."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'resident':
            flash('Please login as a resident.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@resident_bp.route('/dashboard')
@login_required_resident
def dashboard():
    resident_id = session['user_id']
    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        # Resident info (room number)
        cur.execute("SELECT room_number FROM resident WHERE resident_id = %s", (resident_id,))
        room_row = cur.fetchone()
        room_number = room_row[0] if room_row else '—'

        # Active medicines count
        cur.execute(
            "SELECT COUNT(*) FROM medicine_schedule WHERE resident_id = %s AND is_active = TRUE",
            (resident_id,)
        )
        active_medicines = cur.fetchone()[0]

        # Today's reminders
        cur.execute(
            """SELECT COUNT(*) FROM medicine_schedule 
               WHERE resident_id = %s AND is_active = TRUE
               AND (end_date IS NULL OR end_date >= CURRENT_DATE)""",
            (resident_id,)
        )
        todays_reminders = cur.fetchone()[0]

        # Upcoming approved visits count
        cur.execute(
            """SELECT COUNT(*) FROM visit_request 
               WHERE resident_id = %s AND status = 'Approved' 
               AND requested_datetime >= NOW()""",
            (resident_id,)
        )
        upcoming_visits = cur.fetchone()[0]

        # Medicine list (active)
        cur.execute(
            """SELECT medicine_id, medicine_name, dosage, frequency, reminder_time, start_date, end_date
               FROM medicine_schedule 
               WHERE resident_id = %s AND is_active = TRUE
               ORDER BY reminder_time""",
            (resident_id,)
        )
        medicines = cur.fetchall()

        # Upcoming visits detail
        cur.execute(
            """SELECT v.name, vr.requested_datetime, vr.purpose
               FROM visit_request vr
               JOIN visitor v ON v.visitor_id = vr.visitor_id
               WHERE vr.resident_id = %s AND vr.status = 'Approved'
               AND vr.requested_datetime >= NOW()
               ORDER BY vr.requested_datetime""",
            (resident_id,)
        )
        visits = cur.fetchall()

    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        active_medicines = 0
        todays_reminders = 0
        upcoming_visits = 0
        medicines = []
        visits = []
        room_number = '—'
    finally:
        cur.close()
        conn.close()

    return render_template('resident_dashboard.html',
        room_number=room_number,
        active_medicines=active_medicines,
        todays_reminders=todays_reminders,
        upcoming_visits=upcoming_visits,
        medicines=medicines,
        visits=visits
    )


@resident_bp.route('/medicines/add', methods=['POST'])
@login_required_resident
def add_medicine():
    resident_id = session['user_id']
    medicine_name = request.form.get('medicine_name')
    dosage = request.form.get('dosage')
    frequency = request.form.get('frequency')
    reminder_time = request.form.get('reminder_time')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date') or None

    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """INSERT INTO medicine_schedule 
               (resident_id, medicine_name, dosage, frequency, reminder_time, start_date, end_date)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (resident_id, medicine_name, dosage, frequency, reminder_time, start_date, end_date)
        )
        conn.commit()
        flash('Medicine added successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Failed to add medicine: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('resident.dashboard'))


@resident_bp.route('/medicines/take/<int:medicine_id>', methods=['POST'])
@login_required_resident
def take_medicine(medicine_id):
    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        # Verify this medicine belongs to the logged-in resident
        cur.execute(
            "SELECT resident_id FROM medicine_schedule WHERE medicine_id = %s",
            (medicine_id,)
        )
        row = cur.fetchone()
        if not row or row[0] != session['user_id']:
            flash('Medicine not found.', 'error')
            return redirect(url_for('resident.dashboard'))

        now = datetime.now()
        cur.execute(
            """INSERT INTO medicine_log (medicine_id, taken_date, taken_time, is_taken)
               VALUES (%s, %s, %s, TRUE)""",
            (medicine_id, now.date(), now.time())
        )
        conn.commit()
        flash('Medicine marked as taken! ✓', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('resident.dashboard'))
