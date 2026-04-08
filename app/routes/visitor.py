from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from config import Config

visitor_bp = Blueprint('visitor', __name__, url_prefix='/visitor')


def login_required_visitor(f):
    """Decorator to ensure only logged-in visitors can access routes."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'visitor':
            flash('Please login as a visitor.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@visitor_bp.route('/dashboard')
@login_required_visitor
def dashboard():
    visitor_id = session['user_id']
    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        # Request counts
        cur.execute(
            "SELECT COUNT(*) FROM visit_request WHERE visitor_id = %s",
            (visitor_id,)
        )
        total_requests = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM visit_request WHERE visitor_id = %s AND status = 'Pending'",
            (visitor_id,)
        )
        pending = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM visit_request WHERE visitor_id = %s AND status = 'Approved'",
            (visitor_id,)
        )
        approved = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM visit_request WHERE visitor_id = %s AND status = 'Rejected'",
            (visitor_id,)
        )
        rejected = cur.fetchone()[0]

        # My requests with resident names
        cur.execute(
            """SELECT vr.request_id, r.name, vr.requested_datetime, vr.purpose, vr.status, vr.created_at
               FROM visit_request vr
               JOIN resident r ON r.resident_id = vr.resident_id
               WHERE vr.visitor_id = %s
               ORDER BY vr.created_at DESC""",
            (visitor_id,)
        )
        my_requests = cur.fetchall()

    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        total_requests = 0
        pending = 0
        approved = 0
        rejected = 0
        my_requests = []
    finally:
        cur.close()
        conn.close()

    return render_template('visitor_dashboard.html',
        total_requests=total_requests,
        pending=pending,
        approved=approved,
        rejected=rejected,
        my_requests=my_requests,
        search_results=None,
        search_query=''
    )


@visitor_bp.route('/search', methods=['GET'])
@login_required_visitor
def search_resident():
    query = request.args.get('q', '').strip()
    visitor_id = session['user_id']
    search_results = []

    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        if query:
            cur.execute(
                """SELECT resident_id, name, room_number, gender 
                   FROM resident 
                   WHERE name ILIKE %s AND status = 'Active'
                   ORDER BY name""",
                (f'%{query}%',)
            )
            search_results = cur.fetchall()

        # Also load request counts and my_requests for the full page
        cur.execute(
            "SELECT COUNT(*) FROM visit_request WHERE visitor_id = %s", (visitor_id,)
        )
        total_requests = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM visit_request WHERE visitor_id = %s AND status = 'Pending'",
            (visitor_id,)
        )
        pending = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM visit_request WHERE visitor_id = %s AND status = 'Approved'",
            (visitor_id,)
        )
        approved = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM visit_request WHERE visitor_id = %s AND status = 'Rejected'",
            (visitor_id,)
        )
        rejected = cur.fetchone()[0]

        cur.execute(
            """SELECT vr.request_id, r.name, vr.requested_datetime, vr.purpose, vr.status, vr.created_at
               FROM visit_request vr
               JOIN resident r ON r.resident_id = vr.resident_id
               WHERE vr.visitor_id = %s
               ORDER BY vr.created_at DESC""",
            (visitor_id,)
        )
        my_requests = cur.fetchall()

    except Exception as e:
        flash(f'Search error: {str(e)}', 'error')
        total_requests = 0
        pending = 0
        approved = 0
        rejected = 0
        my_requests = []
    finally:
        cur.close()
        conn.close()

    return render_template('visitor_dashboard.html',
        total_requests=total_requests,
        pending=pending,
        approved=approved,
        rejected=rejected,
        my_requests=my_requests,
        search_results=search_results,
        search_query=query
    )


@visitor_bp.route('/request-visit', methods=['POST'])
@login_required_visitor
def request_visit():
    visitor_id = session['user_id']
    resident_id = request.form.get('resident_id')
    requested_datetime = request.form.get('requested_datetime')
    purpose = request.form.get('purpose', '')

    conn = Config.get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """INSERT INTO visit_request (visitor_id, resident_id, requested_datetime, purpose)
               VALUES (%s, %s, %s, %s)""",
            (visitor_id, resident_id, requested_datetime, purpose)
        )
        conn.commit()
        flash('Visit request sent successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Failed to send request: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('visitor.dashboard'))
