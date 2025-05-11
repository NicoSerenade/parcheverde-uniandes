import db_operator # Database operations
import db_conn # Used occasionally for direct DB access
import sqlite3 # For error handling
import bcrypt  # bcrypt is a hashing algorithm
import datetime # For datetime operations
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
socketio = SocketIO()
connected_users = {}

"""
Main business logic module for the Comunidad Verde application.

for creating an admin account:
- student_code: admin
- password: whatever you want (let's use admin2000 for standarization)

for adding a point map:
- permission_code: admin2000

Points System:
-------------
Events:
- Users: 5 points when their attendance is confirmed
- Event Organizers: 
  * 10 points when the first participant is confirmed (event is happening)
  * 2 points for each confirmed participant
- Organizations:
  * 20 points when at least 5 members have confirmed attendance at an event

Items:
- Users: 2 points for confirmed exchanged items, 4 points for borrowed items and 10 points for gave items
- Users: 1 point for each item added
Challenges:
- Points are awarded based on the challenge's difficulty (admins add challenges in the system)

Achievements:
- Are prizes based on the entity's points (users or organizations)

The points system encourages participation and community engagement.
"""

# --- Authentication Functions ---
def register_user(name, email, student_code, password, interests=None, career=None, photo=None):
    """
    Registers a new user whether Student, professor or admin in the system.
    Args:
        name (str): User's name.
        email (str): User's email.
        student_code (str): Student code or Professor code or Admin code.
        password (str): User's password.
        interests (str, optional): User's interests.
        career (str, optional): User's career.
        photo (str, optional): photo text identifier for 3 default photos. (photo-male, photo-female, photo-turtle)
    Returns a status message.
    """
    user_type = "user"

    if student_code == "admin":
        user_type = "admin"

    # 1. Validate Email Domain for non admin users
    elif not isinstance(email, str) or not email.endswith("@uniandes.edu.co"):
        print(f"status: error, message: Email must end with {'@uniandes.edu.co'}")
        return None
    
    if db_operator.check_user_exists(email, student_code):
        return {"status": "error", "message": " Email or student code might exist."}

    # Hash password before sending to db_operator
    hashed_password = None
    if password:
        password_bytes = password.encode('utf-8') #encode the password so that bcrypt module can handle it.
        salt = bcrypt.gensalt()  # Generates random salt; value that get combined with the password before hashing
        hashed_password = bcrypt.hashpw(password_bytes, 
        salt) #hash the password

    success = db_operator.register_user(user_type, student_code, hashed_password, name, email, career, interests, photo)
    if success:
        return {"status": "success", "message": f"User '{name}' registered successfully."}
    else:
        return {"status": "error", "message": "Database error."}

def register_organization(creator_email, creator_student_code, name, email, description, password, interests=None, photo="photo-org"):
    """
    Registers a new organization.
    Requires the student code of the creating user.
    Returns a status message indicating success or failure.

    Args:
        creator_student_code (str): The student code of the user creating the org.
        name (str): Organization name.
        email (str): Organization email.
        description (str): Organization description.
        password (str): Organization password.
        interests (str, optional): Organization interests.
        photo (str, optional): Organization photo.
    """

    if not db_operator.check_user_exists(creator_email, creator_student_code):
        return {"status": "error", "message": "Email or student code might exist."}

    user_type = "org"
    hashed_password = None
    if password:
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        
    success = db_operator.register_org(user_type, creator_student_code, hashed_password, name, email, description, interests)
    if success:
        return {"status": "success", "message": f"Organization '{name}' registered successfully."}
    else:
        return {"status": "error", "message": "Organization registration failed. Email might already exist."}

def login(code, password):
    """
    Authenticates normal users (students, professors or admins)
    args:
        code int: student, professor or admin code
        password str: password of the user
    Returns a dictionary containing status and entity data on success,
    or status and error message on failure.
    """
    # First try to authenticate as a user
    user = db_operator.get_user_by_student_code(code)
    if user:
        password_bytes = password.encode('utf-8')
        stored_password = user['password']
        if bcrypt.checkpw(password_bytes, stored_password):
            if user.get('user_type') == 'admin':
                print(f"Logic: Admin user '{user.get('name')}' authenticated.")
                return {
                    "status": "success",
                    "entity_type": "admin",
                    "user_id": user.get('user_id'),
                    "name": user.get('name'),
                    "email": user.get('email')
                }
                
            return {
                "status": "success",
                "entity_type": "user",
                "entity_id": user.get('user_id'),
                "student_code": user.get('student_code'),
                "name": user.get('name'),
                "email": user.get('email'),
                "points": user.get('points'),
                "interests": user.get('interests'),
                "career": user.get('career'),
                "photo": user.get('photo'),
                "creation_date": user.get("creation_date")
            }

    print(f"Logic: Login failed for code '{code}'")
    return {"status": "error", "message": "Invalid credentials or entity not found."}

def login_orgs(creator_code, password):
    """
    Authenticates organizations.
    Returns:
        a dictionary containing status and organization data on success,
        or status and error message on failure.
    """
    org = db_operator.get_org_by_creator_student_code(creator_code)
    if org:
        password_bytes = password.encode('utf-8')
        stored_password = org['password']
        if bcrypt.checkpw(password_bytes, stored_password):
            print(f"Logic: Organization '{org.get('name')}' authenticated.")
            return {
                "status": "success",
                "entity_type": "organization",
                "entity_id": org.get('org_id'),
                "name": org.get('name'),
                "email": org.get('email'),
                "description": org.get('description'),
                "points": org.get('points'),
                "interests": org.get('interests'),
                "creation_date": org.get("creation_date")
            }
    print(f"Logic: Login failed for code '{creator_code}'")
    return {"status": "error", "message": "Invalid credentials or entity not found."}

# --- Profile Functions ---
def update_my_profile_logic(entity_id, entity_type, new_data):
    """
    Updates a user or organization profile based on entity_type.
    
    Args:
        entity_id (int): ID of the user or organization
        entity_type (str): Either 'user' or 'organization'
        new_data (dict): New data to update the profile
    
    Returns:
        dict: Status and result message
    """

    # Validate email format
    if 'email' in new_data and new_data['email']:
        if not isinstance(new_data['email'], str) or not new_data['email'].endswith("@uniandes.edu.co"):
            return {"status": "error", "message": "Invalid email format. Must end with @uniandes.edu.co"}

    valid_fields = []
    
    # Handle password change with verification
    if 'password' in new_data and new_data['password']:
        # Check if old_password is provided
        if 'old_password' not in new_data or not new_data['old_password']:
            return {"status": "error", "message": "Old password is required to change password"}
        
        # Get current user/org data to verify old password
        if entity_type == 'user' or entity_type == 'admin':
            entity_data = db_operator.get_user_by_id(entity_id)
        elif entity_type == 'organization':
            entity_data = db_operator.get_org_by_id(entity_id)
        else:
            return {"status": "error", "message": f"Invalid entity type: {entity_type}"}
        # Verify old password
        old_password_bytes = new_data['old_password'].encode('utf-8')
        stored_password = entity_data['password']
        
        if not bcrypt.checkpw(old_password_bytes, stored_password):
            return {"status": "error", "message": "Current password is incorrect"}
        
        # Hash the new password
        password_bytes = new_data['password'].encode('utf-8')
        salt = bcrypt.gensalt()
        new_data['password'] = bcrypt.hashpw(password_bytes, salt)
        
        del new_data['old_password']
    
    if entity_type == 'user' or entity_type == 'admin':
        valid_fields = ['name', 'email', 'student_code', 'password', 'career', 'interests', 'photo']
        
        # Create a clean dict with only valid fields
        update_payload = {k: v for k, v in new_data.items() if k in valid_fields and v}
        
        # Call db_operator function
        if update_payload:
            success = db_operator.update_user_profile(entity_id, **update_payload)
            if success:
                return {"status": "success", "message": "Profile updated successfully."}
    
    elif entity_type == 'organization':
        # Valid fields for organization profile update
        valid_fields = ['name', 'email', 'creator_student_code', 'password', 'description', 'interests', 'photo']
        
        # Create a clean dict with only valid fields
        update_payload = {k: v for k, v in new_data.items() if k in valid_fields and v}
        
        # Call db_operator function
        if update_payload:
            success = db_operator.update_org_profile(entity_id, **update_payload)
            if success:
                return {"status": "success", "message": "Organization profile updated successfully."}
    
    else:
        return {"status": "error", "message": f"Invalid entity type: {entity_type}"}
    
    return {"status": "error", "message": "Failed to update profile. Please check your data."}

def delete_my_account_logic(entity_id, entity_type, password):
    """
    Allows the specified user, admin or organization to delete their own account after verifying password.
    Returns a status message dictionary.

    Args:
        entity_id (int): The ID of the user or organization to delete.
        entity_type (str): 'user', 'admin' or 'organization'.
        password (str): The password of the account for verification.
    """
    success = False
    if entity_type == 'user' or entity_type == 'admin':
        user_data = db_operator.get_user_by_id(entity_id)
        if user_data:
             password_bytes = password.encode('utf-8')
             stored_password = user_data['password']
             if bcrypt.checkpw(password_bytes, stored_password):
                student_code = user_data['student_code']
                success = db_operator.delete_my_user(student_code)
        else:
             print(f"Logic Error: Could not find student code for user {entity_id} to attempt deletion.")
             return {"status": "error", "message": "Account details not found for deletion."}

    elif entity_type == 'organization':
        org_data = db_operator.get_org_by_id(entity_id)
        if org_data:
             password_bytes = password.encode('utf-8')
             stored_password = org_data['password']
             if bcrypt.checkpw(password_bytes, stored_password):
                creator_code = org_data['creator_student_code']
                success = db_operator.delete_my_org(creator_code)
        else:
             return {"status": "error", "message": "Account details not found for deletion."}
    else:
         return {"status": "error", "message": f"Unknown entity type: {entity_type}"}

    if success:
        # Logout should be triggered in app.py after this returns success
        return {"status": "success", "message": "Account deleted successfully."}
    else:
        return {"status": "error", "message": "Failed to delete account. Please check your password."}

# --- Search users Functions ---
def search_users_logic(query=None, interests=None, career=None):
    """
    Searches users based on criteria.
    
    Args:
        query (str, optional): Search in name or description fields
        interests (str, optional): Filter by interests (partial match)
        career (str, optional): Filter by career (partial match)
        sort_by (str, optional): Sort by field ('name', 'points', 'creation_date')

    Returns:
        dict: A dictionary with status, message, and data if successful
    """
    users = db_operator.search_users(query=query, career=career, interests=interests)
    if users is None:
         return {"status": "error", "message": "Error searching users."}
    else:
        return {"status": "success", "data": users}

def get_entity_by_id(entity_id, entity_type):
    """
    Retrieves details of a specific user or organization. 
    Returns:
        dict: A dictionary with status, message, and data if successful
    """
    if entity_type == 'user' or entity_type == 'admin':
        entity_data = db_operator.get_user_by_id(entity_id)
        if entity_data is None:
            return {
                "status": "error",
                "message": "Failed to retrieve user details"
            }
    elif entity_type == 'org':
        entity_data = db_operator.get_org_by_id(entity_id)
        if entity_data is None:
            return {
                "status": "error",
                "message": "Failed to retrieve organization details"
            }
    return {
        "status": "success",
        "message": "Entity details retrieved successfully.",
        "data": entity_data
    }


# --- Organization Functions ---
def search_orgs_logic(query=None, interests=None, sort_by=None, user_id=None):
    """
    Searches organizations based on criteria.
    """
    orgs = db_operator.search_orgs(query=query, interests=interests, sort_by=sort_by, user_id=user_id)
    if orgs is None:
         return {"status": "error", "message": "Error searching organizations."}
    else:
        return {"status": "success", "data": orgs}

def get_user_orgs_logic(user_id):
    """
    Retrieves all organizations that a user is a member of.
    
    Args:
        user_id (int): The ID of the user
        
    Returns:
        dict: A dictionary with status, message, and data if successful
    """
    if not user_id:
        return {"status": "error", "message": "User ID is required"}
    
    try:
        # Use the search_orgs function with the user_id filter
        user_orgs = db_operator.search_orgs(user_id=user_id)
        
        if user_orgs is not None:
            return {
                "status": "success",
                "message": f"Found {len(user_orgs)} organizations for user",
                "data": user_orgs
            }
        else:
            return {"status": "error", "message": "Failed to retrieve user organizations"}
    
    except Exception as e:
        print(f"Logic Error in get_user_orgs_logic: {e}")
        return {"status": "error", "message": "An error occurred while retrieving user organizations"}

def get_org_members_logic(org_id):
    """
    Retrieves members of a specific organization.
    Returns a dictionary with status and data.

    Args:
        org_id: ID of the organization
    """
    # No session check needed here
    if not org_id:
        return {"status": "error", "message": "Organization ID is required."}
    
    print(f"Logic: Getting members for organization ID {org_id}")
    members = db_operator.get_org_members(org_id)
    if members is None:  # DB error
        return {"status": "error", "message": "Failed to retrieve organization members."}
    else:
        return {"status": "success", "data": members}

def join_org_logic(user_id, org_id):
    """
    Allows the specified user to join an organization.
    Returns a status message dictionary.

    Args:
        user_id (int): The ID of the user joining.
        org_id (int): The ID of the organization to join.
    """
    # Removed _get_session_details call
    # Type check ('user') should happen in app.py
    if not user_id:
        return {"status": "error", "message": "User ID is required."}

    print(f"Logic: User ID {user_id} attempting to join Org ID {org_id}")
    success = db_operator.join_org(org_id, user_id)

    if success:
        # Update organization points to include the new member's points
        update_org_points_from_members_logic(org_id=org_id)
        
        # Consider points/achievements for joining orgs?
        return {"status": "success", "message": "Successfully joined the organization."}
    else:
        # Possible reasons: already member, org doesn't exist, DB error
        return {"status": "error", "message": "Failed to join organization. You might already be a member or the organization may not exist."}

def leave_org_logic(user_id, org_id):
    """
    Allows the specified user to leave an organization.
    Returns a status message dictionary.

    Args:
        user_id (int): The ID of the user leaving.
        org_id (int): The ID of the organization to leave.
    """
    # Removed _get_session_details call
    # Type check ('user') should happen in app.py
    if not user_id:
        return {"status": "error", "message": "User ID is required."}

    print(f"Logic: User ID {user_id} attempting to leave Org ID {org_id}")
    success = db_operator.leave_org(org_id, user_id)

    if success:
        # Update organization points after member leaves
        update_org_points_from_members_logic(org_id=org_id)
        
        return {"status": "success", "message": "Successfully left the organization."}
    else:
        # Possible reasons: not a member, org doesn't exist, DB error
        return {"status": "error", "message": "Failed to leave organization. You might not be a member or the organization may not exist."}


# --- Event Functions ---
def create_event_logic(organizer_id, organizer_type, title, description, event_datetime, location, event_type):
    """
    Allows a user or organization (specified by ID and type) to create a new event.
    Note: No points are awarded for creating an event. Points are only awarded when:
    - The first participant's attendance is confirmed (10 points)
    - Each confirmed participant (2 points per participant)
    
    Args:
        organizer_id (int): The ID of the user or organization creating the event.
        organizer_type (str): 'user' or 'organization'.
        title (str): Event title.
        description (str): Event description.
        event_datetime (str): Event date and time.
        location (str): Event location.
        event_type (str): Event type.
        
    Returns:
        dict: Status message and event ID if successful
    """
    # Removed _get_session_details call
    # Input validation (e.g., ensuring organizer_id/type are provided) might be needed
    if not organizer_id or not organizer_type:
         return {"status": "error", "message": "Organizer ID and type are required."}

    # Map 'organization' type to 'org' if needed by db_operator
    db_organizer_type = 'org' if organizer_type == 'organization' else organizer_type
    if db_organizer_type not in ['user', 'org']:
         return {"status": "error", "message": f"Invalid organizer type: {organizer_type}"}

    print(f"Logic: {organizer_type.capitalize()} ID {organizer_id} creating event '{title}'")
    result_id = db_operator.create_event(organizer_id, db_organizer_type, title, description, event_type, location, event_datetime)
    if result_id:
        return {"status": "success", "message": f"Event '{title}' created successfully. You will earn points when participants attend.", "event_id": result_id}
    else:
        # Consider more specific error messages based on db_operator return/exceptions
        return {"status": "error", "message": "Failed to create event."}

def delete_event_logic(entity_id, entity_type, event_id):
    """
    Allows the specified user or organization (if they are the organizer) to delete an event.
    Returns a status message dictionary.

     Args:
        entity_id (int): The ID of the user or organization attempting deletion.
        entity_type (str): 'user' or 'organization'.
        event_id (int): The ID of the event to delete.
    """
    # Removed _get_session_details call
    # Permission check (is owner?) is handled by db_operator.delete_event
    if not entity_id or not entity_type:
        return {"status": "error", "message": "Entity ID and type are required."}

    # Map session type ('organization') to db type ('org') if necessary
    entity_type = 'org' if entity_type == 'organization' else entity_type
    if entity_type not in ['user', 'org']:
         return {"status": "error", "message": f"Invalid entity type: {entity_type}"}

    success = db_operator.delete_event(event_id, entity_id, entity_type)

    if success:
        return {"status": "success", "message": "Event deleted successfully."}
    else:
        # db_operator might print specific errors (not found, not authorized)
        return {"status": "error", "message": "Failed to delete event. It might not exist or you are not the organizer."}

def search_events_logic(event_id=None, query=None, event_type=None, status=None, organizer_type=None, organizer_id=None, start_date=None, end_date=None):
    """
    Searches for events based on various criteria.
    
    Params:
      event_id (int, optional): Filter by event ID.
      query (str, optional): Search term for name or description.
      event_type (str, optional): Filter by event type.
      status (str, optional): Filter by event status. (active, completed)
      organizer_type (str, optional): Organizer type ('user' or 'org').
      organizer_id (int, optional): Filter by organizer ID.
      start_date (str, optional): Filter events on or after this date.
      end_date (str, optional): Filter events on or before this date.
      
    
    Returns:
      dict: Status and event data.
    """
    events = db_operator.search_events(
        event_id=event_id,
        query=query,
        event_type=event_type,
        status=status,
        organizer_type=organizer_type,
        organizer_id=organizer_id,
        start_date=start_date,
        end_date=end_date
    )
    if events is None:
        return {"status": "error", "message": "Database error while searching events."}
    events = sorted(events, key=lambda x: x.get('event_datetime', ""), reverse=True)
    return {"status": "success", "data": events}

def get_event_participants_logic(event_id):
    """
    Retrieves participants of a specific event.
    Returns a dictionary with status and data.

    Args:
        event_id: ID of the event
    """
    # No session check needed here
    if not event_id:
        return {"status": "error", "message": "Event ID is required."}
    
    print(f"Logic: Getting participants for event ID {event_id}")
    participants = db_operator.get_event_participants(event_id)
    if participants is None:  # DB error
        return {"status": "error", "message": "Failed to retrieve event participants."}
    else:
        return {"status": "success", "data": participants}

def register_for_event_logic(user_id, event_id):
    """
    Allows a specified user to register for an event.
    Returns a status message. Points are only awarded when attendance is confirmed.

    Args:
        user_id (int): The ID of the user registering.
        event_id (int): The ID of the event to register for.
    """
    # Removed _get_session_details call
    # Type check (ensuring it's a user) should happen in app.py before calling
    if not user_id:
         return {"status": "error", "message": "User ID is required."}

    print(f"Logic: User ID {user_id} registering for event ID {event_id}")
    # Assuming db_operator.join_event expects 'user' as user_type
    success = db_operator.join_event(event_id, user_id, 'user')

    if success:
        return {"status": "success", "message": "Successfully registered for the event! You will receive points when your attendance is confirmed."}
    else:
        # Consider more specific errors (already registered, event full, event not found)
        return {"status": "error", "message": "Failed to register for the event. Maybe already registered, or the event doesn't exist."}

def leave_event_logic(entity_id, entity_type, event_id):
    """
    Allows the specified user or organization to leave an event they are registered for.
    Returns a status message dictionary.

    Args:
        entity_id (int): The ID of the user or organization leaving.
        entity_type (str): 'user' or 'organization'.
        event_id (int): The ID of the event to leave.
    """
    # Removed _get_session_details call
    if not entity_id or not entity_type:
        return {"status": "error", "message": "Entity ID and type are required."}

    # Map session type ('organization') to db type ('org') if necessary
    entity_type = 'org' if entity_type == 'organization' else entity_type
    if entity_type not in ['user', 'org']:
         return {"status": "error", "message": f"Invalid entity type: {entity_type}"}


    print(f"Logic: {entity_type.capitalize()} ID {entity_id} attempting to leave event ID {event_id}")
    success = db_operator.leave_event(event_id, entity_id, entity_type)

    if success:
        return {"status": "success", "message": "Successfully left the event."}
    else:
        return {"status": "error", "message": "Failed to leave event. Maybe you were not registered or the event doesn't exist."}

def mark_event_attendance_logic(marker_id, event_id, participant_id, participant_type):
    """
    Allows the specified event organizer to mark attendance for a participant.
    
    Points System:
    - Users: 5 points when their attendance is confirmed
    - Event Organizers: 
      * 10 points when the first participant is confirmed (event is happening)
      * 2 points for each confirmed participant
    - Organizations: 20 points when at least 5 members have confirmed attendance at an event
    """
    # Get event details to check if marker is the organizer
    events = db_operator.search_events(event_id)
    if not events or len(events) == 0:
        return {"status": "error", "message": "Event not found."}
        
    event_data = events[0]
    organizer_id = event_data['organizer_id']
    organizer_type = event_data['organizer_type']
    
    # Check if marker is the organizer
    if organizer_id != marker_id:
        return {"status": "error", "message": "Only the event organizer can mark attendance."}

    # Call db_operator function to mark attendance
    success = db_operator.mark_event_attendance(event_id, participant_id, participant_type)
    
    if not success:
        return {"status": "error", "message": "Failed to mark attendance. Check if participant is registered for the event."}
    
    # POINTS AWARDING SYSTEM
    messages = []
    
    # 1. Award points to participant for confirmed attendance
    if participant_type == 'user':
        # Award points to the user for participating
        participant_points = 5  # Points for attending an event
        award_participant = award_points_logic(participant_id, participant_type, participant_points)
        if award_participant['status'] == 'success':
            messages.append(f"Participant earned {participant_points} points for attendance.")
    
    # 2. Award points to the event organizer if applicable
    participant_count = get_confirmed_participant_count(event_id=event_id)
    
    # Award 10 points for first confirmed participant
    if participant_count == 1:
        organizer_bonus_points = 10  # Points for first confirmed attendee
        award_bonus = award_points_logic(organizer_id, organizer_type, organizer_bonus_points)
        if award_bonus['status'] == 'success':
            messages.append(f"Organizer earned {organizer_bonus_points} points for first confirmed attendee.")
    
    # Award 2 points to organizer for each confirmed participant
    organizer_points = 2  # Points per confirmed attendee
    award_organizer = award_points_logic(organizer_id, organizer_type, organizer_points)
    if award_organizer['status'] == 'success':
        messages.append(f"Organizer earned {organizer_points} points for confirming an attendee.")
    
    # 3. Check if participant belongs to an organization and if 5+ members attended
    if participant_type == 'user':
        # Get organizations that the user belongs to
        user_orgs = db_operator.search_orgs(user_id=participant_id)
        
        if user_orgs:
            for org in user_orgs:
                org_id = org['org_id']
                # Check how many confirmed members from this org have attended
                org_member_count = get_org_confirmed_count(event_id=event_id, org_id=org_id)
                
                # If exactly 5 members have been confirmed (including this one), award org points
                if org_member_count == 5:
                    org_points = 20  # Points for having 5 confirmed members
                    award_org = award_points_logic(org_id, 'org', org_points)
                    if award_org['status'] == 'success':
                        messages.append(f"Organization ID {org_id} earned {org_points} points for having 5 confirmed attendees.")
    
    # Generate success message
    message = "Attendance marked successfully."
    if messages:
        message += " " + " ".join(messages)
    
    return {"status": "success", "message": message}


def get_confirmed_participant_count(event_id):
    """
    Get the count of confirmed participants for an event.
    
    Args:
        event_id (int): The ID of the event
        
    Returns:
        int: Number of confirmed participants
    """
    conn = db_conn.create_connection()
    count = 0
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Count confirmed user participants
            cursor.execute('''
            SELECT COUNT(*) FROM user_event_participants
            WHERE event_id = ? AND attended = 1
            ''', (event_id,))
            user_count = cursor.fetchone()[0]
            
            # Count confirmed org participants
            cursor.execute('''
            SELECT COUNT(*) FROM org_event_participants
            WHERE event_id = ? AND attended = 1
            ''', (event_id,))
            org_count = cursor.fetchone()[0]
            
            count = user_count + org_count
            
        except sqlite3.Error as e:
            print(f"Error counting confirmed participants: {e}")
        finally:
            conn.close()
    
    return count

def get_org_confirmed_count(event_id, org_id):
    """
    Get the count of confirmed participants from a specific organization for an event.
    
    Args:
        event_id (int): The ID of the event
        org_id (int): The ID of the organization
        
    Returns:
        int: Number of confirmed participants from the organization
    """
    conn = db_conn.create_connection()
    count = 0
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Count confirmed user participants that belong to the organization
            cursor.execute('''
            SELECT COUNT(DISTINCT p.user_id) 
            FROM user_event_participants p
            JOIN organization_members m ON p.user_id = m.user_id
            WHERE p.event_id = ? AND p.attended = 1 AND m.org_id = ?
            ''', (event_id, org_id))
            
            count = cursor.fetchone()[0]
            
        except sqlite3.Error as e:
            print(f"Error counting confirmed org members: {e}")
        finally:
            conn.close()
    
    return count


# --- Item Functions ---
def add_item_logic(owner_id, name, description, item_type, item_terms):
    """
    Allows a specified user to add an item for exchange, gift or borrowing.
    Returns a status message, including points awarded.

    Args:
        owner_id (int): The user_id of the item owner.
        owner_type (str): The type of the owner (user or organization).
        name (str): Item name.
        description (str): Item description.
        item_type (str): Item type (ropa, libros, hogar, otros).
        item_terms (str): Item terms (regalo, intercambio).
    """
    # Removed _get_session_details call
    # Type check (ensuring it's a user) should happen in app.py
    if not owner_id:
        return {"status": "error", "message": "Owner ID is required."}

    valid_terms = ['regalo', 'intercambio']
    if item_terms not in valid_terms:
        return {"status": "error", "message": f"Invalid item terms. Must be one of: {', '.join(valid_terms)}"}
    
    item_id = db_operator.create_item(owner_id, name, description, item_type, item_terms)

    if item_id:
        points_to_award = 1  # Just 1 point for listing an item
        award_result = award_points_logic(owner_id, 'user', points_to_award)
        return {"status": "success", "message": f"Item '{name}' added successfully. {award_result.get('message', '')}"}
    else:
        return {"status": "error", "message": "Failed to add item."}

def delete_my_item_logic(user_id, item_id):
    """
    Allows the specified user to delete (mark as 'removed') their own item.
    Returns a status message dictionary.

    Args:
        user_id (int): The user_id attempting to delete the item.
        item_id (int): The ID of the item to delete.
    """
    # Removed _get_session_details call
    # Type check ('user') happens in app.py
    if not user_id:
        return {"status": "error", "message": "User ID is required."}

    print(f"Logic: User ID {user_id} attempting to delete item ID {item_id}")

    # 1. Verify ownership (important!)
    owner_id = db_operator.get_item_owner(item_id)
    if owner_id is None:
        return {"status": "error", "message": "Item not found."}
    if owner_id != user_id:
        return {"status": "error", "message": "You can only delete your own items."}

    # 2. Update status to 'removed' (or implement a real delete in db_operator if preferred)
    success = db_operator.update_item_status(item_id, 'removed')

    if success:
        return {"status": "success", "message": "Item removed successfully."}
    else:
        return {"status": "error", "message": "Failed to remove item."}

def view_items_logic(item_type=None, item_terms=None, user_id=None):
    """
    Retrieves items currently available for exchange, gift or borrowing.
    Items can be filtered by their terms.
    
    Args:
        item_type (str, optional): Filter by item type (ropa, libros, hogar, otros).
        item_terms (str, optional): Filter by item terms (gift, loan, exchange).
        user_id (int, optional): items from the specific owner.
        If None, all items are returned.
    
    Returns:
        dict: Dictionary with status and data.  
    """ 
    items = db_operator.get_available_items(item_type=item_type, item_terms=item_terms, user_id=user_id)
    if items is None:
        return {"status": "error", "message": "Failed to retrieve items."}
    else:
        return {"status": "success", "data": items}

def request_item_logic(requester_id, item_id, message=""):
    """
    Allows a user to request an item.
    Uses the original item terms defined by the owner.
    
    Args:
        requester_id (int): The user_id of the requester.
        item_id (int): The ID of the item being requested.
        message (str, optional/Mandatory): Mandatory message only for requesting an item as a exchange.
        
    Returns:
        dict: Status message and details.
    """
    # Validate requester and item ID
    if not requester_id or not item_id:
        return {"status": "error", "message": "Requester ID and Item ID are required."}

    # Retrieve item details and verify availability
    item_details = db_operator.get_item_details(item_id)
    if not item_details:
        return {"status": "error", "message": "Item not found."}
    owner_id = item_details.get('owner_id')
    item_name = item_details.get('name')
    item_term = item_details.get('item_terms')  # expected to be 'gift', 'loan', or 'exchange'
    if owner_id == requester_id:
        return {"status": "error", "message": "You cannot request your own items."}
    if item_details.get('status') != 'available':
        return {"status": "error", "message": "This item is not available for request."}
    
    # Process the request based on item term
    if item_term == 'gift':
        update_success = db_operator.update_item_status(item_id, 'unavailable')
        if update_success:
            return {"status": "success", "message": f"Gift item '{item_name}' requested. The item is now unavailable. Initiate chat with the owner."}
        else:
            return {"status": "error", "message": "Failed to update item status for gift request."}
    
    elif item_term == 'loan':
        update_success = db_operator.update_item_status(item_id, 'borrowed')
        if update_success:
            return {"status": "success", "message": f"Loan item '{item_name}' requested. The item is now marked as borrowed. Initiate chat with the owner regarding delivery and return."}
        else:
            return {"status": "error", "message": "Failed to update item status for loan request."}
    
    elif item_term == 'exchange':
        if not message.strip():
            return {"status": "error", "message": "Proposal message is required for exchange requests."}
        exchange_id = db_operator.create_item_request(requester_id, owner_id, item_id, item_term, message)
        if exchange_id:
            return {"status": "success", "message": f"Exchange proposal for item '{item_name}' submitted successfully. Wait for the owner's decision."}
        else:
            return {"status": "error", "message": "Failed to submit exchange proposal."}
    
    else:
        return {"status": "error", "message": "Invalid item term."}

# --- Map Functions ---
def add_map_point_logic(adder_id, adder_type, permission_code, name, latitude, longitude, point_type, description):
    """
    Allows logged-in users/orgs (specified by ID/type) to add a map point if they have the permission code (admin2000).
    Returns a status message.

    Args:
        adder_id (int): The ID of the user/org adding the point.
        adder_type (str): 'user' or 'organization'.
        permission_code (str): The required permission code.
        name (str): Point name.
        latitude (float): Point latitude.
        longitude (float): Point longitude.
        point_type (str): Type of map point.
        description (str): Point description.
    """
    if adder_type != "admin":
        if permission_code != "admin2000":
            return {"status": "error", "message": "invalid permission code."}
    
    success = db_operator.add_map_point(adder_id, name, description, point_type, latitude, longitude)

    if success:
        return {"status": "success", "message": f"Map point '{name}' added successfully."}
    else:
        return {"status": "error", "message": "Failed to add map point. The point might already exists."}

def delete_map_point_logic(deleter_id, deleter_type, point_id):
    """
    Allows an admin or potentially the creator to delete a map point.
    Permission logic needs clarification (is it admin only, or creator?).
    Currently assumes db_operator handles permissions based on deleter_id/type.

    Args:
        deleter_id (int): ID of the user/org attempting deletion.
        deleter_type (str): 'user', 'organization', or 'admin'.
        point_id (int): ID of the map point to delete.
    """
    if not deleter_id or not deleter_type:
        return {"status": "error", "message": "Deleter ID and type are required."}
    # Assuming db_operator.delete_map_point handles permission check
    # TODO: Clarify and confirm db_operator.delete_map_point signature and permission logic
    # Assumed signature: delete_map_point(user_id, user_type, point_id)
    print(f"Logic: {deleter_type.capitalize()} ID {deleter_id} attempting to delete map point ID {point_id}")
    success = db_operator.delete_map_point(deleter_id, deleter_type, point_id)

    if success:
        return {"status": "success", "message": "Map point deleted successfully."}
    else:
        return {"status": "error", "message": "Failed to delete map point. Check permissions or if the point exists."}

def get_map_points_logic():
    """
    Retrieves all map points.
    Returns a dictionary with status and data.
    """
    print("Logic: Fetching all map points.")
    points = db_operator.get_map_points()
    if points is None:  # DB error
        return {"status": "error", "message": "Failed to retrieve map points."}
    else:
        return {"status": "success", "data": points}

#TEMPORARY QUICK SOLUTION FOR MAP POINTS BELOW FROM SANTI's CODE

def get_map_points():
     """Get all map points from database
        Returns list of dictionaries with point data.
     """
     try:
         conn = db_conn.create_connection()
         if conn is None:
             return []
             
         cursor = conn.cursor()
         cursor.execute("""
             SELECT id, name, description, point_type, latitude, longitude, added_by, created_at
             FROM map_points
             ORDER BY created_at DESC
         """)
         
         points = cursor.fetchall()
         
         # Convertir a lista de diccionarios
         map_points = []
         for point in points:
             map_points.append({
                 'id': point[0],
                 'name': point[1],
                 'description': point[2],
                 'point_type': point[3],
                 'latitude': point[4],
                 'longitude': point[5],
                 'added_by': point[6],
                 'created_at': point[7]
             })
             
         return map_points
     except Exception as e:
         print(f"Error getting map points: {e}")
         return []
     finally:
         if conn:
             conn.close()
 
def save_map_point(point_data):
    """
    Saves a new map point to the database.
    """
    try:
        conn = db_conn.create_connection()
        if conn is None:
            return {'status': 'error', 'message': 'Database connection failed'}
            
        cursor = conn.cursor()
        
        # Obtener creator_id de la sesión o usar valor por defecto
        creator_id = point_data.get('creator_id', 1)
        
        cursor.execute("""
            INSERT INTO map_points (
                name, 
                description, 
                point_type, 
                latitude, 
                longitude, 
                added_by,
                creator_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            point_data['name'],
            point_data['description'],
            point_data['point_type'],
            point_data['latitude'],
            point_data['longitude'],
            point_data['added_by'],
            creator_id
        ))
        
        conn.commit()
        return {'status': 'success', 'message': 'Point saved successfully'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
    finally:
        if conn:
            conn.close()

#-----------------------------

# --- Challenge Functions ---
def search_challenges_logic(entity_type):
    """
    Searches for challenges available for the given entity type ('user' or 'organization').

    Args:
        entity_type (str): 'user' or 'organization'.
    """
    if entity_type not in ['user', 'organization']:
         return {"status": "error", "message": "Invalid entity type for challenges."}
    db_type = 'org' if entity_type == 'organization' else 'user'
    print(f"Logic: Searching challenges for {entity_type}s")
    challenges = db_operator.search_challenges(user_type=db_type)
    if challenges is None: # DB Error
        return {"status": "error", "message": f"Could not retrieve challenges for {entity_type}s."}
    else:
        return {"status": "success", "data": challenges}

def join_challenge_logic(entity_id, entity_type, challenge_id):
    """
    Allows the specified user or organization to join a challenge.

    Args:
        entity_id (int): ID of the user/org joining.
        entity_type (str): 'user' or 'organization'.
        challenge_id (int): ID of the challenge to join.
    """
    if not entity_id or not entity_type:
        return {"status": "error", "message": "Entity ID and type are required."}
    db_type = 'org' if entity_type == 'organization' else 'user'
    if db_type not in ['user', 'org']:
         return {"status": "error", "message": f"Invalid entity type: {entity_type}"}

    success = db_operator.join_challenge(entity_id, db_type, challenge_id)
    if success:
        return {"status": "success", "message": "Successfully joined the challenge."}
    else:
        return {"status": "error", "message": "Failed to join challenge. Maybe already joined, challenge doesn't exist, or type mismatch."}

def get_my_active_challenges_logic(entity_id, entity_type):
    """
    Retrieves the active challenges for the specified user or organization.
    Returns a status message and a dict with the active challenges.
    """
    active_challenges = db_operator.get_active_challenges(entity_id, entity_type)
    if active_challenges is None: 
        return {"status": "error", "message": "database error."}

    elif not active_challenges:
        return {"status": "success", "data": []}

    else:
        return {"status": "success", "data": active_challenges}

def search_achievements_logic(entity_type):
    """
    Searches for all defined achievements for a given type.

     Args:
        entity_type (str): 'user' or 'organization'.
    Returns:
        dict: Status message and list of dictionaries, each containing achievement data (id, name, description, points, icon).
    """
    if entity_type == 'user':
        db_type = 'user'
    elif entity_type == 'organization':
        db_type = 'org'
    else:
        return {"status": "error", "message": "Invalid entity type for achievements."}
    achievements = db_operator.search_achievements(db_type)
    if achievements is None:
        return {"status": "error", "message": f"There are no achievements for {entity_type}s."}
    else:
        return {"status": "success", "data": achievements}

def update_challenge_progress_logic(entity_id, entity_type, challenge_id, progress_increment):
    """
    Updates the progress of a challenge for a given entity.
    Args:
        entity_id (int): ID of the user/org.
        entity_type (str): 'user' or 'organization'.
        challenge_id (int): ID of the challenge.
        progress_increment (int): Amount to increment the challenge progress by.
        
    Returns:
        dict: Status and message with details about the operation.
    """
    active_challenges = db_operator.get_active_challenges(entity_id, entity_type)
    for challenge in active_challenges:
        if challenge['challenge_id'] == challenge_id:
            challenge_data = challenge
            break

    current_progress = challenge_data['current_progress']
    goal_target = challenge_data['goal_target']
    new_progress = current_progress + progress_increment

    # Check if the challenge is completed
    if new_progress >= goal_target:
        new_progress = goal_target
        challenge_status = 'completed'
        completion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Award points for completion
        points_awarded = challenge_data['points_reward']
        status = award_points_logic(entity_id, entity_type, points_awarded)
        if status['status'] == 'error':
            return {"status": "error", "message": "Failed to award points for challenge completion."}

    else:
        challenge_status = None
        completion_time = None
        status = None

    db_result = db_operator.update_challenges_progress(
        entity_id, 
        entity_type, 
        challenge_id,
        new_progress,
        challenge_status,
        completion_time
    )

    if db_result and status:
        return {"status": "success", "message": "Challenge completed", "points awarded": f"{points_awarded}."}

    elif db_result:
        return {"status": "success", "message": f"Challenge progress updated to {new_progress}."}
    
    else:
        return {"status": "error", "message": "Failed to update challenge progress."}

# --- Points Functions ---
def update_org_points_from_members_logic(org_id=None, user_id=None):
    """
    Updates organization points based on the sum of its members' points.
    
    If org_id is provided, only that organization's points are updated.
    If user_id is provided, all organizations that the user is a member of will be updated.
    If neither is provided, all organizations will be updated.
    
    Args:
        org_id (int, optional): The ID of a specific organization to update
        user_id (int, optional): The ID of a user whose organizations should be updated
        
    Returns:
        dict: Status message and list of updated organizations
    """
    updated_orgs = []
    
    if user_id:
        # Get all organizations this user is a member of
        user_orgs = db_operator.search_orgs(user_id)
        if user_orgs:
            for org in user_orgs:
                update_result = update_single_org_points(org['org_id'])
                if update_result:
                    updated_orgs.append(update_result)
    elif org_id:
        # Update a specific organization
        update_result = update_single_org_points(org_id)
        if update_result:
            updated_orgs.append(update_result)
    else:
        # Update all organizations
        all_orgs = db_operator.search_orgs()
        if all_orgs:
            for org in all_orgs:
                update_result = update_single_org_points(org['org_id'])
                if update_result:
                    updated_orgs.append(update_result)
    
    if updated_orgs:
        return {
            "status": "success", 
            "message": f"Updated points for {len(updated_orgs)} organizations"
        }
    else:
        return {"status": "info", "message": "No organizations were updated"}

def update_single_org_points(org_id):
    """
    Helper function to update a single organization's points.
    
    Args:
        org_id (int): The ID of the organization to update
        
    Returns:
        dict or None: Information about the updated organization or None if update failed
    """
    members = db_operator.get_org_members(org_id)
    
    if not members:
        return None
    
    # Calculate the sum of all members' points
    total_points = 0
    
    for member in members:
        # Get user details including points
        user_data = db_operator.get_user_by_id(member['user_id'])
        total_points += user_data.get('points', 0)
    
    # Get current organization points
    org_data = db_operator.get_org_by_id(org_id)
    if not org_data:
        return None
    
    current_points = org_data.get('points', 0)
    
    if total_points != current_points:
        points_diff = total_points - current_points
        
        db_operator.update_entity_points(org_id, 'org', points_diff)
        
        print(f"Logic: Updated organization ID {org_id} points from {current_points} to {total_points}")
        
        return {
            'org_id': org_id,
            'name': org_data.get('name', 'Unknown'),
            'previous_points': current_points,
            'new_points': total_points,
            'members_count': len(members)
        }
    
    return None

def award_points_logic(entity_id, entity_type, points_to_add):
    """
    Awards points to a specific user or organization and checks for achievement unlocks.
    
    Points System:
    - Events:
    * Users: 5 points when their attendance is confirmed
    * Event Organizers: 
        - 10 points when the first participant is confirmed (event is happening)
        - 2 points for each confirmed participant
    * Organizations: 20 points when at least 5 members have confirmed attendance at an event
    
    - Items:
    * Users: 2 points for confirmed exchanged items, 4 points for borrowed items and 10 points for gave items
    
    - Challenges:
    * Points are awarded based on the challenge's difficulty (admins add challenges in the system)
    
    - Achievements:
    * Are prizes based on the entity's points (users or organizations)
    
    Args:
    entity_id (int): The ID of the user or organization
    points (int): Number of points to award
    entity_type (str): 'user' or 'org' or 'organization'
    
    Returns:
    dict: Status message, new total points and any unlocked achievements
    """
    response = None
    achievement_unlocked = None
    if entity_type == "user":
        user_data = db_operator.get_user_by_id(entity_id)
        old_points = user_data.get('points', 0)
        new_points = old_points + points_to_add
    elif entity_type == "org":
        org_data = db_operator.get_org_by_id(entity_id)
        old_points = org_data.get('points', 0)
        new_points = old_points + points_to_add


    # Check for achievements logic
    achievements = db_operator.search_achievements(entity_type)
    if achievements:
        for ach in achievements:
            # Check if the new points exceed the any new achievement threshold 
            if old_points < ach['points_required'] and new_points >= ach['points_required']:
                # Unlock the achievement
                achievement_unlocked = ach['name']
                db_operator.update_entity_achievements(entity_id, entity_type, ach['achievement_id'])
                break
        db_operator.update_entity_points(entity_id, entity_type, new_points)
        response = {
            "status": "success",
            "Total points": f"New total points: {new_points}",
            "achievement_unlocked": achievement_unlocked
        }
               
    else:
        response = {
            "status": "error",
            "message": "There are no achivements in the system."
        }

    if entity_type == 'user':
        update_org_points_from_members_logic(entity_id)
     
    return response

def get_entity_achievements(entity_id, entity_type):
    '''
    Retrieves the achievements info for the specified user.
    Returns a dictionary with status message and achievements data.
    '''
    response = db_operator.get_entity_achievements(entity_id, entity_type)
    if response is None:
        return {
            "status": "error",
            "data": "Failed to retrieve achievements."
        }
    return {
        "status": "success",
        "data": response
    }
    
def search_achievements_logic(entity_type):
    """
    Searches for all defined achievements for a given type.
    Returns:
        dict: Status message and list of dictionaries, each containing achievement data (id, name, description, points, icon).
    """
    achievements = db_operator.search_achievements(entity_type)
    if achievements is None:
        return {"status": "error", "message": f"There are no achievements for {entity_type}s."}
    else:
        return {"status": "success", "data": achievements}

# --- Admin Functions ---
#Note: For getting user and orgs data admin can use the same functions as normal users
#Note: This functions appears at the admin dashboard, so only admins must be able to access them

def admin_delete_org_logic(org_id_to_delete):
    """
    Allows an admin (verified in app.py) to delete an organization.

     Args:
        org_id_to_delete (int): The ID of the organization to delete.
    """
    success = db_operator.delete_org_by_id(org_id_to_delete)
    if success:
        return {"status": "success", "message": f"Organization ID {org_id_to_delete} deleted successfully."}
    else:
        return {"status": "error", "message": f"Failed to delete organization ID {org_id_to_delete}."}

def admin_create_achievement_logic(name, description, points_required, badge_icon, achievement_user_type):
    """
    Allows an admin (verified in app.py) to create a new achievement.

     Args:
        name (str): Achievement name.
        description (str): Achievement description.
        points_required (int): Points needed to unlock.
        badge_icon (str): name of the SVG icon to show
        achievement_user_type (str): 'user' or 'org'.
    """
    # Admin check MUST happen in app.py route before calling this
    result_id = db_operator.create_achievement(name, description, points_required, badge_icon, achievement_user_type)
    if result_id:
        return {"status": "success", "message": f"Achievement '{name}' created successfully."}
    else:
        return {"status": "error", "message": "Failed to create achievement. Name might already exist."}

def admin_delete_achievement_logic(achievement_id, achievement_user_type):
    """
    Allows an admin (verified in app.py) to delete an achievement.

    Args:
        achievement_id (int): ID of the achievement to delete.
        achievement_user_type (str): 'user' or 'org'.
    """
    # Admin check MUST happen in app.py route before calling this
    success = db_operator.delete_achievement(achievement_id, achievement_user_type)
    if success:
        return {"status": "success", "message": "Achievement deleted successfully."}
    else:
        return {"status": "error", "message": "Failed to delete achievement."}

def admin_create_challenge_logic(name, description, goal_type, goal_target, points_reward, time_allowed, challenge_user_type):
    """
    Allows an admin (verified in app.py) to create a new challenge.

    Args:
        name (str): Challenge name.
        description (str): Challenge description.
        goal_type (str): Type of goal.
        goal_target (int): Target value for the goal.
        points_reward (int): Points reward.
        time_allowed (int, optional): Time limit in seconds.
        challenge_user_type (str): 'user' or 'org'.
    """
    # Admin check MUST happen in app.py route before calling this
    result_id = db_operator.create_challenge(name, description, goal_type, goal_target, points_reward, time_allowed, challenge_user_type)
    if result_id:
        return {"status": "success", "message": f"Challenge '{name}' created successfully."}
    else:
        return {"status": "error", "message": "Failed to create challenge. Name might already exist."}

def admin_delete_challenge_logic(challenge_id, challenge_user_type):
    """
    Allows an admin (verified in app.py) to delete a challenge.

    Args:
        challenge_id (int): ID of the challenge to delete.
        challenge_user_type (str): 'user' or 'org'.
    """
    # Admin check MUST happen in app.py route before calling this
    success = db_operator.delete_challenge(challenge_id, challenge_user_type)
    if success:
        return {"status": "success", "message": "Challenge deleted successfully."}
    else:
        return {"status": "error", "message": "Failed to delete challenge."}

def admin_get_events(query=None):
    """
    Admin function to get all events, optionally filtered by a search query.
    
    Args:
        query (str, optional): Optional search term for event title or description
        
    Returns:
        dict: Status and data containing a list of events
    """
    events = db_operator.search_events(query=query)
    
    if events is None:
        return {"status": "error", "message": "Failed to retrieve events."}
    else:
        return {"status": "success", "data": events}

def admin_delete_event(event_id):
    """
    Admin function to delete any event regardless of organizer.
    
    Args:
        event_id (int): ID of the event to delete
        
    Returns:
        dict: Status and message
    """
    if not event_id:
        return {"status": "error", "message": "Event ID is required."}
    
    success = db_operator.delete_event(event_id, None, 'admin')
    if success:
        return {"status": "success", "message": "Event deleted successfully."}
    else:
        return {"status": "error", "message": "Failed to delete event. It might not exist."}

# --- Stats Functions ---
def get_users_count():
    """Returns the total number of users in the system."""
    return db_operator.get_users_count()

def get_orgs_count():
    """Returns the total number of organizations in the system."""
    return db_operator.get_orgs_count()

def get_events_count():
    """Returns the total number of events in the system."""
    return db_operator.get_events_count()

def get_items_count():
    """Returns the total number of exchange items in the system."""
    return db_operator.get_items_count()

def users_view():
    """
    Retrieves all users from the database for admin viewing.
    Returns a list of user dictionaries with all information except passwords.
    """
    return db_operator.users_view()

def orgs_view():
    """
    Retrieves all organizations from the database for admin viewing.
    Returns a list of organization dictionaries with all information except passwords.
    """
    return db_operator.orgs_view()

def get_top_orgs_by_points(limit=5):
    """
    Get a list of top organizations by points.
    
    Args:
        limit (int): Number of organizations to return
        
    Returns:
        list: List of top organizations
    """
    # Get all orgs
    result = search_orgs_logic(sort_by="points")
    
    if result['status'] != 'success':
        return []
        
    # Sort by points in descending order
    top_orgs = sorted(result['data'], key=lambda x: x.get('points', 0), reverse=True)
    
    # Limit the results to the specified number
    return top_orgs[:limit] if limit and len(top_orgs) > limit else top_orgs


# --- Messaging Functions ---

## SocketIO event handlers

@socketio.on('connect')
def handle_connect():
    """
    Handler for the SocketIO 'connect' event.

    This function is automatically executed when a new client establishes a
    WebSocket connection with the server. Its primary purpose is:
    1. Identify the authenticated user by accessing the active Flask session
       (`session.get('entity_id')`).
    2. Get the unique session ID (`sid`) for this specific connection
       from `request.sid`.
    3. If the user is authenticated, register the association between their
       `entity_id` and the current `sid` in the `connected_users` dictionary.
    4. Join the connection (`sid`) to the appropriate 'rooms':
        - A personal room named with the user's `entity_id` (for
          private messages).
        - Rooms for each organization group the user belongs to
          (named e.g., 'org_room_<org_id>').

    This function takes no direct arguments but accesses the Flask context
    (`session`, `request`).
    """
    sid = request.sid
    print(f"SocketIO: New connection established with SID: {sid}")
    
    user_id = session.get('entity_id')
    user_type = session.get('entity_type')
    
    if user_id and user_type == 'user':
        connected_users[sid] = user_id
        print(f'User autenticated: ID: {user_id}, type: {user_type}. SID saved: {sid}')
        
        personal_room = str(user_id)
        join_room(personal_room)
        print(f'personal_room: {personal_room}')
        print(f"SocketIO: User {user_id} joined their personal room: {personal_room}")
        
        for org in get_user_orgs_logic(user_id = user_id)['data']:
            org_id = org['org_id']
            org_room = f'org_room_{org_id}'
            join_room(org_room)
            print(f"SocketIO: User {user_id} joined organization room: {org_room}")
        
    #elif with user_type == 'org' case. [TODO: Add logic for organizations]
    else: print(f"SocketIO: User not authenticated. SID: {sid} not saved.")
    # (session, request, connected_users, join_room)

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handler for the SocketIO 'disconnect' event.

    This function is automatically executed when SocketIO detects that a
    client connection has been lost (e.g., browser tab closed, network loss).
    Its main purpose is cleanup:
    1. Get the `sid` of the connection that was lost (`request.sid`).
    2. Look up in the `connected_users` dictionary if that `sid` was
       associated with any `entity_id`.
    3. If an association is found, remove that entry from the
       `connected_users` dictionary to reflect that the user no longer
       has that active connection.

    Leaving the rooms the `sid` was part of is typically handled
    automatically by Flask-SocketIO.
    This function takes no direct arguments but accesses `request.sid`.
    """
    sid = request.sid
    print(f"SocketIO: Connection with SID {sid} has been disconnected.")
    
    user_id_remove = None
    
    
    for key, value in connected_users.items():
        if key == sid:
            user_id_remove = value
            break
    
    if user_id_remove:
        try:
            del connected_users[sid]
            print(f"SocketIO: User ID {user_id_remove} removed from connected users.")
        except KeyError:
            print(f"SocketIO: User ID {user_id_remove} not found in connected users.")
    else: print(f'SocketIO: No user found for SID {sid}.")')
    
    # (request, connected_users)

@socketio.on('private_message')
def handle_private_message(data: dict) -> None:
    """
    Handler for the custom 'private_message' event.

    Triggered when a client emits a 'private_message' event.
    Manages the sending of one-to-one private messages.

    Args:
        data (dict): The data object sent by the client. Expected to
                     contain at least:
                     - 'recipient_id': The ID of the destination user.
                     - 'recipient_type': The type of the recipient (usually 'user').
                     - 'content': The text content of the message.

    Logic:
    1. Identifies the sender (`sender_id`, `sender_type`) using `session`.
    2. Validates that the sender is authenticated and that `data` contains
       the necessary information.
    3. Calls `save_message_logic` to persist the message in the database.
    4. If saved successfully, emits a 'new_message' event with the message
       details only to the recipient's personal room (`room=str(recipient_id)`).
    """
    
    sender_id = session.get('entity_id')
    sender_type = session.get('entity_type')
    
    if not sender_id or not sender_type:
        emit('error_message', {'message': 'Sender not authenticated.'})
        print("SocketIO: Sender not authenticated.")
        return
    
    recipient_id_str = data.get('recipient_id')
    recipient_type = 'user'
    content = data.get('content')
    
    if not recipient_id_str or not recipient_type or not content:
        emit('error_message', {'message': 'Missing required fields.'})
        print("SocketIO: Missing required fields.")
        return
    
    try:
        recipient_id = int(recipient_id_str)
    except (ValueError, TypeError):
        emit('error_message', {'message': 'Invalid recipient ID.'})
        print("SocketIO: Invalid recipient ID.")
        return
    
    
    save_message = save_message_logic(sender_id, sender_type, recipient_id, recipient_type, content)
    
    if not save_message or save_message.get('status') != 'success':
        emit('error_message', {'message': 'Failed to save message.'})
        print("SocketIO: Failed to save message.")
        return
    
    time_now = datetime.now().isoformat()
    message_send = {
        'sender_id': sender_id,
        'sender_type': sender_type,
        'recipient_id': recipient_id,
        'recipient_type': recipient_type,
        'content': content,
        'timestamp': time_now,
        'message_id': save_message.get('message_id'),
    }
    
    recipient_room = str(recipient_id)
    emit('new_message', message_send, room = recipient_room)
    print(f"SocketIO: New message sent to recipient ID {recipient_id} in room {recipient_room}.")
    # (session, data, save_message_logic, emit)

@socketio.on('group_message')
def handle_group_message(data : dict) -> None:
    """
    Handler for the custom 'group_message' event.

    Triggered when a client emits a 'group_message' event.
    Manages the sending of messages to an organization's group chat.

    Args:
        data (dict): The data object sent by the client. Expected to
                     contain at least:
                     - 'org_id': The ID of the destination organization group.
                     - 'content': The text content of the message.

    Logic:
    1. Identifies the sender (`sender_id`, `sender_type`) using `session`.
    2. Extracts `org_id` and `content` from `data`.
    3. Validates that the sender is authenticated and data is complete.
    4. **Authorization:** Verifies if the `sender_id` is a member of the
       target `org_id` (by calling `is_user_member_of_org_logic`).
    5. If authorized, calls `save_message_logic` to persist the message
       (using `org_id` as `recipient_id` and `'org'` as `recipient_type`).
    6. If saved successfully, emits a 'new_group_message' event with the
       message details to the organization's group room
       (`room=f'org_room_{org_id}'`).
    """
    sender_id = session.get('entity_id')
    sender_type = session.get('entity_type')
    
    if not sender_id or not sender_type:
        emit('error_message', {'message': 'Sender not authenticated.'})
        print("SocketIO: Sender not authenticated.")
        return
    
    org_id_str = data.get('recipient_id')
    content = data.get('content')
    
    if not org_id_str or not content:
        emit('error_message', {'message': 'Missing required fields.'})
        print("SocketIO: Missing required fields.")
        return
    
    try:
        org_id = int(org_id_str)
    except (ValueError, TypeError):
        emit('error_message', {'message': 'Invalid organization ID.'})
        print("SocketIO: Invalid organization ID.")
        return
    
    # Check if the user is a member of the organization
    is_member = False
    for org in get_user_orgs_logic(sender_id)['data']:
        if org_id == org['org_id']:
            is_member = True
            break
            
    if not is_member:
        emit('error_message', {'message': 'User is not a member of the organization.'})
        print("SocketIO: User is not a member of the organization.")
        return
    
    save_message = save_message_logic(sender_id, sender_type, org_id, 'org', content)
    
    if not save_message or save_message.get('status') != 'success':
        emit('error_message', {'message': 'Failed to save message.'})
        print("SocketIO: Failed to save message.")
        return
    
    time_now = datetime.now().isoformat()
    message_send = {
        'sender_id': sender_id,
        'sender_type': sender_type,
        'recipient_id': org_id,
        'recipient_type': 'org',
        'content': content,
        'timestamp': time_now,
        'message_id': save_message.get('message_id'),
    }
    
    group_room = f'org_room_{org_id}'
    emit('new_group_message', message_send, room = group_room)
    print(f"SocketIO: New group message sent to organization ID {org_id}")


## Messaging Logic Functions

def save_message_logic(sender_id: int, sender_type: str, recipient_id: int, recipient_type: str, content: str) -> dict:
    """
    function to save a message to the database.

    Calls the corresponding function in db_operator to persist the message.
    Handles both private and group messages based on recipient_type.

    Args:
        sender_id (int): ID of the message sender.
        sender_type (str): Type of the sender ('user' or 'org').
        recipient_id (int): ID of the message recipient (user or org ID).
        recipient_type (str): Type of the recipient ('user' or 'org').
        content (str): The text content of the message.

    Returns:
        dict: A dictionary containing the result from db_operator.save_message,
              typically {'status': 'success', 'message_id': <id>} on success,
              or {'status': 'error', 'message': <error_msg>} on failure.
    """
    
    result = db_operator.save_message(sender_id, sender_type, recipient_id, recipient_type, content)
    
    return result

def get_conversation_logic(user1_id: int, user1_type: str, user2_id: int, user2_type: str, limit) -> dict:
    """
    function to retrieve the message history between two specific entities.

    Calls the corresponding function in db_operator to fetch messages
    where either entity was the sender and the other the recipient.
    Typically used for loading private chat history.

    Args:
        user1_id (int): ID of the first entity.
        user1_type (str): Type of the first entity ('user' or 'org').
        user2_id (int): ID of the second entity.
        user2_type (str): Type of the second entity ('user' or 'org').
        limit (int): The maximum number of messages to retrieve.

    Returns:
        dict: A dictionary containing the result from db_operator.get_conversation,
              typically {'status': 'success', 'data': [<message_dict>, ...]} on success
              (where data can be an empty list if no messages exist),
              or {'status': 'error', 'message': <error_msg>} on failure.
    """
    
    result = db_operator.get_conversation(user1_id, user1_type, user2_id, user2_type, limit)
    
    return result

def get_group_conversation_logic(org_id: int, limit: int) -> list:
    """
    function to retrieve the message history for a specific organization group chat.

    Calls the corresponding function in db_operator (to be created)
    to fetch messages where the organization was the recipient.

    Args:
        org_id (int): The ID of the organization group.
        limit (int): The maximum number of messages to retrieve.

    Returns:
        dict: Result dictionary from the db_operator function, containing
              status and message data list or an error message.
    """
    
    result = db_operator.get_group_conversation(org_id, limit)
    return result
