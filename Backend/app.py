from flask import Flask, render_template, request, redirect, url_for, session, flash
import logic
import os
from functools import wraps # Import wraps for decorators

# --- Flask App Setup ---
app = Flask(__name__)
# SECRET_KEY is crucial for session security. Use a strong, random key.
# Keep this key secret in production (e.g., use environment variables).
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24)) 


# --- Decorators for Route Protection ---

def login_required(f):
    """Decorator to ensure a user or organization is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'entity_type' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def user_login_required(f):
    """Decorator to ensure a standard user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('entity_type') != 'user':
            flash("You must be logged in as a user to perform this action.", "error")
            # Redirect to login or index depending on preference
            return redirect(url_for('login')) 
        return f(*args, **kwargs)
    return decorated_function

def org_login_required(f):
    """Decorator to ensure an organization is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('entity_type') != 'organization':
            flash("You must be logged in as an organization to perform this action.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper removed: get_session_context() is no longer needed.
# Templates will now access session data directly via the 'session' object.


# --- Template Context Processor ---
# This makes the 'session' object available in all templates automatically.
@app.context_processor
def inject_session():
    return dict(session=session)


# --- Basic Routes ---

@app.route('/')
def index():
    """Render the main page."""
    # No longer passing current_session manually, handled by context processor.
    return render_template('index.html')

# --- Authentication Routes ---

@app.route('/register/user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        # Extract data from form
        name = request.form.get('name')
        email = request.form.get('email')
        student_code = request.form.get('student_code')
        password = request.form.get('password')
        interests = request.form.get('interests')
        career = request.form.get('career')

        # Call logic function (unchanged)
        result = logic.register_user(name, email, student_code, password, interests, career)

        flash(result['message'], result['status'])
        if result['status'] == 'success':
            return redirect(url_for('login'))
        else:
            return redirect(url_for('register_user'))

    # For GET request, just show the registration form
    # No longer passing current_session manually
    return render_template('register_user.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to index
    if 'entity_type' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        identifier = request.form.get('identifier') 
        password = request.form.get('password')

        # logic.login now just authenticates and returns data or error
        result = logic.login(identifier, password)

        if result['status'] == 'success':
            # --- Store relevant info in Flask session --- 
            # Clear any old session data first
            session.clear()
            # Store common fields
            session['entity_type'] = result['entity_type']
            session['name'] = result['name']
            session['email'] = result['email']
            session['points'] = result.get('points', 0) # Default points to 0 if missing
            # Store type-specific ID
            if result['entity_type'] == 'user':
                session['user_id'] = result['user_id']
                session['student_code'] = result['student_code']
            elif result['entity_type'] == 'organization':
                session['org_id'] = result['org_id']
            
            # Optionally store other non-sensitive data if needed frequently
            # session['interests'] = result.get('interests')

            flash(f"Login successful for {session['name']}!", 'success')
            return redirect(url_for('index'))
        else:
            # Login failed, flash the error message from logic
            flash(result['message'], result['status'])
            return redirect(url_for('login'))

    # Show login form for GET request
    # No longer passing current_session manually
    return render_template('login.html')

@app.route('/logout')
def logout():
    # logic.logout() is now just a placeholder
    # Clear the Flask session
    session.clear()
    flash("You have been successfully logged out.", 'success')
    return redirect(url_for('index'))

# --- Organization Registration ---
@app.route('/register/org', methods=['GET', 'POST'])
@user_login_required # Use decorator to ensure a user is logged in
def register_org():
    # Decorator handles the check if a user is logged in.
    # We still need the creator's student code from the session.
    creator_student_code = session.get('student_code')
    if not creator_student_code:
        # This should ideally not happen if user_login_required worked, but safety check
        flash("Could not identify logged-in user.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        description = request.form.get('description')
        password = request.form.get('password')
        interests = request.form.get('interests')

        # Pass creator_student_code explicitly to the refactored logic function
        result = logic.register_organization(creator_student_code, name, email, description, password, interests)

        flash(result['message'], result['status'])
        if result['status'] == 'success':
            return redirect(url_for('index'))
        else:
            return redirect(url_for('register_org'))

    # GET request: Show the form
    # No longer passing current_session manually
    return render_template('register_org.html')

# --- Event Routes ---
@app.route('/event/create', methods=['GET', 'POST'])
@login_required # Requires login (user or org)
def create_event():
    # Decorator ensures login.
    # Get organizer details from session.
    organizer_id = session.get('user_id') or session.get('org_id')
    organizer_type = session.get('entity_type')

    if not organizer_id or not organizer_type:
         flash("Could not identify organizer details from session.", "error")
         return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_datetime = request.form.get('event_datetime')
        location = request.form.get('location')
        event_type = request.form.get('event_type')

        # Pass organizer details to the refactored logic function
        result = logic.create_event_logic(
            organizer_id, organizer_type, title, description, 
            event_datetime, location, event_type
        )

        flash(result['message'], result['status'])
        # Consider redirecting to the event view page if one exists
        return redirect(url_for('index'))

    # GET request: Show the form
    # No longer passing current_session manually
    return render_template('create_event.html')

@app.route('/event/participants/<int:event_id>')
@login_required # Login required to view participants
def view_event_participants(event_id):
    """
    Show participants for an event. This route will be used for attendance marking.
    Only accessible to event organizers and admins.
    """
    entity_id = session.get('user_id') or session.get('org_id')
    entity_type = session.get('entity_type')
    
    if not entity_id or not entity_type:
        flash("Could not identify your session.", "error")
        return redirect(url_for('view_events'))
    
    # Get participants from logic layer
    result = logic.get_event_participants_logic(event_id)
    
    if result['status'] != 'success':
        flash(result['message'], result['status'])
        return redirect(url_for('view_events'))
    
    participants = result['data']
    
    # Check if current user is the event organizer (simplified - real check should be in logic layer)
    # In a real implementation, this check should include admin privileges too
    is_organizer = False
    event_details = None
    
    # Get event details
    events_result = logic.view_all_events_logic()
    if events_result['status'] == 'success':
        for event in events_result['data']:
            if event['event_id'] == event_id:
                event_details = event
                
                # Check if current user is organizer
                if ((event['organizer_type'] == entity_type or 
                    (event['organizer_type'] == 'org' and entity_type == 'organization')) and
                    event['organizer_id'] == entity_id):
                    is_organizer = True
                break
    
    if not event_details:
        flash("Event not found.", "error")
        return redirect(url_for('view_events'))
    
    return render_template('event_participants.html', 
                           event_id=event_id,
                           event=event_details,
                           participants=participants,
                           is_organizer=is_organizer)

@app.route('/event/mark_attendance', methods=['POST'])
@login_required # Login required to mark attendance
def mark_attendance():
    """
    Mark attendance for a participant.
    Only accessible to event organizers and admins.
    """
    marker_id = session.get('user_id') or session.get('org_id')
    marker_type = session.get('entity_type')
    
    if not marker_id or not marker_type:
        flash("Could not identify your session.", "error")
        return redirect(url_for('view_events'))
    
    event_id = request.form.get('event_id')
    participant_id = request.form.get('participant_id')
    participant_type = request.form.get('participant_type')
    
    if not event_id or not participant_id or not participant_type:
        flash("Missing required information to mark attendance.", "error")
        return redirect(url_for('view_event_participants', event_id=event_id))
    
    # Convert string values to integers
    try:
        event_id = int(event_id)
        participant_id = int(participant_id)
    except ValueError:
        flash("Invalid event or participant ID.", "error")
        return redirect(url_for('view_events'))
    
    result = logic.mark_event_attendance_logic(
        marker_id, marker_type, event_id, participant_id, participant_type
    )
    
    flash(result['message'], result['status'])
    return redirect(url_for('view_event_participants', event_id=event_id))

# --- Item Exchange Routes ---
@app.route('/item/add', methods=['GET', 'POST'])
@user_login_required # Only users can add items
def add_item():
    # Decorator ensures user login.
    owner_id = session.get('user_id') # Get owner ID from session
    if not owner_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        item_type = request.form.get('item_type')
        item_terms = request.form.get('item_terms')

        # Pass owner_id to the refactored logic function
        result = logic.add_item_for_exchange_logic(owner_id, name, description, item_type, item_terms)

        flash(result['message'], result['status'])
        if result['status'] == 'success':
             # --- Update points in session if needed --- 
             # Check if points were awarded (depends on award_points_logic response format)
             # Simplified: Re-fetch user data to get latest points
             # Note: This is inefficient. award_points_logic could return the delta or new total. 
             # Or, we could increment points in session directly if logic guarantees DB success.
             user_data = logic.view_my_points_and_badges_logic(owner_id)
             if user_data['status'] == 'success':
                 session['points'] = user_data['data'].get('points', session.get('points')) # Update session points
                 session.modified = True # Required when modifying mutable session objects

        return redirect(url_for('index'))

    # GET request: Show the form
    # No longer passing current_session manually
    return render_template('add_item.html')

# --- Viewing Routes ---
@app.route('/events')
def view_events():
    # No login required to view events
    result = logic.view_all_events_logic()
    
    events_list = []
    if result['status'] == 'success':
        events_list = result['data']
    else:
        flash(result['message'], result['status'])
    
    # No longer passing current_session manually
    return render_template('view_events.html', events=events_list)

@app.route('/items')
def view_items():
    # No login required to view items
    result = logic.view_exchange_items_logic()
    
    items_list = []
    if result['status'] == 'success':
        items_list = result['data']
    else:
        flash(result['message'], result['status'])
    
    # No longer passing current_session manually
    return render_template('view_items.html', items=items_list)

@app.route('/profile')
@login_required # Must be logged in to view profile
def profile():
    # Decorator ensures login.
    # The session object is automatically available in the template via context processor
    # No need to pass it explicitly anymore.
    # However, if you need complex data not in session, fetch it here.
    # Example: Fetching badges (assuming view_my_points_and_badges_logic exists)
    badges = []
    if session['entity_type'] == 'user':
        user_id = session['user_id']
        profile_data = logic.view_my_points_and_badges_logic(user_id)
        if profile_data['status'] == 'success':
            badges = profile_data['data'].get('achievements', [])
        else:
            flash("Could not load badge information.", "warning")
            
    # Pass specific extra data if needed, session is already available.
    return render_template('profile.html', badges=badges)

# --- Action Routes (POST requests often) ---

@app.route('/event/register/<int:event_id>', methods=['POST'])
@user_login_required # Only users can register for events
def register_for_event(event_id):
    # Decorator ensures user login.
    user_id = session.get('user_id')
    if not user_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('login'))

    # Pass user_id to the refactored logic function
    result = logic.register_for_event_logic(user_id, event_id)
    flash(result['message'], result['status'])

    if result['status'] == 'success':
         # --- Update points in session --- 
         # Similar to add_item, re-fetch points or increment based on logic guarantees
         user_data = logic.view_my_points_and_badges_logic(user_id)
         if user_data['status'] == 'success':
             session['points'] = user_data['data'].get('points', session.get('points'))
             session.modified = True

    # Redirect back to the events list
    return redirect(url_for('view_events'))

@app.route('/item/request/<int:item_id>', methods=['POST'])
@user_login_required # Only users can request items
def request_exchange(item_id):
    """Handles a user requesting to exchange an item."""
    requester_id = session.get('user_id')
    if not requester_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('login'))

    # Optional: Get message from form if you add a message field
    message = request.form.get('message', "") 

    # Call the logic function
    result = logic.request_exchange_logic(requester_id, item_id, message)
    flash(result['message'], result['status'])

    # Redirect back to the items list (or item detail page if you have one)
    return redirect(url_for('view_items'))

@app.route('/item/delete/<int:item_id>', methods=['POST'])
@user_login_required # Only users can delete their items
def delete_my_item(item_id):
    """Handles a user deleting their own item."""
    user_id = session.get('user_id')
    if not user_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('login'))

    # Call the logic function to delete the item
    result = logic.delete_my_item_logic(user_id, item_id)
    flash(result['message'], result['status'])

    # Redirect back to the items list or profile page
    return redirect(url_for('view_items'))

# --- Example: Update Profile Route (Needs Implementation) ---
# @app.route('/profile/update', methods=['POST'])
# @login_required
# def update_profile():
#     entity_id = session.get('user_id') or session.get('org_id')
#     entity_type = session.get('entity_type')
#     if not entity_id or not entity_type:
#         flash("Session error.", "error")
#         return redirect(url_for('profile'))
     
#     # Extract allowed fields from request.form
#     new_data = {}
#     allowed_fields = ['name', 'email', 'interests', 'career', 'description'] # Adjust per entity type
#     for field in allowed_fields:
#         if field in request.form:
#             new_data[field] = request.form[field]

#     if not new_data:
#         flash("No data provided for update.", "info")
#         return redirect(url_for('profile'))

#     result = logic.update_my_profile_logic(entity_id, entity_type, new_data)
#     flash(result['message'], result['status'])

#     if result['status'] == 'success':
#         # Update session if name/email changed
#         if 'name' in new_data: session['name'] = new_data['name']
#         if 'email' in new_data: session['email'] = new_data['email']
#         session.modified = True

#     return redirect(url_for('profile'))


# --- Placeholder for other routes ---
# TODO: Update other routes (item requests, org join/leave, etc.) 
#       to use decorators and pass session data (entity_id, entity_type) 
#       to their respective refactored logic functions.

@app.route('/profile/exchange_requests')
@user_login_required # Only users have exchange requests
def view_my_requests():
    user_id = session.get('user_id')
    if not user_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('login'))

    # Get received requests by default
    received_result = logic.view_my_exchange_requests_logic(user_id, request_type='received')
    sent_result = logic.view_my_exchange_requests_logic(user_id, request_type='sent')

    received_requests = []
    sent_requests = []
    if received_result['status'] == 'success':
        received_requests = received_result['data']
    else:
        flash(f"Error loading received requests: {received_result['message']}", "error")

    if sent_result['status'] == 'success':
        sent_requests = sent_result['data']
    else:
         flash(f"Error loading sent requests: {sent_result['message']}", "error")

    return render_template('view_exchange_requests.html',
                           received_requests=received_requests,
                           sent_requests=sent_requests)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 