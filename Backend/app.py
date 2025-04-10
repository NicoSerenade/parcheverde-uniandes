from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import logic # Import your logic module
import os

# It's highly recommended to use Flask sessions for managing login state
# instead of the global variable in logic.py for any real application.
# However, for this simple testing setup, we'll proceed with the global variable,
# acknowledging its limitations (not suitable for concurrent users).

app = Flask(__name__)
# Secret key is needed for Flask session management (even if basic)
# You should set this to a random, secret value in a real app, possibly via environment variables
app.secret_key = os.urandom(24)

# --- Helper to get current session --- 
# This helps keep templates consistent
def get_session_context():
    return logic.get_current_session()

# --- Basic Routes ---

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html', current_session=get_session_context())

# --- Authentication Routes ---

@app.route('/register/user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        # Extract data from form
        name = request.form.get('name')
        email = request.form.get('email')
        student_code = request.form.get('student_code')
        password = request.form.get('password')
        interests = request.form.get('interests') # Optional
        career = request.form.get('career')       # Optional

        # Call logic function
        result = logic.register_user(name, email, student_code, password, interests, career)

        # Flash message and redirect
        flash(result['message'], result['status']) # status should be 'success', 'error', 'info'
        if result['status'] == 'success':
            return redirect(url_for('login')) # Redirect to login after successful registration
        else:
            return redirect(url_for('register_user')) # Stay on registration page on error

    # For GET request, just show the registration form
    return render_template('register_user.html', current_session=get_session_context())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier') # Can be student_code or org_name
        password = request.form.get('password')

        result = logic.login(identifier, password)

        flash(result.get('message', f"Login successful for {result.get('name')}"), result['status'])
        if result['status'] == 'success':
            # NOTE: Session state is managed by the global variable in logic.py
            # In a real app, you'd store session info here using flask.session
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))

    return render_template('login.html', current_session=get_session_context())

@app.route('/logout')
def logout():
    result = logic.logout()
    flash(result['message'], result['status'])
    # Session state (global var) is cleared in logic.logout()
    return redirect(url_for('index'))

# --- Organization Registration ---
@app.route('/register/org', methods=['GET', 'POST'])
def register_org():
    current_session = get_session_context()
    if not current_session or current_session.get('user_type') != 'user':
        flash("You must be logged in as a user to register an organization.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        description = request.form.get('description')
        password = request.form.get('password')
        interests = request.form.get('interests')

        # logic.register_organization uses the current_logged_in_entity global
        result = logic.register_organization(name, email, description, password, interests)

        flash(result['message'], result['status'])
        if result['status'] == 'success':
            return redirect(url_for('index')) # Or maybe profile page?
        else:
            return redirect(url_for('register_org'))

    return render_template('register_org.html', current_session=current_session)

# --- Event Routes ---
@app.route('/event/create', methods=['GET', 'POST'])
def create_event():
    current_session = get_session_context()
    if not current_session:
        flash("Please login to create an event.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_datetime = request.form.get('event_datetime') # HTML input type datetime-local
        location = request.form.get('location')
        event_type = request.form.get('event_type') # e.g., 'charla', 'voluntariado'

        # logic.create_event_logic uses the current_logged_in_entity global
        result = logic.create_event_logic(title, description, event_datetime, location, event_type)

        flash(result['message'], result['status'])
        return redirect(url_for('index')) # Redirect home after attempting creation

    return render_template('create_event.html', current_session=current_session)

# --- Item Exchange Routes ---
@app.route('/item/add', methods=['GET', 'POST'])
def add_item():
    current_session = get_session_context()
    if not current_session or current_session.get('user_type') != 'user':
        flash("You must be logged in as a user to add an item.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        item_type = request.form.get('item_type') # e.g., 'gift', 'exchange'
        item_terms = request.form.get('item_terms')

        # logic.add_item_for_exchange_logic uses the current_logged_in_entity global
        result = logic.add_item_for_exchange_logic(name, description, item_type, item_terms)

        flash(result['message'], result['status'])
        return redirect(url_for('index')) # Redirect home after attempting creation

    return render_template('add_item.html', current_session=current_session)

# --- Viewing Routes ---
@app.route('/events')
def view_events():
    # logic.view_all_events_logic() now returns the list directly
    events_list = logic.view_all_events_logic()
    return render_template('view_events.html', events=events_list, current_session=get_session_context())

@app.route('/items')
def view_items():
    # logic.view_exchange_items_logic() now returns the list directly
    items_list = logic.view_exchange_items_logic()
    return render_template('view_items.html', items=items_list, current_session=get_session_context())

@app.route('/profile')
def profile():
    current_session = get_session_context()
    if not current_session:
        flash("Please log in to view your profile.", "info")
        return redirect(url_for('login'))
    # Pass the whole session object to the template
    return render_template('profile.html', current_session=current_session)

# --- Action Routes (POST requests often) ---

@app.route('/event/register/<int:event_id>', methods=['POST'])
def register_for_event(event_id):
    current_session = get_session_context()
    if not current_session or current_session.get('user_type') != 'user':
        flash("You must be logged in as a user to register for events.", "error")
        return redirect(url_for('login'))

    # logic.register_for_event_logic uses the current_logged_in_entity global
    result = logic.register_for_event_logic(event_id)
    flash(result['message'], result['status'])

    # Redirect back to the events list or maybe the specific event page if you had one
    return redirect(url_for('view_events'))

# --- Placeholder for other routes ---
# We will add routes for events, items etc. later


if __name__ == '__main__':
    # Use 0.0.0.0 to make it accessible on your network if needed
    # Debug=True is helpful for development but should be False in production
    app.run(host='0.0.0.0', port=5000, debug=True) 