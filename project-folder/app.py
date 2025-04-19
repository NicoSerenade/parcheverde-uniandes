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


# --- Template Context Processor ---
# This makes the 'session' object available in all templates automatically.
@app.context_processor
def inject_session():
    return dict(session=session)


# --- Basic Routes ---

@app.route('/')
def index():
    """Render the main page."""
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
    return render_template('register_user.html')

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to index
    if 'entity_type' in session:
        if session['entity_type'] == 'admin':
            return redirect(url_for('admin_dashboard'))
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
            session['entity_id'] = result['entity_id']
            session['entity_type'] = result['entity_type']
            session['name'] = result['name']
            session['email'] = result['email']
            session['interests'] = result.get('interests', '')
            session['description'] = result.get('description', '')
            session['points'] = result.get('points', 0) 

            # If admin user, redirect to admin dashboard
            if result['entity_type'] == 'admin':
                flash(f"Admin login successful for {session['name']}!", 'success')
                return redirect(url_for('admin_dashboard'))
            
            # Store type-specific ID and data
            if result['entity_type'] == 'user':
                session['student_code'] = result['student_code']
                session['career'] = result.get('career', '')

            elif result['entity_type'] == 'org':
                session['creator_student_code'] = result['creator_student_code']
                
            flash(f"Login successful for {session['name']}!", 'success')
            return redirect(url_for('index'))
        else:
            # Login failed, flash the error message from logic
            flash(result['message'], result['status'])
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been successfully logged out.", 'success')
    return redirect(url_for('index'))


# --- Profile Routes ---
@app.route('/profile')
@login_required # Must be logged in to view profile
def profile():
    """
    View the user or organization profile based on the session data.
    """
    entity_id = None
    entity_type = session.get('entity_type')
    
    if entity_type == 'user':
        entity_id = session.get('entity_id')
        
        # Create initial user_data from session information
        user_data = {
            'name': session.get('name'),
            'email': session.get('email'),
            'student_code': session.get('student_code'),
            'career': session.get('career'),
            'interests': session.get('interests'),
            'points': session.get('points', 0)
        }
        
        # Get full user data from database for accurate information
        fresh_user_data = logic.get_entity_by_id(entity_id, entity_type)
        if fresh_user_data:
            # Update any missing fields with fresh data
            if not user_data['career'] or user_data['career'] == 'None':
                user_data['career'] = fresh_user_data.get('career', '')
            if not user_data['interests'] or user_data['interests'] == 'None':
                user_data['interests'] = fresh_user_data.get('interests', '')
            # Update session with fresh data to avoid this issue in the future
            session['career'] = fresh_user_data.get('career', '')
            session['interests'] = fresh_user_data.get('interests', '')
            session.modified = True
        

 
        
        # Get points and user orgs
        points = session.get('points', 0)
        user_orgs = []
        
        # Get achievements if available and add to badges
        badges = []
        result = logic.get_entity_achievements(entity_id, entity_type)
        if result['status'] == 'success' and 'data' in result:
            achievement_badges = result.get('data', [])
            # Add any additional badges to our list
            badges.extend(achievement_badges)
        
        # Get user organizations
        orgs_result = logic.get_user_orgs_logic(entity_id)
        if orgs_result['status'] == 'success':
            user_orgs = orgs_result['data']
        
        return render_template('profile.html', 
                              user_data=user_data,
                              points=points, 
                              badges=badges,
                              user_orgs=user_orgs)
        

    elif entity_type == 'organization':
        entity_id = session.get('org_id')
        
        # Create org_data from session information
        org_data = {
            'name': session.get('name'),
            'email': session.get('email'),
            'description': session.get('description'),
            'interests': session.get('interests'),
            'points': session.get('points', 0)
        }
        
        # Get org members if available
        members = []
        members_result = logic.get_org_members_logic(entity_id)
        if members_result['status'] == 'success':
            members = members_result['data']
        
        return render_template('profile.html', 
                              org_data=org_data,
                              members=members)
    
    else:
        # This should not happen due to the @login_required decorator
        flash("Unknown entity type.", "error")
        return redirect(url_for('index'))

@app.route('/profile/update', methods=['GET', 'POST'])
@login_required
def update_profile():
    """
    Allow users or organizations to update their profile information.
    """
    entity_id = session.get('entity_id') or session.get('org_id')
    entity_type = session.get('entity_type')
    
    if not entity_id or not entity_type:
        flash("Could not identify your session.", "error")
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        # Get form data
        new_data = {}
        
        if entity_type == 'user':
            # Fields for users
            if request.form.get('name'):
                new_data['name'] = request.form.get('name')
            if request.form.get('email'):
                new_data['email'] = request.form.get('email')
            if request.form.get('student_code'):
                new_data['student_code'] = request.form.get('student_code')
            if request.form.get('career'):
                new_data['career'] = request.form.get('career')
            if request.form.get('interests'):
                new_data['interests'] = request.form.get('interests')
        
        elif entity_type == 'organization':
            # Fields for organizations
            if request.form.get('name'):
                new_data['name'] = request.form.get('name')
            if request.form.get('email'):
                new_data['email'] = request.form.get('email')
            if request.form.get('description'):
                new_data['description'] = request.form.get('description')
            if request.form.get('interests'):
                new_data['interests'] = request.form.get('interests')
        
        # Update profile using logic function
        result = logic.update_my_profile_logic(entity_id, entity_type, new_data)
        flash(result['message'], result['status'])
        
        # Update session data if profile was updated successfully
        if result['status'] == 'success':
            if 'name' in new_data:
                session['name'] = new_data['name']
            if entity_type == 'user':
                if 'career' in new_data:
                    session['career'] = new_data['career']
                if 'interests' in new_data:
                    session['interests'] = new_data['interests']
            elif entity_type == 'organization':
                if 'description' in new_data:
                    session['description'] = new_data['description']
                if 'interests' in new_data:
                    session['interests'] = new_data['interests']
            session.modified = True
        
        return redirect(url_for('profile'))
    
    # GET: Show the form with current data
    if entity_type == 'user':
        # Create user_data from session information
        data = {
            'name': session.get('name'),
            'email': session.get('email'),
            'student_code': session.get('student_code'),
            'career': session.get('career'),
            'interests': session.get('interests'),
            'points': session.get('points', 0)
        }
        
        # Get additional data if available
        result = logic.get_entity_by_id(entity_id, entity_type)
        if result['status'] == 'success' and 'data' in result:
            # Only update fields from the database that aren't already in session
            db_data = result['data']
            if 'email' in db_data and not data['email']:
                data['email'] = db_data['email']
            if 'career' in db_data and not data['career']:
                data['career'] = db_data['career']
            if 'interests' in db_data and not data['interests']:
                data['interests'] = db_data['interests']
        
        return render_template('update_profile.html', entity_type=entity_type, data=data)
    else:
        # Create org_data from session information
        data = {
            'name': session.get('name'),
            'email': session.get('email'),
            'description': session.get('description'),
            'interests': session.get('interests'),
            'points': session.get('points', 0)
        }
        
        # We could fetch more org data from the database here if needed
        
        return render_template('update_profile.html', entity_type=entity_type, data=data)

@app.route('/profile/delete', methods=['GET', 'POST'])
@login_required
def delete_account():
    """
    Allow users or organizations to delete their account.
    """
    entity_id = session.get('entity_id') or session.get('org_id')
    entity_type = session.get('entity_type')
    
    if not entity_id or not entity_type:
        flash("Could not identify your session.", "error")
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        
        if not password:
            flash("Password is required to delete your account.", "error")
            return redirect(url_for('delete_account'))
        
        # Use logic function to attempt deletion
        result = logic.delete_my_account_logic(entity_id, entity_type, password)
        
        if result['status'] == 'success':
            # Clear session and redirect to home page
            session.clear()
            flash("Your account has been deleted successfully.", "success")
            return redirect(url_for('index'))
        else:
            flash(result['message'], result['status'])
            return redirect(url_for('delete_account'))
    
    # GET: Show confirmation form
    return render_template('delete_account.html')

@app.route('/exchange/requests')
@user_login_required
def view_my_requests():
    """
    View exchange requests (both sent and received).
    """
    entity_id = session.get('entity_id')
    if not entity_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('login'))
    
    # Get the request type from query parameter (default to 'received')
    request_type = request.args.get('type', 'received')
    if request_type not in ['received', 'sent']:
        request_type = 'received'
    
    # Call the logic function
    result = logic.view_my_exchange_requests_logic(entity_id, request_type)
    
    if result['status'] == 'success':
        requests = result.get('data', [])
        return render_template('exchange_requests.html', 
                              requests=requests, 
                              request_type=request_type)
    else:
        flash(result['message'], result['status'])
        return render_template('exchange_requests.html', 
                              requests=[], 
                              request_type=request_type)


# --- Organization Routes ---
@app.route('/organizations')
def view_organizations():
    """
    Search and view organizations.
    Users can search by name or interests.
    """
    # Get search parameters from the query string
    query = request.args.get('q', '')
    interests = request.args.get('interests', '')
    sort_by = request.args.get('sort_by', 'name')
    
    # Call the logic function
    result = logic.search_orgs_logic(query=query, interests=interests, sort_by=sort_by)
    
    if result['status'] == 'success':
        orgs = result.get('data', [])
        return render_template('view_organizations.html', 
                              orgs=orgs, 
                              query=query, 
                              interests=interests, 
                              sort_by=sort_by)
    else:
        flash(result['message'], result['status'])
        return render_template('view_organizations.html', 
                              orgs=[], 
                              query=query, 
                              interests=interests, 
                              sort_by=sort_by)

@app.route('/search_orgs')
def search_orgs():
    """Alias for view_organizations to maintain compatibility with templates"""
    return redirect(url_for('view_organizations'))

@app.route('/organization/<int:org_id>/members')
def view_org_members(org_id):
    """
    View all members of an organization.
    """
    # Call the logic function
    result = logic.get_org_members_logic(org_id)
    
    # Get organization details
    org_details = None
    orgs_result = logic.search_orgs_logic(query="", sort_by="name")
    if orgs_result['status'] == 'success':
        for org in orgs_result['data']:
            if org['org_id'] == org_id:
                org_details = org
                break
    
    if not org_details:
        flash("Organization not found.", "error")
        return redirect(url_for('view_organizations'))
    
    if result['status'] == 'success':
        members = result.get('data', [])
        # Check if current user is a member of this organization
        is_member = False
        if session.get('entity_type') == 'user' and session.get('entity_id'):
            entity_id = session.get('entity_id')
            for member in members:
                if member.get('entity_id') == entity_id:
                    is_member = True
                    break
        
        return render_template('org_members.html', 
                               org=org_details,
                               members=members,
                               is_member=is_member)
    else:
        flash(result['message'], result['status'])
        return redirect(url_for('view_organizations'))

@app.route('/organization/join/<int:org_id>', methods=['POST'])
@user_login_required
def join_org(org_id):
    """
    Allows a user to join an organization.
    """
    entity_id = session.get('entity_id')
    if not entity_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('login'))
    
    # Call the logic function
    result = logic.join_org_logic(entity_id, org_id)
    flash(result['message'], result['status'])
    
    return redirect(url_for('view_organizations'))

@app.route('/organization/leave/<int:org_id>', methods=['POST'])
@user_login_required
def leave_org(org_id):
    """
    Allows a user to leave an organization they've joined.
    """
    entity_id = session.get('entity_id')
    if not entity_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('login'))
    
    # Call the logic function
    result = logic.leave_org_logic(entity_id, org_id)
    flash(result['message'], result['status'])
    
    return redirect(url_for('view_organizations'))


# --- Event Routes ---
@app.route('/event/create', methods=['GET', 'POST'])
@login_required # Requires login (user or org)
def create_event():
    # Decorator ensures login.
    # Get organizer details from session.
    organizer_id = session.get('entity_id') or session.get('org_id')
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

@app.route('/event/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    """
    Delete an event. Only the organizer or an admin can delete an event.
    """
    entity_id = session.get('entity_id') or session.get('org_id')
    entity_type = session.get('entity_type')
    
    if not entity_id or not entity_type:
        flash("Could not identify your session.", "error")
        return redirect(url_for('view_events'))
    
    # Call the logic function to delete the event
    result = logic.delete_event_logic(entity_id, entity_type, event_id)
    flash(result['message'], result['status'])

    # Redirect back to the events list
    return redirect(url_for('view_events'))

@app.route('/events')
def view_events():
    # No login required to view events
    # Add any needed event filtering parameters here
    query = request.args.get('q', '')
    
    # Call the logic function
    result = logic.search_events_logic(query)
    
    if result['status'] == 'success':
        events = result.get('data', [])
        # Render the template with the events data
        return render_template('view_events.html', events=events)
    else:
        flash(result['message'], result['status'])
        return render_template('view_events.html', events=[])

@app.route('/event/participants/<int:event_id>')
@login_required # Login required to view participants
def view_event_participants(event_id):
    """
    Show participants for an event. This route will be used for attendance marking.
    Only accessible to event organizers and admins.
    """
    entity_id = session.get('entity_id') or session.get('org_id')
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
    events_result = logic.search_events_logic(query="")
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

@app.route('/event/register/<int:event_id>', methods=['POST'])
@user_login_required # Only users can register for events
def register_for_event(event_id):
    # Decorator ensures user login.
    entity_id = session.get('entity_id')
    entity_type = session.get("entity_type")
    if not entity_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('login'))

    result = logic.register_for_event_logic(entity_id, event_id)
    flash(result['message'], result['status'])

    if result['status'] == 'success':
         # --- Update points in session --- 
         # Similar to add_item, re-fetch points or increment based on logic guarantees
         user_data = logic.get_entity_by_id(entity_id, entity_type)
         if user_data['status'] == 'success':
             session['points'] = user_data['data'].get('points', session.get('points'))
             session.modified = True

    # Redirect back to the events list
    return redirect(url_for('view_events'))

@app.route('/event/leave/<int:event_id>', methods=['POST'])
@user_login_required
def leave_event(event_id):
    """
    Allows a user to leave an event they've registered for.
    """
    entity_id = session.get('entity_id')
    if not entity_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('view_events'))
    
    result = logic.leave_event_logic(entity_id, event_id)
    flash(result['message'], result['status'])
    
    return redirect(url_for('view_events'))

@app.route('/event/mark_attendance', methods=['POST'])
@login_required # Login required to mark attendance
def mark_attendance():
    """
    Mark attendance for a participant.
    Only accessible to event organizers and admins.
    """
    marker_id = session.get('entity_id') or session.get('org_id')
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


# --- Item Routes ---
@app.route('/item/add', methods=['GET', 'POST'])
@user_login_required # Only users can add items
def add_item():
    # Decorator ensures user login.
    owner_id = session.get('entity_id')
    owner_type = session.get('entity_type') 

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        item_type = request.form.get('item_type')
        item_terms = request.form.get('item_terms')

        # Validate required fields
        if not all([name, description, item_type, item_terms]):
            flash("All fields are required.", "error")
            return redirect(url_for('add_item'))
            
        # Call the logic function with updated parameters
        result = logic.add_item_logic(
            owner_id, owner_type, name, description, item_type, item_terms
        )

        flash(result['message'], result['status'])
        
        # Update session points if successful
        if result['status'] == 'success':
            # Re-fetch current points to ensure accuracy
             user_data = logic.get_entity_by_id(owner_id, owner_type)
             if user_data['status'] == 'success':
                 session['points'] = user_data['data'].get('points', session.get('points')) # Update session points
                 session.modified = True # Required when modifying mutable session objects

        return redirect(url_for('view_items'))

    # GET request: Show the form
    return render_template('add_item.html')

@app.route('/item/delete/<int:item_id>', methods=['POST'])
@user_login_required # Only users can delete their items
def delete_my_item(item_id):
    """Handles a user deleting their own item."""
    entity_id = session.get('entity_id')
    if not entity_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('login'))

    # Call the logic function to delete the item
    result = logic.delete_my_item_logic(entity_id, item_id)
    flash(result['message'], result['status'])
    
    # Redirect back to the items list
    return redirect(url_for('view_items'))

@app.route('/items')
def view_items():
    # No login required to view items
    # Get optional filter for item terms
    item_terms = request.args.get('terms')
    
    # Call the logic function with optional filter
    result = logic.view_items_logic(item_terms)
    
    if result['status'] == 'success':
        items = result.get('data', [])
        # Render the template with items and current filter
        return render_template('view_items.html', items=items, current_filter=item_terms)
    else:
        flash(result['message'], result['status'])
        return render_template('view_items.html', items=[], current_filter=item_terms)

@app.route('/item/request/<int:item_id>', methods=['POST'])
@user_login_required
def request_item(item_id):
    requester_id = session.get('entity_id')
    if not requester_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('login'))

    # Get message from form if added
    message = request.form.get('message', "") 

    # Call the updated logic function (using original item terms)
    result = logic.request_item_logic(requester_id, item_id, message)
    flash(result['message'], result['status'])

    return redirect(url_for('view_items'))

@app.route('/exchange/accept/<int:exchange_id>', methods=['POST'])
@user_login_required
def accept_exchange(exchange_id):
    """
    Accept an exchange request.
    """
    entity_id = session.get('entity_id')
    if not entity_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('login'))

    # Call the logic function
    result = logic.accept_exchange_logic(entity_id, exchange_id)
    flash(result['message'], result['status'])

    # Redirect back to exchange requests
    return redirect(url_for('view_my_requests'))

@app.route('/exchange/reject/<int:exchange_id>', methods=['POST'])
@user_login_required
def reject_exchange(exchange_id):
    """
    Reject an exchange request.
    """
    entity_id = session.get('entity_id')
    if not entity_id:
        flash("Could not identify user session.", "error")
        return redirect(url_for('login'))
    
    # Call the logic function
    result = logic.reject_exchange_logic(entity_id, exchange_id)
    flash(result['message'], result['status'])
    
    # Redirect back to exchange requests
    return redirect(url_for('view_my_requests'))


# --- Map Routes ---

@app.route('/map')
def view_map():
    """
    View map points.
    """
    # Call the logic function to get all map points
    result = logic.get_map_points_logic()
    
    if result['status'] == 'success':
        map_points = result.get('data', [])
        return render_template('view_map.html', map_points=map_points)
    else:
        flash(result['message'], result['status'])
        return render_template('view_map.html', map_points=[])

@app.route('/map/add', methods=['GET', 'POST'])
@login_required
def add_map_point():
    """
    Add a new map point if the user has the special permission code.
    """
    entity_id = session.get('entity_id') or session.get('org_id')
    entity_type = session.get('entity_type')
    
    if not entity_id or not entity_type:
        flash("Could not identify your session.", "error")
        return redirect(url_for('view_map'))
    
    if request.method == 'POST':
        # Get form data
        permission_code = request.form.get('permission_code')
        name = request.form.get('name')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        point_type = request.form.get('point_type')
        description = request.form.get('description')
        
        # Validate required fields
        if not all([permission_code, name, latitude, longitude, point_type]):
            flash("All required fields must be filled.", "error")
            return redirect(url_for('add_map_point'))
        
        # Convert latitude and longitude to float
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            flash("Latitude and longitude must be valid numbers.", "error")
            return redirect(url_for('add_map_point'))
        
        # Call the logic function
        result = logic.add_map_point_logic(
            entity_id, entity_type, permission_code, name, 
            latitude, longitude, point_type, description
        )
        
        flash(result['message'], result['status'])
        if result['status'] == 'success':
            return redirect(url_for('view_map'))
    else:
            return redirect(url_for('add_map_point'))
    
    # GET request: render the form
    return render_template('add_map_point.html')


# --- Challenge Routes ---

@app.route('/challenges')
@login_required
def view_challenges():
    """
    View all available challenges for the logged-in entity type.
    """
    entity_type = session.get('entity_type')
    
    # Get all challenges for this entity type
    result = logic.search_challenges_logic(entity_type)
    
    if result['status'] == 'success':
        challenges = result.get('data', [])
        
        # Get user's active challenges if they're logged in
        active_challenges = []
        if 'entity_type' in session:
            entity_id = session.get('entity_id') or session.get('org_id')
            active_result = logic.get_my_active_challenges_logic(entity_id, entity_type)
            if active_result['status'] == 'success':
                active_challenges = active_result.get('data', [])
        
        return render_template('view_challenges.html', 
                              challenges=challenges, 
                              active_challenges=active_challenges)
    else:
        flash(result['message'], result['status'])
        return render_template('view_challenges.html', challenges=[], active_challenges=[])

@app.route('/challenge/join/<int:challenge_id>', methods=['POST'])
@login_required
def join_challenge(challenge_id):
    """
    Join a challenge.
    """
    entity_id = session.get('entity_id') or session.get('org_id')
    entity_type = session.get('entity_type')
    
    if not entity_id or not entity_type:
        flash("Could not identify your session.", "error")
        return redirect(url_for('view_challenges'))
    
    # Call logic function
    result = logic.join_challenge_logic(entity_id, entity_type, challenge_id)
    flash(result['message'], result['status'])
    
    return redirect(url_for('view_challenges'))

@app.route('/achievements')
@login_required
def view_achievements():
    """
    View achievements for the logged-in entity type.
    """
    entity_type = session.get('entity_type')
    entity_id = session.get('entity_id') or session.get('org_id')
    
    if not entity_id or not entity_type:
        flash("Could not identify your session.", "error")
        return redirect(url_for('index'))
    
    # Get all achievements for this entity type
    result = logic.search_achievements_logic(entity_type)
    
    # Get user's unlocked achievements
    unlocked_achievements = []
    if entity_type == 'user':
        user_data = logic.get_entity_by_id(entity_id, entity_type)
        if user_data['status'] == 'success':
            unlocked_achievements = user_data['data'].get('achievements', [])
    
    if result['status'] == 'success':
        achievements = result.get('data', [])
        return render_template('view_achievements.html', 
                              achievements=achievements,
                              unlocked_achievements=unlocked_achievements)
    else:
        flash(result['message'], result['status'])
        return render_template('view_achievements.html', 
                              achievements=[],
                              unlocked_achievements=[])


# --- Admin Routes ---

def admin_required(f):
    """Decorator to ensure admin is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('entity_type') != 'admin':
            flash("Admin access required for this page.", "error")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    # If already logged in as admin, redirect to admin dashboard
    if session.get('entity_type') == 'admin':
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Call the logic function for admin authentication
        result = logic.admin_login(username, password)
        
        if result['status'] == 'success':
            # Store admin info in session
            session.clear()
            session['entity_type'] = 'admin'
            session['admin_id'] = result['admin_id']
            session['name'] = result['name']
            
            flash("Admin login successful!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash(result['message'], result['status'])
            return redirect(url_for('admin_login'))
    
    # GET request: show login form
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.clear()
    flash("Admin logged out successfully.", "success")
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard showing system overview."""
    # Get counts for various entities in the system
    users_count = logic.get_users_count()
    orgs_count = logic.get_orgs_count()
    events_count = logic.get_events_count()
    items_count = logic.get_items_count()
    
    # Get all users and organizations for display
    all_users = logic.users_view()
    all_orgs = logic.orgs_view()
    
    # Get top organizations by points
    top_orgs = logic.get_top_orgs_by_points(limit=5)

    return render_template('admin/dashboard.html',
                          users_count=users_count,
                          orgs_count=orgs_count,
                          events_count=events_count,
                          items_count=items_count,
                          all_users=all_users,
                          all_orgs=all_orgs,
                          top_orgs=top_orgs)

# --- User Management ---
@app.route('/admin/users')
@admin_required
def admin_users():
    """View and manage all users."""
    # Get filter parameters
    query = request.args.get('q', '')
    
    # Get users from database using search_users
    users = logic.search_users(query=query)
    
    return render_template('admin/users.html', users=users, query=query)

@app.route('/admin/users/<int:entity_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(entity_id):
    """Delete a user."""
    admin_id = session.get('admin_id')
    result = logic.admin_delete_user_logic(admin_id, entity_id)
    flash(result['message'], result['status'])
    return redirect(url_for('admin_users'))
  
# --- Organization Management ---
@app.route('/admin/organizations')
@admin_required
def admin_organizations():
    """View and manage all organizations."""
    # Get filter parameters
    query = request.args.get('q', '')
    
    # Get organizations from database
    result = logic.search_orgs_logic(query=query)
    
    if result['status'] == 'success':
        organizations = result.get('data', [])
        return render_template('admin/organizations.html', organizations=organizations, query=query)
    else:
        flash(result['message'], result['status'])
        return render_template('admin/organizations.html', organizations=[], query=query)
    
@app.route('/admin/organizations/<int:org_id>/delete', methods=['POST'])
@admin_required
def admin_delete_organization(org_id):
    """Delete an organization."""
    admin_id = session.get('admin_id')
    result = logic.admin_delete_org_logic(admin_id, org_id)
    flash(result['message'], result['status'])
    return redirect(url_for('admin_organizations'))

# --- Event Management ---
@app.route('/admin/events')
@admin_required
def admin_events():
    """View and manage all events."""
    # Get filter parameters
    query = request.args.get('q', '')
    
    # Get events from database
    result = logic.admin_get_events(query)
    
    if result['status'] == 'success':
        events = result.get('data', [])
        return render_template('admin/events.html', events=events, query=query)
    else:
        flash(result['message'], result['status'])
        return render_template('admin/events.html', events=[], query=query)

@app.route('/admin/events/<int:event_id>/delete', methods=['POST'])
@admin_required
def admin_delete_event(event_id):
    """Delete an event."""
    result = logic.admin_delete_event(event_id)
    flash(result['message'], result['status'])
    return redirect(url_for('admin_events'))

# --- Challenge Management ---
@app.route('/admin/challenges')
@admin_required
def admin_challenges():
    """View and manage all challenges."""
    # Get challenges from database for both users and organizations
    user_result = logic.search_challenges_logic('user')
    org_result = logic.search_challenges_logic('organization')
    
    challenges = []
    
    if user_result['status'] == 'success':
        challenges.extend(user_result.get('data', []))
        
    if org_result['status'] == 'success':
        challenges.extend(org_result.get('data', []))
        
    return render_template('admin/challenges.html', challenges=challenges)

@app.route('/admin/challenges/create', methods=['GET', 'POST'])
@admin_required
def admin_create_challenge():
    """Create a new challenge."""
    if request.method == 'POST':
        # Get form data
        admin_id = session.get('admin_id')
        name = request.form.get('title')
        description = request.form.get('description')
        points = int(request.form.get('points', 0))
        target_entity = request.form.get('target_entity')  # 'user' or 'organization'
        
        # Set default values for other required parameters
        goal_type = 'participation'  # Default goal type
        goal_target = 1  # Default target (1 participation)
        time_allowed = 0  # No time limit by default
        
        # Call logic function to create challenge
        result = logic.admin_create_challenge_logic(
            admin_id, name, description, goal_type, goal_target, 
            points, time_allowed, target_entity
        )
        
        flash(result['message'], result['status'])
        if result['status'] == 'success':
            return redirect(url_for('admin_challenges'))
        
    # GET request: show form
    return render_template('admin/create_challenge.html')

@app.route('/admin/challenges/<int:challenge_id>/delete', methods=['POST'])
@admin_required
def admin_delete_challenge(challenge_id):
    """Delete a challenge."""
    admin_id = session.get('admin_id')
    target_entity = request.form.get('target_entity', 'user')  # Default to 'user' if not specified
    result = logic.admin_delete_challenge_logic(admin_id, challenge_id, target_entity)
    flash(result['message'], result['status'])
    return redirect(url_for('admin_challenges'))

# --- Achievement Management ---
@app.route('/admin/achievements')
@admin_required
def admin_achievements():
    """View and manage all achievements."""
    # Get achievements from database for both users and organizations
    user_result = logic.search_achievements_logic('user')
    org_result = logic.search_achievements_logic('organization')
    
    achievements = []
    
    if user_result['status'] == 'success':
        achievements.extend(user_result.get('data', []))
        
    if org_result['status'] == 'success':
        achievements.extend(org_result.get('data', []))
        
    return render_template('admin/achievements.html', achievements=achievements)

@app.route('/admin/achievements/create', methods=['GET', 'POST'])
@admin_required
def admin_create_achievement():
    """Create a new achievement."""
    if request.method == 'POST':
        # Get form data
        admin_id = session.get('admin_id')
        name = request.form.get('name')
        description = request.form.get('description')
        target_entity = request.form.get('target_entity')  # 'user' or 'organization'
        points_threshold = int(request.form.get('points_threshold', 0))
        badge_icon = request.form.get('badge_icon', 'default_badge')  # Default icon if not specified
        
        # Call logic function to create achievement
        result = logic.admin_create_achievement_logic(
            admin_id, name, description, points_threshold, badge_icon, target_entity
        )
        
        flash(result['message'], result['status'])
        if result['status'] == 'success':
            return redirect(url_for('admin_achievements'))
        
    # GET request: show form
    return render_template('admin/create_achievement.html')

@app.route('/admin/achievements/<int:achievement_id>/delete', methods=['POST'])
@admin_required
def admin_delete_achievement(achievement_id):
    """Delete an achievement."""
    admin_id = session.get('admin_id')
    target_entity = request.form.get('target_entity', 'user')  # Default to 'user' if not specified
    result = logic.admin_delete_achievement_logic(admin_id, achievement_id, target_entity)
    flash(result['message'], result['status'])
    return redirect(url_for('admin_achievements'))

# --- System Stats ---
@app.route('/admin/stats')
@admin_required
def admin_stats():
    """View system statistics."""
    # Get stats from database
    stats = {
        'total_users': logic.get_users_count(),
        'total_orgs': logic.get_orgs_count(),
        'total_events': logic.get_events_count(),
        'total_items': logic.get_items_count(),
        'users': logic.users_view(),
        'orgs': logic.orgs_view(),
        'top_orgs': logic.get_top_orgs_by_points(limit=10)
    }
    
    return render_template('admin/stats.html', stats=stats)

@app.route('/admin/update_org_points', methods=['GET', 'POST'])
@admin_required
def admin_update_org_points():
    """Update all organization points based on their members' points."""
    if request.method == 'POST':
        # Update all organizations' points
        result = logic.update_org_points_from_members_logic()
        flash(result['message'], result['status'])
        
        # If organizations were updated, show details
        if result['status'] == 'success' and 'updated_orgs' in result:
            updated_orgs = result['updated_orgs']
            return render_template('admin/org_points_updated.html', updated_orgs=updated_orgs)
        
    # GET request or no organizations updated
    return render_template('admin/update_org_points.html')

if __name__ == '__main__':
    # Initialize the database
    import db_conn
    db_conn.setup_database()
    
    # Update database schema for exchange requests
    import db_operator
    db_operator.update_exchange_requests_schema()
    
    app.run(host='0.0.0.0', port=5000, debug=True) 