'''Core application logic module'''

import db_operator
import sqlite3 # Import sqlite3 for error handling if needed in modified functions
import db_conn # Import db_conn for direct DB access in some functions

# --- Session Management Removed ---
# Global variable 'current_logged_in_entity' has been removed.
# Session state will now be managed by Flask's session mechanism in app.py.
# Functions 'get_current_session' and '_get_session_details' have been removed.

# --- Authentication Functions ---

def register_user(name, email, student_code, password, interests=None, career=None):
    """
    Registers a new user in the system.
    Returns a status message indicating success or failure.
    """
    # No change needed here as it didn't depend on session state
    result_id = db_operator.register_user(student_code, password, name, email, career, interests)
    if result_id:
        return {"status": "success", "message": f"User '{name}' registered successfully."}
    else:
        # Added specific check for duplicate error if db_operator raises it
        # Note: This requires db_operator to potentially raise specific errors
        # or return more detailed failure info. For now, keeping generic message.
        return {"status": "error", "message": "User registration failed. Email, student code might exist, or email domain is invalid."}

def register_organization(creator_student_code, name, email, description, password, interests=None):
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
    """
    # Removed check for global current_logged_in_entity
    # The check if the creator is a standard user should now happen in app.py before calling this.
    print(f"Logic: User with student code {creator_student_code} attempting to register org '{name}'")
    result_id = db_operator.register_org(creator_student_code, password, name, email, description, interests)
    if result_id:
        return {"status": "success", "message": f"Organization '{name}' registered successfully."}
    else:
        return {"status": "error", "message": "Organization registration failed. Email might already exist."}

def login(identifier, password):
    """
    Authenticates a user (using student_code) or an organization (using name).
    Returns a dictionary containing status and entity data on success,
    or status and error message on failure.
    It no longer manages global session state.
    """
    # Removed global current_logged_in_entity management
    user_data = db_operator.authenticate_user(identifier, password)
    if user_data:
         # Return data needed for Flask session setup
         return {
             "status": "success",
             "entity_type": "user", # Consistent type name
             "user_id": user_data.get('user_id'),
             "student_code": user_data.get('student_code'), # Keep student_code
             "name": user_data.get('name'),
             "email": user_data.get('email'),
             "points": user_data.get('points'),
             "interests": user_data.get('interests'),
             "career": user_data.get('career'),
             "creation_date": user_data.get("creation_date")
             # Add other necessary fields if needed for session
         }

    org_data = db_operator.authenticate_org(identifier, password)
    if org_data:
        # Return data needed for Flask session setup
        print(f"Logic: Organization '{org_data.get('name')}' authenticated.")
        return {
            "status": "success",
            "entity_type": "organization", # Consistent type name
            "org_id": org_data.get('org_id'),
            "name": org_data.get('name'),
            "email": org_data.get('email'),
            "description": org_data.get('description'),
            "points": org_data.get('points'),
            "interests": org_data.get('interests'),
            "creation_date": org_data.get("creation_date")
            # Add other necessary fields if needed for session
         }

    # If both fail
    print(f"Logic: Login failed for identifier '{identifier}'")
    return {"status": "error", "message": "Invalid credentials or entity not found."}

def logout():
    """
    This function is now a placeholder.
    Actual logout (clearing the Flask session) should be handled in app.py.
    """
    # Removed global current_logged_in_entity management
    print("Logic: Logout called (Session clearing happens in app.py).")
    return {"status": "success", "message": "Logout processed (session cleared by Flask)."}

# --- Helper function _get_session_details REMOVED ---
# Functions below now accept entity_id and entity_type as arguments

# --- Core Features (Now Require Entity Info as Args) ---

def create_event_logic(organizer_id, organizer_type, title, description, event_datetime, location, event_type):
    """
    Allows a user or organization (specified by ID and type) to create a new event.
    Returns a status message.

    Args:
        organizer_id (int): The ID of the user or organization creating the event.
        organizer_type (str): 'user' or 'organization'.
        title (str): Event title.
        description (str): Event description.
        event_datetime (str): Event date and time.
        location (str): Event location.
        event_type (str): Event type.
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
        return {"status": "success", "message": f"Event '{title}' created successfully."}
    else:
        # Consider more specific error messages based on db_operator return/exceptions
        return {"status": "error", "message": "Failed to create event."}

def register_for_event_logic(user_id, event_id):
    """
    Allows a specified user to register for an event.
    Returns a status message, potentially including points awarded.

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
        points_reason = f"Joined event {event_id}"
        points_to_award = 5 # Example points
        # Pass user_id to award_points_logic
        award_result = award_points_logic(user_id, points_to_award, points_reason)
        return {"status": "success", "message": f"Successfully registered for the event! {award_result.get('message', '')}"}
    else:
        # Consider more specific errors (already registered, event full, event not found)
        return {"status": "error", "message": "Failed to register for the event. Maybe already registered, or the event doesn't exist."}

def add_item_for_exchange_logic(owner_id, name, description, item_type, item_terms):
    """
    Allows a specified user to add an item for exchange.
    Returns a status message, potentially including points awarded.

    Args:
        owner_id (int): The user_id of the item owner.
        name (str): Item name.
        description (str): Item description.
        item_type (str): Item type.
        item_terms (str): Item terms.
    """
    # Removed _get_session_details call
    # Type check (ensuring it's a user) should happen in app.py
    if not owner_id:
        return {"status": "error", "message": "Owner ID is required."}

    print(f"Logic: User ID {owner_id} adding item '{name}'")
    item_id = db_operator.create_item(owner_id, name, description, item_type, item_terms)

    if item_id:
         points_reason = f"Added item '{name}' for exchange"
         points_to_award = 2 # Example points
         # Pass owner_id to award_points_logic
         award_result = award_points_logic(owner_id, points_to_award, points_reason)
         return {"status": "success", "message": f"Item '{name}' added successfully. {award_result.get('message', '')}"}
    else:
        return {"status": "error", "message": "Failed to add item."}


def add_map_point_logic(adder_id, adder_type, permission_code, name, latitude, longitude, point_type, description):
    """
    Allows logged-in users/orgs (specified by ID/type) to add a map point if they have the permission code.
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
    # Removed _get_session_details call
    if not adder_id or not adder_type:
        return {"status": "error", "message": "Adder ID and type are required."}

    # Basic permission check (could be more complex)
    # TODO: Move permission check logic here or confirm db_operator handles it
    # For now, assuming db_operator handles the permission check
    print(f"Logic: {adder_type.capitalize()} ID {adder_id} attempting to add map point '{name}'")
    result_id = db_operator.add_map_point(adder_id, permission_code, name, description, point_type, latitude, longitude)

    if result_id:
        return {"status": "success", "message": f"Map point '{name}' added successfully."}
    else:
        # Provide more specific feedback if possible
        return {"status": "error", "message": "Failed to add map point. Check permissions, data, or if the point already exists."}


def update_my_profile_logic(entity_id, entity_type, new_data):
    """
    Updates the profile of the specified user or organization.
    Input `new_data` should be a dictionary of fields to update.
    Returns a status message.

    Args:
        entity_id (int): The ID of the user or organization to update.
        entity_type (str): 'user' or 'organization'.
        new_data (dict): Dictionary of fields to update.
    """
    # Removed _get_session_details call
    if not entity_id or not entity_type:
        return {"status": "error", "message": "Entity ID and type are required."}

    allowed_user_fields = {'student_code', 'name', 'email', 'career', 'interests'} # Removed password update here
    allowed_org_fields = {'name', 'email', 'description', 'interests'} # Removed password update here
    # Password updates should likely have a separate, dedicated function/route for security.

    update_payload = {}
    result = False # Initialize result

    if entity_type == 'user':
        for key, value in new_data.items():
            if key in allowed_user_fields:
                update_payload[key] = value
        if update_payload: # Only call DB if there's something to update
            print(f"Logic: Updating profile for User ID {entity_id} with data: {update_payload}")
            result = db_operator.update_user_profile(entity_id, **update_payload)
        else:
             return {"status": "info", "message": "No valid fields provided for update."}

    elif entity_type == 'organization':
         for key, value in new_data.items():
            if key in allowed_org_fields:
                update_payload[key] = value
         if update_payload: # Only call DB if there's something to update
             print(f"Logic: Updating profile for Org ID {entity_id} with data: {update_payload}")
             # Ensure db_operator.update_org_profile uses org_id correctly
             result = db_operator.update_org_profile(entity_id, **update_payload)
         else:
             return {"status": "info", "message": "No valid fields provided for update."}
    else:
         return {"status": "error", "message": f"Unknown entity type: {entity_type}"}

    if result:
        # Removed update of local session cache (current_logged_in_entity)
        # Flask session needs to be updated in app.py if critical info changes
        return {"status": "success", "message": "Profile updated successfully."}
    else:
        # db_operator might return False even if payload was empty, check logic
        if not update_payload:
             # This case should have been caught above, but as a safeguard:
             return {"status": "info", "message": "No valid fields provided for update."}
        else:
             return {"status": "error", "message": "Failed to update profile. Check data or if email/name constraints violated."}

def award_points_logic(user_id, points, reason=""):
     """
     Awards points to a specific user and checks for achievement unlocks.
     Primarily for internal use by other logic functions.
     Returns a dictionary indicating status and any unlocked achievement.
     Session points are NOT updated here; must be done in app.py after calling this.
     """
     # Removed global current_logged_in_entity usage
     if not user_id:
          print("Logic Error: award_points called without user_id")
          return {"status": "error", "message": "User ID is required to award points."}

     print(f"Logic: Awarding {points} points to user ID {user_id} for: {reason}")

     # db_operator.update_entity_points expects 'user' type for users
     # It returns the name of a newly unlocked achievement or None, or False on error
     achievement_unlocked = db_operator.update_entity_points(user_id, 'user', points)

     response = {"status": "success"}
     if achievement_unlocked is False: # Check for explicit failure from db_operator
         print(f"Logic Error: Failed to award points to user {user_id}.")
         response = {"status": "error", "message": "Failed to update points in database."}
     else:
          # --- Session cache update REMOVED ---
          # This needs to happen in app.py using the Flask session object

          # --- Format response message ---
          if isinstance(achievement_unlocked, str): # Achievement name string returned
               print(f"Logic: Awarded {points} points to user {user_id}. Unlocked: {achievement_unlocked}")
               response["message"] = f"Awarded {points} points. Unlocked: {achievement_unlocked}!"
               response["unlocked_achievement"] = achievement_unlocked
          else: # Success (achievement_unlocked is None), no new achievement
               print(f"Logic: Awarded {points} points to user {user_id}. No new achievement.")
               response["message"] = f"Awarded {points} points."
     return response

# --- Data Retrieval Functions (Mostly Read-Only) ---

def view_all_events_logic():
    """
    Retrieves a list of all events.
    Returns a dictionary with status and data.
    """
    print("Logic: Fetching all events.")
    events = db_operator.search_events()
    if events is None:  # DB error
        return {"status": "error", "message": "Failed to retrieve events."}
    else:
        return {"status": "success", "data": events}

def search_events_logic(query):
    """
    Searches for events matching the query in name or description.
    Returns a dictionary with status and data.
    """
    print(f"Logic: Searching events for '{query}'")
    events = db_operator.search_events(query=query)
    if events is None:  # DB error
        return {"status": "error", "message": f"Failed to search events for '{query}'."}
    else:
        return {"status": "success", "data": events}

def view_exchange_items_logic():
    """
    Retrieves items currently available for exchange.
    Returns a dictionary with status and data.
    """
    print("Logic: Fetching available exchange items.")
    items = db_operator.get_available_items()
    if items is None:  # DB error
        return {"status": "error", "message": "Failed to retrieve exchange items."}
    else:
        return {"status": "success", "data": items}

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

def view_my_points_and_badges_logic(user_id):
     """
     Retrieves the points and unlocked achievements (badges) for the specified user.
     Returns a dictionary with status and data, or status and error message.

     Args:
         user_id (int): The ID of the user whose details to fetch.
     """
     # Removed _get_session_details call
     # Type check ('user') should happen in app.py
     if not user_id:
        return {"status": "error", "message": "User ID is required."}

     print(f"Logic: Fetching points and badges for user ID {user_id}")
     user_profile_data = db_operator.get_user_points_and_achievements(user_id)

     if user_profile_data is not None: # Check for None, which might indicate DB error
         # user_profile_data should be like {'points': X, 'achievements': [...]}
         return {"status": "success", "data": user_profile_data}
     else:
         # Handle case where user exists but fetching failed, or user not found
         return {"status": "error", "message": "Could not retrieve points and badges for the user."}


# --- Item Exchange Logic ---

def request_exchange_logic(requester_id, item_id, message=""):
    """
    Allows the specified user to request an exchange for an item.
    Returns a status message dictionary.

    Args:
        requester_id (int): The user_id of the person requesting the item.
        item_id (int): The ID of the item being requested.
        message (str, optional): A message from the requester. Defaults to "".
    """
    # Removed _get_session_details call
    # Type check ('user') should happen in app.py
    if not requester_id:
        return {"status": "error", "message": "Requester ID is required."}

    print(f"Logic: User ID {requester_id} requesting item ID {item_id}")

    # Check Item Owner
    owner_id = db_operator.get_item_owner(item_id)
    if owner_id is None:
        return {"status": "error", "message": "Item not found or could not determine owner."}
    if owner_id == requester_id:
         return {"status": "error", "message": "You cannot request your own item."}
    # TODO: Add check using db_operator to ensure item status is 'available'?

    # Create Request in DB
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

def accept_exchange_logic(current_user_id, exchange_id):
    """
    Allows the specified user (owner of the item) to accept a pending exchange request.
    Updates the exchange status and the item status.
    Returns a status message dictionary.

     Args:
        current_user_id (int): The user_id attempting to accept the request.
        exchange_id (int): The ID of the exchange request.
    """
    # Removed _get_session_details call
    # Type check ('user') should happen in app.py
    if not current_user_id:
        return {"status": "error", "message": "User ID is required."}

    print(f"Logic: User ID {current_user_id} attempting to accept exchange ID {exchange_id}")

    # Get Request Details & Validate
    request_details = db_operator.get_exchange_request(exchange_id)
    if not request_details:
        return {"status": "error", "message": "Exchange request not found."}

    if request_details['owner_id'] != current_user_id:
         return {"status": "error", "message": "You are not authorized to accept this request."}
    if request_details['status'] != 'pending':
         return {"status": "error", "message": f"This request is not pending (current status: {request_details['status']})."}

    # Update DB
    success_exchange = db_operator.update_exchange_status(exchange_id, 'accepted')
    success_item = False
    if success_exchange:
        item_id = request_details['item_id']
        success_item = db_operator.update_item_status(item_id, 'exchanged')
        if not success_item:
             print(f"Logic WARNING: Accepted exchange {exchange_id} but failed to update item {item_id} status.")

    # Format Response
    if success_exchange and success_item:
        # Optional: Award points, notify requester
        return {"status": "success", "message": f"Exchange request {exchange_id} accepted and item status updated."}
    elif success_exchange:
        return {"status": "warning", "message": f"Exchange request {exchange_id} accepted, but there was an issue updating the item's status."}
    else:
        return {"status": "error", "message": "Failed to accept exchange request."}


def reject_exchange_logic(current_user_id, exchange_id):
    """
    Allows the specified user (owner of the item) to reject a pending exchange request.
    Updates the exchange status.
    Returns a status message dictionary.

     Args:
        current_user_id (int): The user_id attempting to reject the request.
        exchange_id (int): The ID of the exchange request.
    """
    # Removed _get_session_details call
    # Type check ('user') should happen in app.py
    if not current_user_id:
        return {"status": "error", "message": "User ID is required."}

    print(f"Logic: User ID {current_user_id} attempting to reject exchange ID {exchange_id}")

    # Get Request Details & Validate
    request_details = db_operator.get_exchange_request(exchange_id)
    if not request_details:
        return {"status": "error", "message": "Exchange request not found."}

    if request_details['owner_id'] != current_user_id:
         return {"status": "error", "message": "You are not authorized to reject this request."}
    if request_details['status'] != 'pending':
         return {"status": "error", "message": f"This request is not pending (current status: {request_details['status']})."}

    # Update DB
    success = db_operator.update_exchange_status(exchange_id, 'rejected')

    # Format Response
    if success:
        # Optional: Notify requester
        return {"status": "success", "message": f"Exchange request {exchange_id} rejected successfully."}
    else:
        return {"status": "error", "message": "Failed to reject exchange request."}

def view_my_exchange_requests_logic(user_id, request_type='received'):
    """
    Allows the specified user to view their 'received' or 'sent' exchange requests.
    Returns a dictionary containing the status and a list of request details.

     Args:
        user_id (int): The user_id whose requests to view.
        request_type (str): 'received' or 'sent'. Defaults to 'received'.
    """
    # Removed _get_session_details call
    # Type check ('user') should happen in app.py
    if not user_id:
        return {"status": "error", "message": "User ID is required."}

    if request_type not in ['received', 'sent']:
        return {"status": "error", "message": "Invalid request type specified. Use 'received' or 'sent'."}

    print(f"Logic: User ID {user_id} viewing {request_type} exchange requests")

    # Get Data from DB
    requests_list = db_operator.get_user_exchange_requests(user_id, request_type)

    # Format Response
    if requests_list is None: # Indicates DB error
        return {"status": "error", "message": f"An error occurred while retrieving {request_type} requests."}
    else:
        # Return success status and the list (which might be empty)
        return {"status": "success", "data": requests_list}


# --- Organization Membership Logic ---

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
        return {"status": "success", "message": "Successfully left the organization."}
    else:
        # Possible reasons: not a member, org doesn't exist, DB error
        return {"status": "error", "message": "Failed to leave organization. You might not be a member or the organization may not exist."}

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


# --- Event Management Logic ---

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
    db_entity_type = 'org' if entity_type == 'organization' else entity_type
    if db_entity_type not in ['user', 'org']:
         return {"status": "error", "message": f"Invalid entity type: {entity_type}"}


    print(f"Logic: {entity_type.capitalize()} ID {entity_id} attempting to leave event ID {event_id}")
    success = db_operator.leave_event(event_id, entity_id, db_entity_type)

    if success:
        return {"status": "success", "message": "Successfully left the event."}
    else:
        return {"status": "error", "message": "Failed to leave event. Maybe you were not registered or the event doesn't exist."}

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
    db_entity_type = 'org' if entity_type == 'organization' else entity_type
    if db_entity_type not in ['user', 'org']:
         return {"status": "error", "message": f"Invalid entity type: {entity_type}"}


    print(f"Logic: {entity_type.capitalize()} ID {entity_id} attempting to delete event ID {event_id}")
    # db_operator.delete_event handles the check if the entity is the organizer
    success = db_operator.delete_event(event_id, entity_id, db_entity_type)

    if success:
        return {"status": "success", "message": "Event deleted successfully."}
    else:
        # db_operator might print specific errors (not found, not authorized)
        return {"status": "error", "message": "Failed to delete event. It might not exist or you are not the organizer."}

def mark_event_attendance_logic(marker_id, marker_type, event_id, participant_id, participant_type):
    """
    Allows the specified event organizer or an admin to mark attendance for a participant.
    Awards points upon successful marking (points awarded within db_operator).
    Returns a status message dictionary.

    Args:
        marker_id (int): ID of the user/org marking attendance (must be admin or organizer).
        marker_type (str): 'user' or 'organization' (or 'admin').
        event_id (int): The ID of the event.
        participant_id (int): ID of the participant whose attendance is being marked.
        participant_type (str): 'user' or 'organization'.
    """
    # Permission validation
    if not marker_id or not marker_type:
        return {"status": "error", "message": "Marker ID and type are required."}
    if not participant_id or not participant_type:
        return {"status": "error", "message": "Participant ID and type are required."}

    # Map participant_type 'organization' to 'org' for db_operator
    db_participant_type = 'org' if participant_type == 'organization' else participant_type
    if db_participant_type not in ['user', 'org']:
        return {"status": "error", "message": f"Invalid participant type: {participant_type}"}

    # Map marker_type 'organization' to 'org' for db_operator
    db_marker_type = 'org' if marker_type == 'organization' else marker_type
    if db_marker_type not in ['user', 'org', 'admin']:
        return {"status": "error", "message": f"Invalid marker type: {marker_type}"}
    
    # Check if marker is authorized (event organizer or admin)
    authorized = False
    
    # Special case for admin (admin authorization would need separate check)
    if db_marker_type == 'admin':
        authorized = True  # Assuming admin can mark attendance for any event
    else:
        # Check if marker is the event organizer
        conn = db_conn.create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT organizer_id, organizer_type 
                FROM events 
                WHERE event_id = ?
                ''', (event_id,))
                
                event_data = cursor.fetchone()
                if event_data:
                    organizer_id, organizer_type = event_data
                    # Check if marker is the organizer
                    if (organizer_id == marker_id and 
                        ((organizer_type == db_marker_type) or 
                         (organizer_type == 'org' and db_marker_type == 'organization'))):
                        authorized = True
                
            except sqlite3.Error as e:
                print(f"Error checking event organizer: {e}")
                return {"status": "error", "message": "Database error while checking permissions."}
            finally:
                conn.close()
    
    if not authorized:
        return {"status": "error", "message": "You are not authorized to mark attendance for this event. Only the organizer can perform this action."}

    print(f"Logic: {marker_type.capitalize()} ID {marker_id} marking attendance for {participant_type} ID {participant_id} at event ID {event_id}")

    # Call db_operator function with the expected signature
    success = db_operator.mark_event_attendance(event_id, participant_id, db_participant_type)
    
    # Format response
    if not success:
        return {"status": "error", "message": "Failed to mark attendance. Check if participant is registered for the event."}
    else:
        message = "Attendance marked successfully."
        # Fetch user's points to include in response
        if db_participant_type == 'user':
            user_data = db_operator.get_user_points_and_achievements(participant_id)
            points = user_data.get('points', 0) if user_data else 0
            message += f" {points} total points."
        
        print(f"Logic: Attendance marked for {participant_type} {participant_id} at event {event_id}.")
        return {"status": "success", "message": message}


# --- Item Management Logic ---

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
        # This check is crucial and correctly placed here.
        return {"status": "error", "message": "You can only delete your own items."}

    # 2. Update status to 'removed' (or implement a real delete in db_operator if preferred)
    success = db_operator.update_item_status(item_id, 'removed')

    if success:
        return {"status": "success", "message": "Item removed successfully."}
    else:
        return {"status": "error", "message": "Failed to remove item."}


# --- Account Management Logic ---

def delete_my_account_logic(entity_id, entity_type, password):
    """
    Allows the specified user or organization to delete their own account after verifying password.
    Returns a status message dictionary.

    Args:
        entity_id (int): The ID of the user or organization to delete.
        entity_type (str): 'user' or 'organization'.
        password (str): The password of the account for verification.
    """
    # Removed _get_session_details call
    if not entity_id or not entity_type:
        return {"status": "error", "message": "Entity ID and type are required."}

    success = False
    print(f"Logic: {entity_type.capitalize()} ID {entity_id} attempting account deletion.")

    if entity_type == 'user':
        # db_operator.delete_my_user needs user_id and password
        # TODO: Confirm db_operator.delete_my_user signature and existence. Assuming it takes (user_id, password)
        # Need to fetch student_code first to call the assumed delete_my_user(student_code, password)
        user_data = db_operator.get_user_by_id(entity_id)
        if user_data and user_data.get('student_code'):
             student_code = user_data['student_code']
             # Now call delete_my_user which likely handles password verification
             success = db_operator.delete_my_user(student_code, password)
        else:
             print(f"Logic Error: Could not find student code for user {entity_id} to attempt deletion.")
             return {"status": "error", "message": "Account details not found for deletion."}

    elif entity_type == 'organization':
        # db_operator.delete_my_org needs org_id and password
        # TODO: Confirm db_operator.delete_my_org signature and existence. Assuming it takes (org_id, password)
        # Need to fetch creator_student_code first based on current db_operator structure?
        # Refactoring db_operator.delete_my_org to take org_id and password would be cleaner.
        # Assuming for now delete_my_org can work with org_id and password directly (needs db_op change).
        # success = db_operator.delete_my_org(entity_id, password) # Idealized call

        # Workaround based on likely current db_operator.delete_my_org(creator_student_code, password):
        org_data = db_operator.get_org_by_id(entity_id)
        if org_data and org_data.get('creator_student_code'):
             creator_code = org_data['creator_student_code']
             success = db_operator.delete_my_org(creator_code, password) # This feels wrong, it should verify org's password
             # MAJOR REFACTOR NEEDED: delete_my_org should take org_id and password, authenticate org, then delete.
             # This current workaround is insecure if creator leaves Uniandes.
             print("Logic WARNING: Org deletion logic using creator_student_code is potentially insecure and needs refactoring.")
        else:
             print(f"Logic Error: Could not find org details for org {entity_id} to attempt deletion.")
             return {"status": "error", "message": "Account details not found for deletion."}


    else:
         return {"status": "error", "message": f"Unknown entity type: {entity_type}"}

    if success:
        # Logout should be triggered in app.py after this returns success
        return {"status": "success", "message": "Account deleted successfully."}
    else:
        # Failure reasons: wrong password, DB error
        return {"status": "error", "message": "Failed to delete account. Please check your password."}


# --- Challenge Logic --- (Assuming these exist and may need session info)

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


    print(f"Logic: {entity_type.capitalize()} ID {entity_id} joining challenge ID {challenge_id}")
    success = db_operator.join_challenge(entity_id, db_type, challenge_id)
    if success:
        return {"status": "success", "message": "Successfully joined the challenge."}
    else:
        return {"status": "error", "message": "Failed to join challenge. Maybe already joined, challenge doesn't exist, or type mismatch."}

def get_my_active_challenges_logic(entity_id, entity_type):
    """
    Retrieves the active challenges for the specified user or organization.

     Args:
        entity_id (int): ID of the user/org.
        entity_type (str): 'user' or 'organization'.
    """
    if not entity_id or not entity_type:
        return {"status": "error", "message": "Entity ID and type are required."}
    db_type = 'org' if entity_type == 'organization' else 'user'
    if db_type not in ['user', 'org']:
         return {"status": "error", "message": f"Invalid entity type: {entity_type}"}

    print(f"Logic: Fetching active challenges for {entity_type.capitalize()} ID {entity_id}")
    active_challenges = db_operator.get_active_challenges(entity_id, db_type)
    if active_challenges is None: # DB error
        return {"status": "error", "message": "Could not retrieve active challenges."}
    else:
        return {"status": "success", "data": active_challenges}

# --- Achievement Logic --- (Assuming search doesn't need session)

def search_achievements_logic(entity_type):
    """
    Searches for all defined achievements for a given type.

     Args:
        entity_type (str): 'user' or 'organization'.
    """
    if entity_type not in ['user', 'organization']:
         return {"status": "error", "message": "Invalid entity type for achievements."}
    db_type = 'org' if entity_type == 'organization' else 'user'

    print(f"Logic: Searching all achievements for {entity_type}s")
    achievements = db_operator.search_achievements(user_type=db_type)
    if achievements is None: # DB error
        return {"status": "error", "message": f"Could not retrieve achievements for {entity_type}s."}
    else:
        return {"status": "success", "data": achievements}


# --- Search Logic --- (No session needed)

def search_users_logic(query=None, career=None, interests=None):
    """Searches users based on criteria."""
    print(f"Logic: Searching users with query='{query}', career='{career}', interests='{interests}'")
    users = db_operator.search_users(query=query, career=career, interests=interests)
    if users is None:
         return {"status": "error", "message": "Error searching users."}
    else:
        return {"status": "success", "data": users}

def search_orgs_logic(query=None, interests=None, sort_by=None):
    """Searches organizations based on criteria."""
    print(f"Logic: Searching orgs with query='{query}', interests='{interests}', sort_by='{sort_by}'")
    orgs = db_operator.search_orgs(query=query, interests=interests, sort_by=sort_by)
    if orgs is None:
         return {"status": "error", "message": "Error searching organizations."}
    else:
        return {"status": "success", "data": orgs}

# --- Map Point Deletion --- (Needs permission check)

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


# --- Admin Functions ---
# These functions require an admin check, which should now happen in app.py
# before calling these logic functions.

def _is_admin_session():
     """
     Placeholder/Removed. Admin checks must now happen in app.py
     """
     # This function should be removed or left as a non-functional placeholder.
     # Admin role check needs to be based on Flask session data in app.py routes.
     print("Logic Warning: _is_admin_session called, but admin checks must happen in app.py")
     return False # Always return False, forcing check in app.py

def admin_delete_user_logic(admin_id, user_id_to_delete):
    """
    Allows an admin (verified in app.py) to delete a user.

    Args:
        admin_id (int): The ID of the admin performing the action (for logging).
        user_id_to_delete (int): The ID of the user to delete.
    """
    # Admin check MUST happen in app.py route before calling this
    print(f"Logic: Admin ID {admin_id} deleting user ID {user_id_to_delete}")
    success = db_operator.delete_user_by_id(user_id_to_delete)
    if success:
        return {"status": "success", "message": f"User ID {user_id_to_delete} deleted successfully."}
    else:
        return {"status": "error", "message": f"Failed to delete user ID {user_id_to_delete}."}


def admin_delete_org_logic(admin_id, org_id_to_delete):
    """
    Allows an admin (verified in app.py) to delete an organization.

     Args:
        admin_id (int): The ID of the admin performing the action (for logging).
        org_id_to_delete (int): The ID of the organization to delete.
    """
    # Admin check MUST happen in app.py route before calling this
    print(f"Logic: Admin ID {admin_id} deleting organization ID {org_id_to_delete}")
    success = db_operator.delete_org_by_id(org_id_to_delete)
    if success:
        return {"status": "success", "message": f"Organization ID {org_id_to_delete} deleted successfully."}
    else:
        return {"status": "error", "message": f"Failed to delete organization ID {org_id_to_delete}."}


def admin_create_achievement_logic(admin_id, name, description, points_required, badge_icon, achievement_user_type):
    """
    Allows an admin (verified in app.py) to create a new achievement.

     Args:
        admin_id (int): The ID of the admin performing the action (for logging).
        name (str): Achievement name.
        description (str): Achievement description.
        points_required (int): Points needed to unlock.
        badge_icon (str): Icon identifier/URL.
        achievement_user_type (str): 'user' or 'org'.
    """
    # Admin check MUST happen in app.py route before calling this
    print(f"Logic: Admin ID {admin_id} creating {achievement_user_type} achievement '{name}'")
    result_id = db_operator.create_achievement(name, description, points_required, badge_icon, achievement_user_type)
    if result_id:
        return {"status": "success", "message": f"Achievement '{name}' created successfully."}
    else:
        return {"status": "error", "message": "Failed to create achievement. Name might already exist."}


def admin_delete_achievement_logic(admin_id, achievement_id, achievement_user_type):
    """
    Allows an admin (verified in app.py) to delete an achievement.

    Args:
        admin_id (int): The ID of the admin performing the action (for logging).
        achievement_id (int): ID of the achievement to delete.
        achievement_user_type (str): 'user' or 'org'.
    """
    # Admin check MUST happen in app.py route before calling this
    print(f"Logic: Admin ID {admin_id} deleting {achievement_user_type} achievement ID {achievement_id}")
    success = db_operator.delete_achievement(achievement_id, achievement_user_type)
    if success:
        return {"status": "success", "message": "Achievement deleted successfully."}
    else:
        return {"status": "error", "message": "Failed to delete achievement."}


def admin_create_challenge_logic(admin_id, name, description, goal_type, goal_target, points_reward, time_allowed, challenge_user_type):
    """
    Allows an admin (verified in app.py) to create a new challenge.

    Args:
        admin_id (int): ID of the admin (for logging).
        name (str): Challenge name.
        description (str): Challenge description.
        goal_type (str): Type of goal.
        goal_target (int): Target value for the goal.
        points_reward (int): Points reward.
        time_allowed (int, optional): Time limit in seconds.
        challenge_user_type (str): 'user' or 'org'.
    """
    # Admin check MUST happen in app.py route before calling this
    print(f"Logic: Admin ID {admin_id} creating {challenge_user_type} challenge '{name}'")
    result_id = db_operator.create_challenge(name, description, goal_type, goal_target, points_reward, time_allowed, challenge_user_type)
    if result_id:
        return {"status": "success", "message": f"Challenge '{name}' created successfully."}
    else:
        return {"status": "error", "message": "Failed to create challenge. Name might already exist."}


def admin_delete_challenge_logic(admin_id, challenge_id, challenge_user_type):
    """
    Allows an admin (verified in app.py) to delete a challenge.

    Args:
        admin_id (int): ID of the admin (for logging).
        challenge_id (int): ID of the challenge to delete.
        challenge_user_type (str): 'user' or 'org'.
    """
    # Admin check MUST happen in app.py route before calling this
    print(f"Logic: Admin ID {admin_id} deleting {challenge_user_type} challenge ID {challenge_id}")
    success = db_operator.delete_challenge(challenge_id, challenge_user_type)
    if success:
        return {"status": "success", "message": "Challenge deleted successfully."}
    else:
        return {"status": "error", "message": "Failed to delete challenge."}

# Note: Some functions might require further refinement based on specific needs
# or changes in db_operator function signatures (e.g., delete_my_account_logic).
print("Logic Module Loaded and Ready (Refactored for Flask Sessions).")