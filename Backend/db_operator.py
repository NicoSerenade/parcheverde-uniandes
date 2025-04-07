'''Data base modifications'''
import bcrypt # bcrypt is a hashing algorithm
import sqlite3
import db_conn

#USER REGISTRATION
def register_user(student_code, password, name, email, career=None, interests=None):
    """
    Registers a new user in the system.
    Returns the user_id if successful, None otherwise.
    """
    if student_code == "admin":
        user_type = "admin"
    else:
        user_type = "user"
    user_id = None
    conn = db_conn.create_connection()
    if conn is not None:
        try:
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

#ORG REGISTRATION
def register_org(creator_student_code, password, name, email, description=None, interests=None):
    user_type = "org"
    user_id = None
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

