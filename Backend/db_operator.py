'''Data base modifications'''
import bcrypt # bcrypt is a hashing algorithm
import sqlite3

#CUSTOM MODULES
import db_conn

# datetime format ISO 8601 YYYY-MM-DD HH:MM:SS

#USER REGISTRATION
def check_user_exists(conn, email, student_code):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE email = ? OR student_code = ?", (email, student_code))
    existing_user = cursor.fetchone()
    return existing_user is not None

def register_user(student_code, password, name, email, career=None, interests=None):
    user_id = None
    user_type = "user"

    if student_code == "admin":
        user_type = "admin"

    # 1. Validate Email Domain for non admin users
    elif not isinstance(email, str) or not email.endswith("@uniandes.edu.co"):
        print(f"Error: Email must end with {"@uniandes.edu.co"}")
        return None
    
    try:
        conn = db_conn.create_connection()
        
        if check_user_exists(conn, email, student_code):
             print(f"Error: User with email '{email}' or student code '{student_code}' already exists.")
             return None

        password_bytes = password.encode('utf-8') #ebcode the password so that bcrypt module can handle it.
        salt = bcrypt.gensalt()  # Generates random salt; value that get combined with the password before hashing
        hashed_password = bcrypt.hashpw(password_bytes, salt) #hash the password

        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO users (user_type, student_code, password, name, email, career, interests)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_type, student_code, hashed_password, name, email, career, interests)) 
        conn.commit()
        user_id = cursor.lastrowid #returns the id of the last manipulated row

    except sqlite3.Error as e:
        print(f"Error registering user: {e}")
    finally:
        conn.close()
        
    return user_id

def authenticate_user(student_code, password):
    """
    Authenticates a user based on student code and password.
    Returns a dict with user data if successful, None otherwise.
    """
    user_data = None
    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor() #The order of fields in the SELECT statement determines the order in the tuple
            cursor.execute('''
            SELECT user_id, user_type, student_code, name, email, password, career, interests, points, creation_date
            FROM users
            WHERE student_code = ?
            ''', (student_code,)) #the comma is crusial so it is consider a tuple
            
            user = cursor.fetchone()
            if user:
                password_bytes = password.encode('utf-8')
                stored_password = user[5]
                if bcrypt.checkpw(password_bytes, stored_password): #Extracts the salt from the hashed password, embed it into the login password, and compare them.
                    user_data = {
                        'user_id': user[0],
                        'user_type': user[1],
                        'student_code': user[2],
                        'name': user[3],
                        'email': user[4],
                        'career': user[6],
                        'interests': user[7],
                        'points': user[8],
                        'creation_date': user[9]
                    }
        except sqlite3.Error as e:
            print(f"Error authenticating user: {e}")
        finally:
            conn.close()
    return user_data

def update_user_profile(user_id, student_code=None, password=None, name=None, email=None, career=None, interests=None):
    """
    Updates a user's profile information.
    Returns True if successful, False otherwise.
    """
    success = False

    if not isinstance(email, str) or not email.endswith("@uniandes.edu.co"):
        print(f"Error: Email must end with {"@uniandes.edu.co"}")
        return None

    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if student_code:
                updates.append("student_code = ?")
                params.append(student_code)

            if password:
                password_bytes = password.encode('utf-8')
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(password_bytes, salt)
                updates.append("password = ?")
                params.append(hashed_password)
            
            if name:
                updates.append("name = ?")
                params.append(name)
                
            if email:
                updates.append("email = ?")
                params.append(email)

            if career:
                updates.append("career = ?")
                params.append(career)

            if interests:
                updates.append("interests = ?")
                params.append(interests)
                
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
            cursor.execute(query, params) #both tuples and list work in sql queries.
            conn.commit()
            success = cursor.rowcount > 0 # rowcount returns how many rows were affected by the most recent SQL operation.
        except sqlite3.Error as e:
            print(f"Error updating user profile: {e}")
        finally:
            conn.close()
    return success

def delete_my_user(student_code, password):
    """Deletes a user after verifying their student_code and password securely

    Returns:
        True if the user was successfully found, password verified, and deleted.
        False otherwiswe"""
    
    success = False
    try:
        conn = db_conn.create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE student_code = ?", (student_code,))
        stored_password = cursor.fetchone()

        if stored_password:
            stored_password = stored_password[0]
            password_bytes = password.encode('utf-8')

            if bcrypt.checkpw(password_bytes, stored_password):
                cursor.execute("DELETE FROM users WHERE student_code = ?", (student_code,))
                conn.commit()

                if cursor.rowcount > 0:
                    print(f"User successfully deleted.")
                    success = True

    except sqlite3.Error as e:
        print(f"Database error during user deletion: {e}")

    finally:
        conn.close() 
    return success

#ORG REGISTRATION
def register_org(creator_student_code, password, name, email, description=None, interests=None):
    user_type = "org"
    user_id = None

    if not isinstance(email, str) or not email.endswith("@uniandes.edu.co"):
        print(f"Error: Email must end with {"@uniandes.edu.co"}")
        return None

    conn = db_conn.create_connection()
    if conn is not None:
        try:
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt) 

            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO organizations (user_type, creator_student_code, password, name, email, description, interests)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_type, creator_student_code, hashed_password, name, email, description, interests)) 
            conn.commit()
            user_id = cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error registering organization: {e}")
        finally:
            conn.close()
    return user_id

def authenticate_org(name, password):
    """
    Authenticates an organization based on name and password.
    Returns a dict with organization data if successful, None otherwise.
    """
    user_data = None
    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT user_id, user_type, creator_student_code, name, email, password, description, interests, points, creation_date
            FROM organizations
            WHERE name = ?
            ''', (name,))
            
            org = cursor.fetchone()
            if org:
                password_bytes = password.encode('utf-8')
                stored_password = org[5]
                if bcrypt.checkpw(password_bytes, stored_password):
                    user_data = {
                        'user_id': org[0],
                        'user_type': org[1],
                        'creator_student_code': org[2],
                        'name': org[3],
                        'email': org[4],
                        'description': org[6],
                        'interests': org[7],
                        'points': org[8],
                        'creation_date': org[9]
                    }
        except sqlite3.Error as e:
            print(f"Error authenticating organization: {e}")
        finally:
            conn.close()
    return user_data

def update_org_profile(user_id, creator_student_code=None, password=None, name=None, email=None, description=None, interests=None):
    success = False

    if not isinstance(email, str) or not email.endswith("@uniandes.edu.co"):
        print(f"Error: Email must end with {"@uniandes.edu.co"}")
        return None

    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if creator_student_code:
                updates.append("creator_student_code = ?")
                params.append(creator_student_code)
            if password:
                password_bytes = password.encode('utf-8')
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(password_bytes, salt)
                updates.append("password = ?")
                params.append(hashed_password)
            if name:
                updates.append("name = ?")
                params.append(name)
            if email:
                updates.append("email = ?")
                params.append(email)
            if description:
                updates.append("description = ?")
                params.append(description)
            if interests:
                updates.append("interests = ?")
                params.append(interests)
            
            params.append(user_id)
            
            query = f"UPDATE organizations SET {', '.join(updates)} WHERE user_id = ?"
            cursor.execute(query, params)
            conn.commit()
            
            success = cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating organization profile: {e}")
        finally:
            conn.close()
    return success

def delete_my_org(creator_student_code, password):
    """Deletes a or after verifying their creator_student_code and password securely

    Returns:
        True if the user was successfully found, password verified, and deleted.
        False otherwiswe"""
    
    success = False
    try:
        conn = db_conn.create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM organizations WHERE creator_student_code = ?", (creator_student_code,))
        stored_password = cursor.fetchone()

        if stored_password:
            stored_password = stored_password[0]
            password_bytes = password.encode('utf-8')

            if bcrypt.checkpw(password_bytes, stored_password):
                cursor.execute("DELETE FROM organizations WHERE creator_student_code = ?", (creator_student_code,))
                conn.commit()

                if cursor.rowcount > 0:
                    print(f"Organization successfully deleted.")
                    success = True

    except sqlite3.Error as e:
        print(f"Database error during org deletion: {e}")

    finally:
        conn.close() 
    return success

#ADMIN FUNCTIONS
def get_user_by_id(user_id):
    """
    Retrieves user information by user ID.
    Returns user data if found, None otherwise.
    """
    user_data = None
    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT user_id, user_type, student_code, name, email, password, career, interests, points
            FROM users
            WHERE user_id = ?
            ''', (user_id,))
            user = cursor.fetchone()
            if user:
                user_data = {
                    'user_id': user[0],
                    'user_type': user[1],
                    'student_code': user[2],
                    'name': user[3],
                    'email': user[4],
                    "password": user[5], #TRY, QUIT
                    'career': user[6],
                    'interests': user[7],
                    'points': user[8]
                }
        except sqlite3.Error as e:
            print(f"Error retrieving user: {e}")
        finally:
            conn.close()
    return user_data

def delete_user_by_id(user_id):
    success = False
    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor() #DELETE remove all columns for any rows that match that condition.
            cursor.execute('''
            DELETE FROM users
            WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
            if cursor.rowcount > 0:
                success = True

        except sqlite3.Error as e:
            print(f"Error deleting user profile: {e}")
        finally:
            conn.close()
    return success

def get_org_by_id(user_id):
    user_data = None
    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT user_id, user_type, creator_student_code, name, email, description, interests, points, creation_date
            FROM organizations
            WHERE user_id = ?
            ''', (user_id,))
            
            org = cursor.fetchone()
            if org:
                user_data = {
                    'user_id': org[0],
                    'user_type': org[1],
                    'creator_student_code': org[2],
                    'name': org[3],
                    'email': org[4],
                    'description': org[5],
                    'interests': org[6],
                    'points': org[7],
                    'creation_date': org[8]
                }
        except sqlite3.Error as e:
            print(f"Error retrieving organization: {e}")
        finally:
            conn.close()
    return user_data

def delete_org_by_id(user_id):
    success = False
    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            DELETE FROM organizations
            WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            if cursor.rowcount > 0:
                success = True
        except sqlite3.Error as e:
            print(f"Error deleting organization: {e}")
        finally:
            conn.close()
    return success


#USER/ORG FUNCTIONS
def create_event(organizer_id, organizer_type, title, description, event_type, location, event_datetime):
    """
    Creates a new event in the system.
    Returns the event_id if successful, None otherwise.
    """
    event_id = None
    conn = db_conn.create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO events (organizer_id, organizer_type, title, description, event_type, location, event_datetime)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (organizer_id, organizer_type, title, description, event_type, location, event_datetime))
        conn.commit()
        event_id = cursor.lastrowid

    except sqlite3.Error as e:
        print(f"Error creating event: {e}")
    finally:
        conn.close()
    return event_id

def register_for_event(event_id, user_id, user_type):
    """
    Registers a user for an event.
    Returns True if successful, False otherwise.
    """

#GENERAL LOGIC
def update_points(user_id, user_type, points_to_add):
    """
    Awards points to a user or organization and checks for achievement unlocks.
    Returns:
        The name of the highest newly unlocked achievement (str), otherwise None.
    """
    old_points = None
    new_total_points = None
    achievement_unlocked = None

    # Determine table and id column based on user_type
    if user_type == "user":
        table_name = "users"
    elif user_type == "org":
        table_name = "organizations"

    try:
        conn = db_conn.create_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT points FROM {table_name} WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        old_points = result[0]
   
        new_total_points = old_points + points_to_add

        cursor.execute(f'''
            UPDATE {table_name}
            SET points = points + ?
            WHERE user_id = ?
        ''', (points_to_add, user_id))

        conn.commit()

        achievement_unlocked = get_achievements(old_points, new_total_points)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return achievement_unlocked

def get_achievements(old_points, new_points):
    achievements_config = {
        10000: "Ultimate Champion",
        5000: "Platinum Contributor",
        1000: "Gold Star",
        500: "Silver Badge",
        100: "Bronze Starter",
    }

    newly_achieved_name = None

    for threshold, name in achievements_config.items():
        if old_points < threshold <= new_points:
            newly_achieved_name = name
            break
    return newly_achieved_name









