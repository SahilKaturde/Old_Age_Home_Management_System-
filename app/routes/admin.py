from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from config import Config
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def login_required_admin(f):
    """Decorator to ensure only logged-in admins can access routes."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Please login as an admin.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/dashboard')
@login_required_admin
def dashboard():
    admin_id = session['user_id']
    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        # Resident Count
        cur.execute("SELECT COUNT(*) FROM resident WHERE status = 'Active'")
        total_residents = cur.fetchone()[0]

        # Visitor Count
        cur.execute("SELECT COUNT(*) FROM visitor")
        total_visitors = cur.fetchone()[0]

        # Pending Requests Count
        cur.execute("SELECT COUNT(*) FROM visit_request WHERE status = 'Pending'")
        pending_requests_count = cur.fetchone()[0]

        # All Residents (expanded fields for CRUD)
        cur.execute("""
            SELECT resident_id, name, email, phone, dob, gender, 
                   room_number, admission_date, emergency_contact, status, leave_date
            FROM resident 
            ORDER BY name
        """)
        residents = cur.fetchall()

        # All Visitors (expanded fields for CRUD)
        cur.execute("SELECT visitor_id, name, email, phone, relation FROM visitor ORDER BY name")
        visitors = cur.fetchall()

        # Pending Visit Requests
        cur.execute("""
            SELECT vr.request_id, v.name AS visitor_name, r.name AS resident_name, vr.requested_datetime, vr.purpose
            FROM visit_request vr
            JOIN visitor v ON vr.visitor_id = v.visitor_id
            JOIN resident r ON vr.resident_id = r.resident_id
            WHERE vr.status = 'Pending'
            ORDER BY vr.requested_datetime ASC
        """)
        pending_requests = cur.fetchall()

    except Exception as e:
        flash(f'Error loading admin dashboard: {str(e)}', 'error')
        total_residents = 0
        total_visitors = 0
        pending_requests_count = 0
        residents = []
        visitors = []
        pending_requests = []
    finally:
        cur.close()
        conn.close()

    return render_template('admin_dashboard.html',
                           total_residents=total_residents,
                           total_visitors=total_visitors,
                           pending_requests_count=pending_requests_count,
                           residents=residents,
                           visitors=visitors,
                           pending_requests=pending_requests)


@admin_bp.route('/approve_visit/<int:request_id>', methods=['POST'])
@login_required_admin
def approve_visit(request_id):
    admin_id = session['user_id']
    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        now = datetime.now()
        cur.execute("""
            UPDATE visit_request 
            SET status = 'Approved', approved_by = %s, approved_at = %s 
            WHERE request_id = %s
        """, (admin_id, now, request_id))
        conn.commit()
        flash('Visit request approved successfully.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error approving request: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/reject_visit/<int:request_id>', methods=['POST'])
@login_required_admin
def reject_visit(request_id):
    admin_id = session['user_id']
    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        now = datetime.now()
        cur.execute("""
            UPDATE visit_request 
            SET status = 'Rejected', approved_by = %s, approved_at = %s 
            WHERE request_id = %s
        """, (admin_id, now, request_id))
        conn.commit()
        flash('Visit request rejected.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error rejecting request: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin.dashboard'))


# ============================================
#  RESIDENT CRUD
# ============================================

@admin_bp.route('/add_resident', methods=['POST'])
@login_required_admin
def add_resident():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    phone = request.form.get('phone') or None
    dob = request.form.get('dob') or None
    gender = request.form.get('gender') or None
    room_number = request.form.get('room_number') or None
    emergency_contact = request.form.get('emergency_contact') or None

    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO resident (name, email, password, phone, dob, gender, room_number, emergency_contact)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, email, password, phone, dob, gender, room_number, emergency_contact))
        conn.commit()
        flash('Resident added successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Failed to add resident: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/edit_resident/<int:resident_id>', methods=['POST'])
@login_required_admin
def edit_resident(resident_id):
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone') or None
    dob = request.form.get('dob') or None
    gender = request.form.get('gender') or None
    room_number = request.form.get('room_number') or None
    emergency_contact = request.form.get('emergency_contact') or None
    status = request.form.get('status', 'Active')
    leave_date = request.form.get('leave_date') or None

    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE resident 
            SET name = %s, email = %s, phone = %s, dob = %s, gender = %s,
                room_number = %s, emergency_contact = %s, status = %s, leave_date = %s
            WHERE resident_id = %s
        """, (name, email, phone, dob, gender, room_number, emergency_contact, status, leave_date, resident_id))
        conn.commit()
        flash('Resident updated successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Failed to update resident: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/delete_resident/<int:resident_id>', methods=['POST'])
@login_required_admin
def delete_resident(resident_id):
    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM resident WHERE resident_id = %s", (resident_id,))
        conn.commit()
        flash('Resident deleted successfully.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Failed to delete resident: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin.dashboard'))


# ============================================
#  VISITOR CRUD
# ============================================

@admin_bp.route('/add_visitor', methods=['POST'])
@login_required_admin
def add_visitor():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    phone = request.form.get('phone') or None
    relation = request.form.get('relation') or None

    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO visitor (name, email, password, phone, relation)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, email, password, phone, relation))
        conn.commit()
        flash('Visitor added successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Failed to add visitor: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/edit_visitor/<int:visitor_id>', methods=['POST'])
@login_required_admin
def edit_visitor(visitor_id):
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone') or None
    relation = request.form.get('relation') or None

    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE visitor 
            SET name = %s, email = %s, phone = %s, relation = %s
            WHERE visitor_id = %s
        """, (name, email, phone, relation, visitor_id))
        conn.commit()
        flash('Visitor updated successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Failed to update visitor: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/delete_visitor/<int:visitor_id>', methods=['POST'])
@login_required_admin
def delete_visitor(visitor_id):
    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM visitor WHERE visitor_id = %s", (visitor_id,))
        conn.commit()
        flash('Visitor deleted successfully.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Failed to delete visitor: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin.dashboard'))


# ============================================
#  MEDICINE & REPORT APIs
# ============================================

@admin_bp.route('/api/resident_medicines/<int:resident_id>', methods=['GET'])
@login_required_admin
def get_resident_medicines(resident_id):
    conn = Config.get_db_connection()
    cur = conn.cursor()
    medicines = []
    try:
        cur.execute("""
            SELECT medicine_name, dosage, frequency, reminder_time 
            FROM medicine_schedule 
            WHERE resident_id = %s AND is_active = TRUE
            ORDER BY reminder_time
        """, (resident_id,))
        rows = cur.fetchall()
        for row in rows:
            # Need to format time to string for JSON serialization
            rem_time = row[3].strftime('%H:%M:%S') if row[3] else None
            medicines.append({
                'medicine_name': row[0],
                'dosage': row[1],
                'frequency': row[2],
                'reminder_time': rem_time
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()
        
    return jsonify(medicines)


@admin_bp.route('/api/annual_report', methods=['GET'])
@login_required_admin
def annual_report():
    """Returns all residents with their joining date, leave date, status, and medicine history."""
    conn = Config.get_db_connection()
    cur = conn.cursor()
    report = []

    try:
        # Get all residents (both active and inactive)
        cur.execute("""
            SELECT resident_id, name, room_number, admission_date, leave_date, status, 
                   phone, emergency_contact, gender, dob
            FROM resident 
            ORDER BY name
        """)
        residents = cur.fetchall()

        for res in residents:
            resident_id = res[0]

            # Get all medicines (active and inactive) for this resident
            cur.execute("""
                SELECT medicine_name, dosage, frequency, reminder_time, start_date, end_date, is_active
                FROM medicine_schedule 
                WHERE resident_id = %s
                ORDER BY is_active DESC, start_date DESC
            """, (resident_id,))
            meds = cur.fetchall()

            medicine_list = []
            for med in meds:
                rem_time = med[3].strftime('%H:%M') if med[3] else None
                medicine_list.append({
                    'medicine_name': med[0],
                    'dosage': med[1],
                    'frequency': med[2],
                    'reminder_time': rem_time,
                    'start_date': med[4].strftime('%d %b %Y') if med[4] else None,
                    'end_date': med[5].strftime('%d %b %Y') if med[5] else None,
                    'is_active': med[6]
                })

            report.append({
                'resident_id': resident_id,
                'name': res[1],
                'room_number': res[2] or '—',
                'admission_date': res[3].strftime('%d %b %Y') if res[3] else '—',
                'leave_date': res[4].strftime('%d %b %Y') if res[4] else '—',
                'status': res[5] or 'Active',
                'phone': res[6] or '—',
                'emergency_contact': res[7] or '—',
                'gender': res[8] or '—',
                'dob': res[9].strftime('%d %b %Y') if res[9] else '—',
                'medicines': medicine_list
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

    return jsonify(report)
