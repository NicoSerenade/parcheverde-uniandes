'''Core application logic module'''

import db_operator

# This acts as a simple session state holder.
current_logged_in_entity = None #dict with logged entity data

#SESSION MANAGEMENT FUNCTIONS

def register_user(name, email, student_code, password, interests=None, career=None):
    """
    Registers a new user in the system.
    Returns a status message indicating success or failure.
    """
    result_id = db_operator.register_user(student_code, password, name, email, career, interests)
    if result_id:
        return {"status": "success", "message": f"User '{name}' registered successfully."}
    else:
        return {"status": "error", "message": "User registration failed. Email or student code might already exist, or email domain is invalid."}

def register_organization(name, email, description, password, interests=None):
    """
    Registers a new organization. Requires a standard user to be logged in.
    Returns a status message indicating success or failure.
    """
    global current_logged_in_entity
    if not current_logged_in_entity:
        return {"status": "error", "message": "Login required to register an organization."}
    
    if current_logged_in_entity.get('user_type') != 'user':
        return {"status": "error", "message": "Only standard users can register organizations."}

    creator_student_code = current_logged_in_entity.get('student_code')
    result_id = db_operator.register_org(creator_student_code, password, name, email, description, interests)
    if result_id:
        return {"status": "success", "message": f"Organization '{name}' registered successfully."}
    else:
        return {"status": "error", "message": "Organization registration failed. Email might already exist."}

def login(identifier, password):
    """
    Logs in a user (using student_code) or an organization (using name).
    Returns the entity's data dictionary on success, None on failure.
    """
    global current_logged_in_entity
    user_data = db_operator.authenticate_user(identifier, password)
    if user_data:
         current_logged_in_entity = user_data # Store session data
         return {
             "status": "success",
             "entity_type": "user",
             "user_id": user_data.get('user_id'),
             "name": user_data.get('name'),
             "email": user_data.get('email'),
             "student_code": user_data.get('student_code'),
             "points": user_data.get('points'),
             "interests": user_data.get('interests'),
             "career": user_data.get('career'),
             "creation_date": user_data.get("creation_date")
         }

    # Try organization authentication
    org_data = db_operator.authenticate_org(identifier, password)
    if org_data:
        current_logged_in_entity = org_data # Store session data
        print(f"Logic: Organization '{org_data.get('name')}' logged in.")
        return {
            "status": "success",
            "entity_type": "org",
            "org_id": org_data.get('org_id'),
            "name": org_data.get('name'),
            "email": org_data.get('email'),
            "description": org_data.get('description'),
            "points": org_data.get('points'),
            "interests": org_data.get('interests'),
            "creation_date": org_data.get("creation_date")
         }
    # If both fail
    current_logged_in_entity = None
    return {"status": "error", "message": "Invalid credentials or entity not found."}

def logout():
    """
    Logs out the currently logged-in entity.
    Returns a status message.
    """
    global current_logged_in_entity
    if current_logged_in_entity:
        current_logged_in_entity = None
        return {"status": "success", "message": "Successfully logged out."}
    else:
        return {"status": "info", "message": "No one is currently logged in."}

def get_current_session():
    """
    Returns the data dictionary of the currently logged-in entity.
    This is useful for the frontend to know who is logged in.
    Returns None if no one is logged in.
    """
    # Return a copy to prevent external modification of the session state
    return current_logged_in_entity.copy() if current_logged_in_entity else None

# --- Helper function to get ID and Type safely ---
def _get_session_details():
    """Internal helper to get ID and type from the current session."""
    if not current_logged_in_entity:
        return None, None, "Login required."

    entity_type = current_logged_in_entity.get('user_type')
    entity_id = None

    if entity_type == 'user':
        entity_id = current_logged_in_entity.get('user_id')
    elif entity_type == 'organization' or entity_type == 'org': # Allow 'org' as well
         # Ensure consistency in db_operator return keys ('org_id')
         entity_id = current_logged_in_entity.get('org_id')
    else:
        return None, None, "Unknown entity type in session."

    if not entity_id:
         return None, None, f"Could not find ID for entity type '{entity_type}'."

    return entity_id, entity_type, None # No error

# --- Core Features (Require Login) ---

def create_event_logic(title, description, event_datetime, location, event_type):
    """
    Allows the logged-in user or organization to create a new event.
    Returns a status message.
    """
    organizer_id, organizer_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}
        
    # Map 'organization' type from session back to 'org' if needed by db_operator
    db_organizer_type = 'org' if organizer_type == 'organization' else organizer_type 

    print(f"Logic: {organizer_type.capitalize()} ID {organizer_id} creating event '{title}'")
    result_id = db_operator.create_event(organizer_id, db_organizer_type, title, description, event_type, location, event_datetime)
    if result_id:
        return {"status": "success", "message": f"Event '{title}' created successfully."}
    else:
        return {"status": "error", "message": "Failed to create event."}

def register_for_event_logic(event_id):
    """
    Allows the logged-in user to register for an event.
    Returns a status message, potentially including points awarded.
    """
    user_id, user_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}
    if user_type != 'user':
        return {"status": "error", "message": "Only users can register for events."}

    print(f"Logic: User ID {user_id} registering for event ID {event_id}")
    # Assuming db_operator.join_event expects 'user' as user_type
    success = db_operator.join_event(event_id, user_id, 'user')

    if success:
        # Award points for joining (adjust points/reason as needed)
        points_reason = f"Joined event {event_id}"
        points_to_award = 5 # Example points
        award_result = award_points_logic(user_id, points_to_award, points_reason)
        # Include points message in the success response
        return {"status": "success", "message": f"Successfully registered for the event! {award_result.get('message', '')}"}
    else:
        return {"status": "error", "message": "Failed to register for the event. Maybe you are already registered, or the event doesn't exist."}

def add_item_for_exchange_logic(name, description, item_type, item_terms):
    """
    Allows the logged-in user to add an item for exchange.
    Returns a status message, potentially including points awarded.
    """
    owner_id, owner_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}
    if owner_type != 'user':
        return {"status": "error", "message": "Only users can add items for exchange."}

    print(f"Logic: User ID {owner_id} adding item '{name}'")
    item_id = db_operator.create_item(owner_id, name, description, item_type, item_terms)

    if item_id:
         # Award points for adding an item
         points_reason = f"Added item '{name}' for exchange"
         points_to_award = 2 # Example points
         award_result = award_points_logic(owner_id, points_to_award, points_reason)
         return {"status": "success", "message": f"Item '{name}' added successfully. {award_result.get('message', '')}"}
    else:
        return {"status": "error", "message": "Failed to add item."}

def add_map_point_logic(permission_code, name, latitude, longitude, point_type, description):
    """
    Allows logged-in users to add a map point if they have the permission code.
    Returns a status message.
    """
    adder_id, adder_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}
    result_id = db_operator.add_map_point(adder_id, permission_code, name, description, point_type, latitude, longitude)
    if result_id:
        return {"status": "success", "message": f"Map point '{name}' added successfully."}
    else:
        return {"status": "error", "message": "Failed to add map point. Check permissions or data."}

def update_my_profile_logic(new_data):
    """
    Updates the profile of the logged-in user or organization.
    Input `new_data` should be a dictionary of fields to update.
    Returns a status message.
    """
    entity_id, entity_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}

    # Filter data - prevent updating sensitive fields like ID, type, password directly here.
    allowed_user_fields = {'student_code', 'name', 'email', 'career', 'interests'}
    allowed_org_fields = {'name', 'email', 'description', 'interests'}

    update_payload = {}
    if entity_type == 'user':
        for key, value in new_data.items():
            if key in allowed_user_fields:
                update_payload[key] = value
        result = db_operator.update_user_profile(entity_id, **update_payload)
    elif entity_type == 'organization' or entity_type == 'org':
         for key, value in new_data.items():
            if key in allowed_org_fields:
                update_payload[key] = value
         # Ensure db_operator.update_org_profile uses org_id
         result = db_operator.update_org_profile(entity_id, **update_payload)
    else:
         return {"status": "error", "message": "Unknown entity type."} # Should be caught by _get_session_details

    if result:
        # Update local session cache if critical info like name/email changed
        for key, value in update_payload.items():
             if key in current_logged_in_entity:
                 current_logged_in_entity[key] = value
        return {"status": "success", "message": "Profile updated successfully."}
    else:
        return {"status": "error", "message": "Failed to update profile. Check data or email domain."}

def award_points_logic(user_id, points, reason=""):
     """
     Awards points to a specific user and checks for achievement unlocks.
     Primarily for internal use by other logic functions.
     Returns a dictionary indicating status and any unlocked achievement.
     """
     # Add permission checks if this needs to be exposed directly via API endpoint
     print(f"Logic: Awarding {points} points to user ID {user_id} for: {reason}")

     # db_operator.update_entity_points expects 'user' type for users
     achievement_unlocked = db_operator.update_entity_points(user_id, 'user', points)

     response = {"status": "success"}
     if achievement_unlocked is False: # Check for explicit failure indication if db_op uses it
         print(f"Logic Error: Failed to award points to user {user_id}.")
         response = {"status": "error", "message": "Failed to update points."}
     elif achievement_unlocked: # Achievement name string returned
          print(f"Logic: Awarded {points} points to user {user_id}. Unlocked: {achievement_unlocked}")
          response["message"] = f"Awarded {points} points. Unlocked: {achievement_unlocked}!"
          response["unlocked_achievement"] = achievement_unlocked
     else: # Success, no new achievement
          print(f"Logic: Awarded {points} points to user {user_id}. No new achievement.")
          response["message"] = f"Awarded {points} points."
     return response

# --- Data Retrieval Functions (Mostly Read-Only) ---

def view_all_events_logic():
    """
    Retrieves a list of all events.
    Returns the list of event dictionaries or an empty list on error.
    """
    print("Logic: Fetching all events.")

    events = db_operator.search_events()

    return events

def search_events_logic(query):
    """
    Searches for events matching the query in name or description.
    Returns the list of matching event dictionaries or an error message.
    """
    print(f"Logic: Searching events for '{query}'")
    events = db_operator.search_events(query=query)
    return {"status": "success", "data": events}

def view_exchange_items_logic():
    """
    Retrieves items currently available for exchange.
    Returns the list of item dictionaries or an empty list on error.
    """

    items = db_operator.get_available_items()
    return items

def get_map_points_logic():
    """
    Retrieves all map points.
    Returns the list of map point dictionaries or an error message.
    """
    print("Logic: Fetching all map points.")
    points = db_operator.get_map_points()
    return {"status": "success", "data": points}

def view_my_points_and_badges_logic():
     """
     Retrieves the points and unlocked achievements (badges) for the logged-in user.
     Returns a dictionary with points and a list of achievements, or an error message.
     """
     user_id, user_type, error = _get_session_details()
     if error:
        return {"status": "error", "message": error}
     if user_type != 'user':
         return {"status": "error", "message": "Only users have points and badges."}

     print(f"Logic: Fetching points and badges for user ID {user_id}")
     # Assumes db_operator.get_user_points_and_achievements is implemented correctly
     user_profile_data = db_operator.get_user_points_and_achievements(user_id)

     if user_profile_data:
         # user_profile_data should be like {'points': X, 'achievements': [...]}
         return {"status": "success", "data": user_profile_data}
     else:
         # Handle case where user exists but fetching failed, or user not found (already handled by db_op?)
         return {"status": "error", "message": "Could not retrieve points and badges for the user."}


# --- Item Exchange Logic ---

def request_exchange_logic(item_id, message=""):
    """
    Allows the logged-in user to request an exchange for an item listed by another user.
    Returns a status message dictionary.
    """
    requester_id, user_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}
    if user_type != 'user':
        return {"status": "error", "message": "Only users can request items for exchange."}

    print(f"Logic: User ID {requester_id} requesting item ID {item_id}")

    # --- Check Item Owner ---
    owner_id = db_operator.get_item_owner(item_id)
    if owner_id is None:
        return {"status": "error", "message": "Item not found or could not determine owner."}
    if owner_id == requester_id:
         return {"status": "error", "message": "You cannot request your own item."}
    # TODO: Add check here using db_operator to ensure item status is 'available'?

    # --- Create Request in DB ---
    exchange_id = db_operator.create_exchange_request(
        item_id=item_id,
        requester_id=requester_id,
        owner_id=owner_id,
        message=message
    )

    if exchange_id:
        # Optionally notify the owner (implementation detail outside this scope)
        return {"status": "success", "message": f"Exchange request sent successfully for item {item_id}."}
    else:
        return {"status": "error", "message": "Failed to send exchange request. Please try again."}

def accept_exchange_logic(exchange_id):
    """
    Allows the logged-in user (owner of the item) to accept a pending exchange request.
    Updates the exchange status and the item status.
    Returns a status message dictionary.
    """
    current_user_id, user_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}
    if user_type != 'user':
        return {"status": "error", "message": "Only users can accept exchange requests."}

    print(f"Logic: User ID {current_user_id} attempting to accept exchange ID {exchange_id}")

    # --- Get Request Details & Validate ---
    request_details = db_operator.get_exchange_request(exchange_id)
    if not request_details:
        return {"status": "error", "message": "Exchange request not found."}

    if request_details['owner_id'] != current_user_id:
         return {"status": "error", "message": "You are not authorized to accept this request."}
    if request_details['status'] != 'pending':
         return {"status": "error", "message": f"This request is not pending (current status: {request_details['status']})."}

    # --- Update DB ---
    # 1. Accept the exchange request
    success_exchange = db_operator.update_exchange_status(exchange_id, 'accepted')

    # 2. Mark the item as exchanged if request acceptance was successful
    success_item = False
    if success_exchange:
        item_id = request_details['item_id']
        # update_item_status already exists in db_operator.py
        success_item = db_operator.update_item_status(item_id, 'exchanged')
        if not success_item:
             # Handle inconsistency - log error, maybe try to revert exchange status? (More complex)
             print(f"Logic WARNING: Accepted exchange {exchange_id} but failed to update item {item_id} status.")

    # --- Format Response ---
    if success_exchange and success_item:
        # Optional: Award points, notify requester
        return {"status": "success", "message": f"Exchange request {exchange_id} accepted and item status updated."}
    elif success_exchange:
        # Exchange updated but item failed - inform user but maybe flag for admin review
        return {"status": "warning", "message": f"Exchange request {exchange_id} accepted, but there was an issue updating the item's status."}
    else:
        # Failed to update the exchange request status itself
        return {"status": "error", "message": "Failed to accept exchange request."}


def reject_exchange_logic(exchange_id):
    """
    Allows the logged-in user (owner of the item) to reject a pending exchange request.
    Updates the exchange status.
    Returns a status message dictionary.
    """
    current_user_id, user_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}
    if user_type != 'user':
        return {"status": "error", "message": "Only users can reject exchange requests."}

    print(f"Logic: User ID {current_user_id} attempting to reject exchange ID {exchange_id}")

    # --- Get Request Details & Validate ---
    request_details = db_operator.get_exchange_request(exchange_id)
    if not request_details:
        return {"status": "error", "message": "Exchange request not found."}

    if request_details['owner_id'] != current_user_id:
         return {"status": "error", "message": "You are not authorized to reject this request."}
    if request_details['status'] != 'pending':
         return {"status": "error", "message": f"This request is not pending (current status: {request_details['status']})."}

    # --- Update DB ---
    success = db_operator.update_exchange_status(exchange_id, 'rejected')

    # --- Format Response ---
    if success:
        # Optional: Notify requester
        return {"status": "success", "message": f"Exchange request {exchange_id} rejected successfully."}
    else:
        return {"status": "error", "message": "Failed to reject exchange request."}

def view_my_exchange_requests_logic(request_type='received'):
    """
    Allows the logged-in user to view their 'received' or 'sent' exchange requests.
    Returns a dictionary containing the status and a list of request details.
    """
    user_id, user_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}
    if user_type != 'user':
        return {"status": "error", "message": "Only users have exchange requests to view."}

    if request_type not in ['received', 'sent']:
        return {"status": "error", "message": "Invalid request type specified. Use 'received' or 'sent'."}

    print(f"Logic: User ID {user_id} viewing {request_type} exchange requests")

    # --- Get Data from DB ---
    requests_list = db_operator.get_user_exchange_requests(user_id, request_type)

    # --- Format Response ---
    if requests_list is None:
        # Indicates an error occurred during DB fetch
        return {"status": "error", "message": f"An error occurred while retrieving {request_type} requests."}
    else:
        # Return success status and the list (which might be empty)
        return {"status": "success", "data": requests_list}

# --- Organization Membership Logic ---

def join_org_logic(org_id):
    """
    Allows the logged-in user to join an organization.
    Returns a status message dictionary.
    """
    user_id, user_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}
    if user_type != 'user':
        return {"status": "error", "message": "Only users can join organizations."}

    print(f"Logic: User ID {user_id} attempting to join organization ID {org_id}")
    success = db_operator.join_org(org_id, user_id)

    if success:
        # Optionally award points for joining an org?
        # award_result = award_points_logic(user_id, 1, f"Joined organization {org_id}")
        return {"status": "success", "message": f"Successfully joined organization."} # {award_result.get('message', '')}"}
    else:
        return {"status": "error", "message": "Failed to join organization. Maybe you are already a member or the organization doesn't exist."}

def leave_org_logic(org_id):
    """
    Allows the logged-in user to leave an organization.
    Returns a status message dictionary.
    """
    user_id, user_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}
    if user_type != 'user':
        return {"status": "error", "message": "Only users can leave organizations."}

    print(f"Logic: User ID {user_id} attempting to leave organization ID {org_id}")
    success = db_operator.leave_org(org_id, user_id)

    if success:
        return {"status": "success", "message": "Successfully left the organization."}
    else:
        return {"status": "error", "message": "Failed to leave organization. Maybe you were not a member or the organization doesn't exist."}

def get_org_members_logic(org_id):
    """
    Retrieves the list of members for a given organization.
    Accessible to any logged-in user (or adjust permissions as needed).
    Returns a dictionary with status and data (list of members).
    """
    entity_id, entity_type, error = _get_session_details()
    if error:
        # Allow viewing even if not logged in? Decide based on requirements.
        # If login is required, uncomment the following line:
        # return {"status": "error", "message": error}
        print(f"Logic: Public request (or failed session) to view members for org ID {org_id}")
    else:
         print(f"Logic: {entity_type.capitalize()} ID {entity_id} viewing members for org ID {org_id}")

    members = db_operator.get_org_members(org_id)
    if members is not None: # Check if db_operator returns None on error vs empty list
        return {"status": "success", "data": members}
    else:
        # This suggests an issue within db_operator or org_id is invalid
        return {"status": "error", "message": "Could not retrieve organization members."}

# --- Event Management Logic ---

def get_event_participants_logic(event_id):
    """
    Retrieves the list of participants (users and orgs) for a given event.
    Accessible to any logged-in user (adjust permissions as needed).
    Returns a dictionary with status and data (dict with 'users' and 'orgs' lists).
    """
    entity_id, entity_type, error = _get_session_details()
    if error:
        # Allow viewing even if not logged in? Decide based on requirements.
        # If login is required, uncomment the following line:
        # return {"status": "error", "message": error}
         print(f"Logic: Public request (or failed session) to view participants for event ID {event_id}")
    else:
         print(f"Logic: {entity_type.capitalize()} ID {entity_id} viewing participants for event ID {event_id}")


    participants = db_operator.get_event_participants(event_id)
    if participants is not None: # Check if db_operator returns None on error
         # participants should be {'users': [...], 'orgs': [...]}
         return {"status": "success", "data": participants}
    else:
         # This suggests an issue within db_operator or event_id is invalid
         return {"status": "error", "message": "Could not retrieve event participants."}


def leave_event_logic(event_id):
    """
    Allows the logged-in user or organization to leave an event they are registered for.
    Returns a status message dictionary.
    """
    entity_id, entity_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}

    # Map session type ('organization') to db type ('org') if necessary
    db_entity_type = 'org' if entity_type == 'organization' else entity_type

    print(f"Logic: {entity_type.capitalize()} ID {entity_id} attempting to leave event ID {event_id}")
    success = db_operator.leave_event(event_id, entity_id, db_entity_type)

    if success:
        return {"status": "success", "message": "Successfully left the event."}
    else:
        return {"status": "error", "message": "Failed to leave event. Maybe you were not registered or the event doesn't exist."}

def delete_event_logic(event_id):
    """
    Allows the logged-in user or organization (if they are the organizer) to delete an event.
    Returns a status message dictionary.
    """
    entity_id, entity_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}

    # Map session type ('organization') to db type ('org') if necessary
    db_entity_type = 'org' if entity_type == 'organization' else entity_type

    print(f"Logic: {entity_type.capitalize()} ID {entity_id} attempting to delete event ID {event_id}")
    # db_operator.delete_event handles the check if the entity is the organizer
    success = db_operator.delete_event(event_id, entity_id, db_entity_type)

    if success:
        return {"status": "success", "message": "Event deleted successfully."}
    else:
        # db_operator might print specific errors (not found, not authorized)
        return {"status": "error", "message": "Failed to delete event. It might not exist or you are not the organizer."}

def mark_event_attendance_logic(event_id, participant_id, participant_type):
    """
    Allows the logged-in event organizer or an admin to mark attendance for a participant.
    Awards points upon successful marking.
    Returns a status message dictionary, potentially including achievement info.
    """
    marker_id, marker_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}

    # --- Permission Check: Only Admin or Organizer ---
    is_admin = marker_type == 'admin'
    is_organizer = False

    # Fetch event details to check organizer (could be cached or optimized)
    # Simplified: Assume db_operator.mark_event_attendance needs organizer/admin check first
    # Or enhance db_operator.mark_event_attendance to take marker_id/type and do the check
    # For now, let's assume only admins can do this via this logic function for simplicity,
    # or that the frontend only shows this button to the organizer.
    # A more robust implementation fetches the event organizer ID/Type from db first.

    if not is_admin:
         # TODO: Add check if marker_id/marker_type matches the event's organizer_id/organizer_type
         # event_details = db_operator.search_events(event_id=event_id) # Need a get_event_by_id function
         # if not event_details or event_details[0]['organizer_id'] != marker_id or event_details[0]['organizer_type'] != ('org' if marker_type == 'organization' else marker_type):
              return {"status": "error", "message": "Permission denied. Only the event organizer or admin can mark attendance."}

    print(f"Logic: {marker_type.capitalize()} ID {marker_id} marking attendance for {participant_type} ID {participant_id} at event ID {event_id}")

    # Map participant_type 'organization' to 'org' if needed by db_operator
    db_participant_type = 'org' if participant_type == 'organization' else participant_type

    success = db_operator.mark_event_attendance(event_id, participant_id, db_participant_type)

    if success:
         # db_operator.mark_event_attendance handles points and achievements internally now
         # We just report success from the logic layer
         # We might want db_operator to return unlocked achievement name here if needed
         return {"status": "success", "message": f"Attendance marked successfully for {participant_type} ID {participant_id}. Points awarded if applicable."}
    else:
         return {"status": "error", "message": f"Failed to mark attendance. Ensure the participant is registered and the event exists."}


# --- Item Management Logic ---

def delete_my_item_logic(item_id):
    """
    Allows the logged-in user to delete (mark as 'removed') their own item.
    Returns a status message dictionary.
    """
    user_id, user_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}
    if user_type != 'user':
        return {"status": "error", "message": "Only users can manage items."}

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

# --- User/Organization Account Deletion ---

def delete_my_account_logic(password):
    """
    Allows the logged-in user or organization creator to delete their account after password verification.
    Logs out the user upon successful deletion.
    Returns a status message dictionary.
    """
    entity_id, entity_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}

    success = False
    identifier_for_delete = None

    print(f"Logic: {entity_type.capitalize()} ID {entity_id} attempting account deletion.")

    if entity_type == 'user':
        student_code = current_logged_in_entity.get('student_code')
        if not student_code:
             return {"status": "error", "message": "Could not retrieve student code for deletion."}
        identifier_for_delete = student_code
        success = db_operator.delete_my_user(student_code, password)
    elif entity_type == 'organization' or entity_type == 'org':
         creator_student_code = current_logged_in_entity.get('creator_student_code')
         if not creator_student_code:
             return {"status": "error", "message": "Could not retrieve creator student code for deletion."}
         # Org deletion in db_operator uses creator_student_code for lookup
         identifier_for_delete = creator_student_code
         success = db_operator.delete_my_org(creator_student_code, password)
    else:
        return {"status": "error", "message": "Unknown entity type for deletion."}


    if success:
        print(f"Logic: Account associated with identifier {identifier_for_delete} deleted successfully. Logging out.")
        logout() # Log out after successful deletion
        return {"status": "success", "message": "Account deleted successfully."}
    else:
        # db_operator prints specific errors (pw mismatch, not found)
        return {"status": "error", "message": "Account deletion failed. Password may be incorrect or account not found."}


# --- Challenge Logic ---

def search_challenges_logic():
    """
    Retrieves available challenges for the logged-in entity's type (user or org).
    Returns a dictionary with status and data (list of challenges).
    """
    entity_id, entity_type, error = _get_session_details()
    if error:
        # Decide if anonymous users can see challenges. If so, default to 'user'?
        # For now, require login.
         return {"status": "error", "message": error}

    # Map session type ('organization') to db type ('org') if necessary
    db_entity_type = 'org' if entity_type == 'organization' else entity_type

    print(f"Logic: Fetching available challenges for {db_entity_type}s.")
    challenges = db_operator.search_challenges(db_entity_type)

    if challenges is not None: # Check if db_operator returns None on error
        return {"status": "success", "data": challenges}
    else:
        return {"status": "error", "message": f"Could not retrieve challenges for {db_entity_type}s."}

def join_challenge_logic(challenge_id):
    """
    Allows the logged-in user or organization to join a challenge.
    Returns a status message dictionary.
    """
    entity_id, entity_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}

    # Map session type ('organization') to db type ('org') if necessary
    db_entity_type = 'org' if entity_type == 'organization' else entity_type

    print(f"Logic: {entity_type.capitalize()} ID {entity_id} attempting to join challenge ID {challenge_id}")
    success = db_operator.join_challenge(entity_id, db_entity_type, challenge_id)

    if success:
        return {"status": "success", "message": "Successfully joined the challenge."}
    else:
        # db_operator might print specific errors (already joined, not found)
        return {"status": "error", "message": "Failed to join challenge. You might already be participating, or the challenge is invalid for your type."}


def get_my_active_challenges_logic():
    """
    Retrieves the active challenges and progress for the logged-in user or organization.
    Returns a dictionary with status and data (list of active challenges).
    """
    entity_id, entity_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}

    # Map session type ('organization') to db type ('org') if necessary
    db_entity_type = 'org' if entity_type == 'organization' else entity_type

    print(f"Logic: Fetching active challenges for {entity_type.capitalize()} ID {entity_id}")
    active_challenges = db_operator.get_active_challenges(entity_id, db_entity_type)

    if active_challenges is not None: # Check if db_operator returns None on error
        return {"status": "success", "data": active_challenges}
    else:
        return {"status": "error", "message": "Could not retrieve active challenges."}


# --- Achievement Logic ---

def search_achievements_logic():
    """
    Retrieves all possible achievements for the logged-in entity's type (user or org).
    Returns a dictionary with status and data (list of achievements).
    """
    entity_id, entity_type, error = _get_session_details()
    if error:
        # Allow anonymous viewing? Default to user? Require login for now.
         return {"status": "error", "message": error}

    # Map session type ('organization') to db type ('org') if necessary
    db_entity_type = 'org' if entity_type == 'organization' else entity_type

    print(f"Logic: Fetching all possible achievements for {db_entity_type}s.")
    achievements = db_operator.search_achievements(db_entity_type)

    if achievements is not None: # Check if db_operator returns None on error
        return {"status": "success", "data": achievements}
    else:
        return {"status": "error", "message": f"Could not retrieve achievements for {db_entity_type}s."}


# --- Searching Logic ---

def search_users_logic(query=None, career=None, interests=None):
    """
    Searches for users based on query, career, or interests.
    Accessible to any logged-in user.
    Returns a dictionary with status and data (list of users).
    """
    entity_id, entity_type, error = _get_session_details()
    if error:
        # Allow anonymous search? Require login for now.
         return {"status": "error", "message": error}

    print(f"Logic: {entity_type.capitalize()} ID {entity_id} searching users (query='{query}', career='{career}', interests='{interests}')")
    users = db_operator.search_users(query=query, career=career, interests=interests)

    if users is not None:
        return {"status": "success", "data": users}
    else:
        return {"status": "error", "message": "Failed to search users."}

def search_orgs_logic(query=None, interests=None, sort_by=None):
    """
    Searches for organizations based on query, interests, or sorting.
    Accessible to any logged-in user.
    Returns a dictionary with status and data (list of organizations).
    """
    entity_id, entity_type, error = _get_session_details()
    if error:
        # Allow anonymous search? Require login for now.
         return {"status": "error", "message": error}

    print(f"Logic: {entity_type.capitalize()} ID {entity_id} searching orgs (query='{query}', interests='{interests}', sort='{sort_by}')")
    orgs = db_operator.search_orgs(query=query, interests=interests, sort_by=sort_by)

    if orgs is not None:
        return {"status": "success", "data": orgs}
    else:
        return {"status": "error", "message": "Failed to search organizations."}

# --- Map Point Logic ---

def delete_map_point_logic(point_id):
    """
    Allows the logged-in user (if admin or creator) to delete a map point.
    Returns a status message dictionary.
    """
    entity_id, entity_type, error = _get_session_details()
    if error:
        return {"status": "error", "message": error}

    # Map session type ('organization') to db type ('org') if necessary
    # Although add_map_point uses 'store', delete uses creator_id, so user_type mapping less critical here
    # db_operator.delete_map_point handles admin override and creator check
    db_entity_type = 'org' if entity_type == 'organization' else entity_type


    print(f"Logic: {entity_type.capitalize()} ID {entity_id} attempting to delete map point ID {point_id}")
    success = db_operator.delete_map_point(entity_id, db_entity_type, point_id) # Pass user type for permission check in db_op

    if success:
        return {"status": "success", "message": "Map point deleted successfully."}
    else:
        # db_operator prints specific errors (not found, permission denied)
        return {"status": "error", "message": "Failed to delete map point. It might not exist or you lack permission."}


# --- Admin Specific Logic ---
# These functions MUST include robust checks for admin privileges

def _is_admin_session():
    """Internal helper to check if the current session is for an admin."""
    if not current_logged_in_entity:
        return False, {"status": "error", "message": "Login required."}
    if current_logged_in_entity.get('user_type') != 'admin':
         return False, {"status": "error", "message": "Admin privileges required."}
    return True, None

def admin_delete_user_logic(user_id_to_delete):
    """
    Allows an admin to delete any user account.
    Returns a status message dictionary.
    """
    is_admin, error_response = _is_admin_session()
    if not is_admin:
        return error_response

    admin_id = current_logged_in_entity.get('user_id')
    print(f"Logic: Admin ID {admin_id} attempting to delete user ID {user_id_to_delete}")

    if admin_id == user_id_to_delete:
         return {"status": "error", "message": "Admin cannot delete their own account using this function."}

    success = db_operator.delete_user_by_id(user_id_to_delete)
    if success:
        return {"status": "success", "message": f"User ID {user_id_to_delete} deleted successfully."}
    else:
        return {"status": "error", "message": f"Failed to delete user ID {user_id_to_delete}. User might not exist."}

def admin_delete_org_logic(org_id_to_delete):
    """
    Allows an admin to delete any organization account.
    Returns a status message dictionary.
    """
    is_admin, error_response = _is_admin_session()
    if not is_admin:
        return error_response

    admin_id = current_logged_in_entity.get('user_id')
    print(f"Logic: Admin ID {admin_id} attempting to delete organization ID {org_id_to_delete}")

    success = db_operator.delete_org_by_id(org_id_to_delete)
    if success:
        return {"status": "success", "message": f"Organization ID {org_id_to_delete} deleted successfully."}
    else:
        return {"status": "error", "message": f"Failed to delete organization ID {org_id_to_delete}. Organization might not exist."}

def admin_create_achievement_logic(name, description, points_required, badge_icon, achievement_user_type):
    """
    Allows an admin to create a new achievement for users or orgs.
    Returns a status message dictionary.
    """
    is_admin, error_response = _is_admin_session()
    if not is_admin:
        return error_response

    admin_id = current_logged_in_entity.get('user_id')
    db_achievement_type = 'org' if achievement_user_type == 'organization' else achievement_user_type
    if db_achievement_type not in ['user', 'org']:
        return {"status": "error", "message": "Invalid achievement user type. Must be 'user' or 'org'."}

    print(f"Logic: Admin ID {admin_id} creating achievement '{name}' for {db_achievement_type}s")
    achievement_id = db_operator.create_achievement(name, description, points_required, badge_icon, db_achievement_type)

    if achievement_id:
        return {"status": "success", "message": f"Achievement '{name}' created successfully with ID {achievement_id}."}
    else:
        return {"status": "error", "message": "Failed to create achievement."}

def admin_delete_achievement_logic(achievement_id, achievement_user_type):
    """
    Allows an admin to delete an achievement for users or orgs.
    Returns a status message dictionary.
    """
    is_admin, error_response = _is_admin_session()
    if not is_admin:
        return error_response

    admin_id = current_logged_in_entity.get('user_id')
    db_achievement_type = 'org' if achievement_user_type == 'organization' else achievement_user_type
    if db_achievement_type not in ['user', 'org']:
        return {"status": "error", "message": "Invalid achievement user type. Must be 'user' or 'org'."}

    print(f"Logic: Admin ID {admin_id} deleting achievement ID {achievement_id} for {db_achievement_type}s")
    success = db_operator.delete_achievement(achievement_id, db_achievement_type)

    if success:
        return {"status": "success", "message": f"Achievement ID {achievement_id} deleted successfully."}
    else:
        return {"status": "error", "message": f"Failed to delete achievement ID {achievement_id}. It might not exist for the specified type."}

def admin_create_challenge_logic(name, description, goal_type, goal_target, points_reward, time_allowed, challenge_user_type):
    """
    Allows an admin to create a new challenge for users or orgs.
    Returns a status message dictionary.
    """
    is_admin, error_response = _is_admin_session()
    if not is_admin:
        return error_response

    admin_id = current_logged_in_entity.get('user_id')
    db_challenge_type = 'org' if challenge_user_type == 'organization' else challenge_user_type
    if db_challenge_type not in ['user', 'org']:
        return {"status": "error", "message": "Invalid challenge user type. Must be 'user' or 'org'."}

    print(f"Logic: Admin ID {admin_id} creating challenge '{name}' for {db_challenge_type}s")
    challenge_id = db_operator.create_challenge(name, description, goal_type, goal_target, points_reward, time_allowed, db_challenge_type)

    if challenge_id:
        return {"status": "success", "message": f"Challenge '{name}' created successfully with ID {challenge_id}."}
    else:
        return {"status": "error", "message": "Failed to create challenge."}

def admin_delete_challenge_logic(challenge_id, challenge_user_type):
    """
    Allows an admin to delete a challenge for users or orgs.
    Returns a status message dictionary.
    """
    is_admin, error_response = _is_admin_session()
    if not is_admin:
        return error_response

    admin_id = current_logged_in_entity.get('user_id')
    db_challenge_type = 'org' if challenge_user_type == 'organization' else challenge_user_type
    if db_challenge_type not in ['user', 'org']:
        return {"status": "error", "message": "Invalid challenge user type. Must be 'user' or 'org'."}

    print(f"Logic: Admin ID {admin_id} deleting challenge ID {challenge_id} for {db_challenge_type}s")
    success = db_operator.delete_challenge(challenge_id, db_challenge_type)

    if success:
        return {"status": "success", "message": f"Challenge ID {challenge_id} deleted successfully."}
    else:
        return {"status": "error", "message": f"Failed to delete challenge ID {challenge_id}. It might not exist for the specified type."}


# --- Initialization Message ---
print("Logic Module Loaded and Ready.")