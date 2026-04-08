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

        # All Residents
        cur.execute("SELECT resident_id, name, room_number, admission_date, emergency_contact FROM resident WHERE status = 'Active' ORDER BY name")
        residents = cur.fetchall()

        # All Visitors
        cur.execute("SELECT visitor_id, name, phone, relation FROM visitor ORDER BY name")
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
