import sqlite3
import os
from datetime import datetime

def create_connection():
    try:
        conn = sqlite3.connect('comunidad_verde.db')
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def setup_database():
    """
    Creates all necessary tables in the database if they don't exist.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_code TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                career TEXT,
                interests TEXT,
                points INTEGER DEFAULT 0,
                creation_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Organizations table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS organizations (
                org_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                interests TEXT,
                creation_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Events table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                event_type TEXT NOT NULL,
                location TEXT NOT NULL,
                event_date TEXT NOT NULL,
                event_time TEXT NOT NULL,
                organizer_id INTEGER,
                organizer_type TEXT NOT NULL,
                creation_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (organizer_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            ''')
            
            # Event Participants table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                user_id INTEGER,
                registered_date TEXT DEFAULT CURRENT_TIMESTAMP,
                attended BOOLEAN DEFAULT 0,
                FOREIGN KEY (event_id) REFERENCES events(event_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            ''')
            
            # Exchange Items table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                item_type TEXT NOT NULL,
                status TEXT DEFAULT 'available',
                creation_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            ''')
            
            # Groups table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                topic TEXT NOT NULL,
                creator_id INTEGER,
                creation_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_id) REFERENCES users(user_id)
            )
            ''')
            
            # Group Members table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                user_id INTEGER,
                join_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(group_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            ''')
            
            # Messages table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                recipient_id INTEGER,
                content TEXT NOT NULL,
                sent_date TEXT DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                FOREIGN KEY (sender_id) REFERENCES users(user_id),
                FOREIGN KEY (recipient_id) REFERENCES users(user_id)
            )
            ''')
            
            # Group Messages table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                sender_id INTEGER,
                content TEXT NOT NULL,
                sent_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(group_id),
                FOREIGN KEY (sender_id) REFERENCES users(user_id)
            )
            ''')
            
            # Achievements table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                points_required INTEGER,
                badge_icon TEXT
            )
            ''')
            
            # User Achievements table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement_id INTEGER,
                date_earned TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id)
            )
            ''')
            
            # Challenges table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS challenges (
                challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                goal_count INTEGER,
                goal_type TEXT,
                points_reward INTEGER,
                start_date TEXT,
                end_date TEXT
            )
            ''')
            
            # User Challenges table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                challenge_id INTEGER,
                current_count INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                date_joined TEXT DEFAULT CURRENT_TIMESTAMP,
                date_completed TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id)
            )
            ''')
            
            # Map Points table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS map_points (
                point_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                point_type TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                address TEXT,
                creation_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            print("Database setup complete.")
        except sqlite3.Error as e:
            print(f"Error setting up database: {e}")
        finally:
            conn.close()
    else:
        print("Error: Could not establish database connection.")

# User Management Functions
def register_user(student_code, username, email, password, career=None, interests=None):
    """
    Registers a new user in the system.
    Returns the user_id if successful, None otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO users (student_code, username, email, password, career, interests)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (student_code, username, email, password, career, interests))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error registering user: {e}")
            return None
        finally:
            conn.close()
    return None

def authenticate_user(student_code, password):
    """
    Authenticates a user based on student code and password.
    Returns user data if successful, None otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT user_id, username, email, career, interests, points
            FROM users
            WHERE student_code = ? AND password = ?
            ''', (student_code, password))
            user = cursor.fetchone()
            if user:
                return {
                    'user_id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'career': user[3],
                    'interests': user[4],
                    'points': user[5]
                }
            return None
        except sqlite3.Error as e:
            print(f"Error authenticating user: {e}")
            return None
        finally:
            conn.close()
    return None

def update_user_profile(user_id, username=None, email=None, career=None, interests=None):
    """
    Updates a user's profile information.
    Returns True if successful, False otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if username:
                updates.append("username = ?")
                params.append(username)
            if email:
                updates.append("email = ?")
                params.append(email)
            if career:
                updates.append("career = ?")
                params.append(career)
            if interests:
                updates.append("interests = ?")
                params.append(interests)
                
            if not updates:
                return False
                
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating user profile: {e}")
            return False
        finally:
            conn.close()
    return False

def get_user_by_id(user_id):
    """
    Retrieves user information by user ID.
    Returns user data if found, None otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT user_id, student_code, username, email, career, interests, points
            FROM users
            WHERE user_id = ?
            ''', (user_id,))
            user = cursor.fetchone()
            if user:
                return {
                    'user_id': user[0],
                    'student_code': user[1],
                    'username': user[2],
                    'email': user[3],
                    'career': user[4],
                    'interests': user[5],
                    'points': user[6]
                }
            return None
        except sqlite3.Error as e:
            print(f"Error retrieving user: {e}")
            return None
        finally:
            conn.close()
    return None

# Event Management Functions
def create_event(title, description, event_type, location, event_date, event_time, organizer_id, organizer_type):
    """
    Creates a new event in the system.
    Returns the event_id if successful, None otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO events (title, description, event_type, location, event_date, event_time, organizer_id, organizer_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, event_type, location, event_date, event_time, organizer_id, organizer_type))
            conn.commit()
            
            # Award points to the organizer if they are a user
            if organizer_type == 'user':
                award_points_to_user(organizer_id, 10)  # 10 points for creating an event
                
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating event: {e}")
            return None
        finally:
            conn.close()
    return None

def register_for_event(event_id, user_id):
    """
    Registers a user for an event.
    Returns True if successful, False otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO event_participants (event_id, user_id)
            VALUES (?, ?)
            ''', (event_id, user_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error registering for event: {e}")
            return False
        finally:
            conn.close()
    return False

def mark_event_attendance(event_id, user_id):
    """
    Marks a user as having attended an event and awards points.
    Returns True if successful, False otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE event_participants
            SET attended = 1
            WHERE event_id = ? AND user_id = ?
            ''', (event_id, user_id))
            conn.commit()
            
            # Award points for attending the event
            if cursor.rowcount > 0:
                award_points_to_user(user_id, 5)  # 5 points for attending an event
                
                # Check if this attendance completes any challenges
                update_user_challenges(user_id, 'event_attendance')
                
                return True
            return False
        except sqlite3.Error as e:
            print(f"Error marking attendance: {e}")
            return False
        finally:
            conn.close()
    return False

def get_upcoming_events(limit=10, event_type=None, location=None):
    """
    Retrieves upcoming events with optional filtering.
    Returns a list of events if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            query = '''
            SELECT e.event_id, e.title, e.description, e.event_type, e.location, 
                   e.event_date, e.event_time, e.organizer_id, e.organizer_type,
                   CASE 
                       WHEN e.organizer_type = 'user' THEN u.username
                       WHEN e.organizer_type = 'organization' THEN o.name
                       ELSE 'Unknown'
                   END as organizer_name
            FROM events e
            LEFT JOIN users u ON e.organizer_id = u.user_id AND e.organizer_type = 'user'
            LEFT JOIN organizations o ON e.organizer_id = o.org_id AND e.organizer_type = 'organization'
            WHERE e.event_date >= date('now')
            '''
            
            params = []
            if event_type:
                query += " AND e.event_type = ?"
                params.append(event_type)
            if location:
                query += " AND e.location LIKE ?"
                params.append(f"%{location}%")
                
            query += " ORDER BY e.event_date, e.event_time LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            events = cursor.fetchall()
            
            result = []
            for event in events:
                result.append({
                    'event_id': event[0],
                    'title': event[1],
                    'description': event[2],
                    'event_type': event[3],
                    'location': event[4],
                    'event_date': event[5],
                    'event_time': event[6],
                    'organizer_id': event[7],
                    'organizer_type': event[8],
                    'organizer_name': event[9]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving upcoming events: {e}")
            return []
        finally:
            conn.close()
    return []

def get_event_participants(event_id):
    """
    Retrieves all participants registered for an event.
    Returns a list of participants if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT u.user_id, u.username, u.career, ep.registered_date, ep.attended
            FROM event_participants ep
            JOIN users u ON ep.user_id = u.user_id
            WHERE ep.event_id = ?
            ORDER BY ep.registered_date
            ''', (event_id,))
            participants = cursor.fetchall()
            
            result = []
            for participant in participants:
                result.append({
                    'user_id': participant[0],
                    'username': participant[1],
                    'career': participant[2],
                    'registered_date': participant[3],
                    'attended': bool(participant[4])
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving event participants: {e}")
            return []
        finally:
            conn.close()
    return []

# Group Management Functions
def create_group(name, description, topic, creator_id):
    """
    Creates a new group in the system.
    Returns the group_id if successful, None otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO groups (name, description, topic, creator_id)
            VALUES (?, ?, ?, ?)
            ''', (name, description, topic, creator_id))
            conn.commit()
            
            group_id = cursor.lastrowid
            
            # Add creator as first member
            join_group(group_id, creator_id)
            
            # Award points for creating a group
            award_points_to_user(creator_id, 15)  # 15 points for creating a group
            
            return group_id
        except sqlite3.Error as e:
            print(f"Error creating group: {e}")
            return None
        finally:
            conn.close()
    return None

def join_group(group_id, user_id):
    """
    Adds a user to a group.
    Returns True if successful, False otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO group_members (group_id, user_id)
            VALUES (?, ?)
            ''', (group_id, user_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error joining group: {e}")
            return False
        finally:
            conn.close()
    return False

def send_group_message(group_id, sender_id, content):
    """
    Sends a message to a group.
    Returns the message_id if successful, None otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO group_messages (group_id, sender_id, content)
            VALUES (?, ?, ?)
            ''', (group_id, sender_id, content))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error sending group message: {e}")
            return None
        finally:
            conn.close()
    return None

def get_group_messages(group_id, limit=50):
    """
    Retrieves recent messages from a group.
    Returns a list of messages if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT gm.message_id, gm.sender_id, u.username, gm.content, gm.sent_date
            FROM group_messages gm
            JOIN users u ON gm.sender_id = u.user_id
            WHERE gm.group_id = ?
            ORDER BY gm.sent_date DESC
            LIMIT ?
            ''', (group_id, limit))
            messages = cursor.fetchall()
            
            result = []
            for msg in messages:
                result.append({
                    'message_id': msg[0],
                    'sender_id': msg[1],
                    'sender_name': msg[2],
                    'content': msg[3],
                    'sent_date': msg[4]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving group messages: {e}")
            return []
        finally:
            conn.close()
    return []

def get_groups_by_topic(topic=None, limit=20):
    """
    Retrieves groups, optionally filtered by topic.
    Returns a list of groups if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            query = '''
            SELECT g.group_id, g.name, g.description, g.topic, g.creator_id, u.username as creator_name,
                   (SELECT COUNT(*) FROM group_members WHERE group_id = g.group_id) as member_count
            FROM groups g
            JOIN users u ON g.creator_id = u.user_id
            '''
            
            params = []
            if topic:
                query += " WHERE g.topic = ?"
                params.append(topic)
                
            query += " ORDER BY member_count DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            groups = cursor.fetchall()
            
            result = []
            for group in groups:
                result.append({
                    'group_id': group[0],
                    'name': group[1],
                    'description': group[2],
                    'topic': group[3],
                    'creator_id': group[4],
                    'creator_name': group[5],
                    'member_count': group[6]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving groups: {e}")
            return []
        finally:
            conn.close()
    return []

def get_user_groups(user_id):
    """
    Retrieves all groups that a user is a member of.
    Returns a list of groups if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT g.group_id, g.name, g.description, g.topic, g.creator_id, 
                   (SELECT COUNT(*) FROM group_members WHERE group_id = g.group_id) as member_count,
                   gm.join_date
            FROM groups g
            JOIN group_members gm ON g.group_id = gm.group_id
            WHERE gm.user_id = ?
            ORDER BY gm.join_date DESC
            ''', (user_id,))
            groups = cursor.fetchall()
            
            result = []
            for group in groups:
                result.append({
                    'group_id': group[0],
                    'name': group[1],
                    'description': group[2],
                    'topic': group[3],
                    'creator_id': group[4],
                    'member_count': group[5],
                    'join_date': group[6]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving user groups: {e}")
            return []
        finally:
            conn.close()
    return []

def leave_group(group_id, user_id):
    """
    Removes a user from a group.
    Returns True if successful, False otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            DELETE FROM group_members
            WHERE group_id = ? AND user_id = ?
            ''', (group_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error leaving group: {e}")
            return False
        finally:
            conn.close()
    return False

# Exchange Item Functions
def create_exchange_item(user_id, title, description, item_type):
    """
    Creates a new item for exchange, gifting, or lending.
    Returns the item_id if successful, None otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO exchange_items (user_id, title, description, item_type)
            VALUES (?, ?, ?, ?)
            ''', (user_id, title, description, item_type))
            conn.commit()
            
            # Award points for offering an item
            award_points_to_user(user_id, 3)  # 3 points for listing an item
            
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating exchange item: {e}")
            return None
        finally:
            conn.close()
    return None

def update_item_status(item_id, status):
    """
    Updates the status of an exchange item (available, pending, exchanged).
    Returns True if successful, False otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE exchange_items
            SET status = ?
            WHERE item_id = ?
            ''', (status, item_id))
            conn.commit()
            
            # If item is marked as exchanged, award points to the owner
            if status == 'exchanged':
                cursor.execute('''
                SELECT user_id FROM exchange_items WHERE item_id = ?
                ''', (item_id,))
                user = cursor.fetchone()
                if user:
                    award_points_to_user(user[0], 7)  # 7 additional points for completing an exchange
                    update_user_challenges(user[0], 'item_exchange')
                    
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating item status: {e}")
            return False
        finally:
            conn.close()
    return False

def get_available_items(item_type=None, limit=20):
    """
    Retrieves available exchange items, optionally filtered by type.
    Returns a list of items if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            query = '''
            SELECT ei.item_id, ei.user_id, u.username, ei.title, ei.description, 
                   ei.item_type, ei.creation_date
            FROM exchange_items ei
            JOIN users u ON ei.user_id = u.user_id
            WHERE ei.status = 'available'
            '''
            
            params = []
            if item_type:
                query += " AND ei.item_type = ?"
                params.append(item_type)
                
            query += " ORDER BY ei.creation_date DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            items = cursor.fetchall()
            
            result = []
            for item in items:
                result.append({
                    'item_id': item[0],
                    'user_id': item[1],
                    'username': item[2],
                    'title': item[3],
                    'description': item[4],
                    'item_type': item[5],
                    'creation_date': item[6]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving available items: {e}")
            return []
        finally:
            conn.close()
    return []

def get_user_items(user_id):
    """
    Retrieves all exchange items created by a specific user.
    Returns a list of items if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT item_id, title, description, item_type, status, creation_date
            FROM exchange_items
            WHERE user_id = ?
            ORDER BY creation_date DESC
            ''', (user_id,))
            items = cursor.fetchall()
            
            result = []
            for item in items:
                result.append({
                    'item_id': item[0],
                    'title': item[1],
                    'description': item[2],
                    'item_type': item[3],
                    'status': item[4],
                    'creation_date': item[5]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving user items: {e}")
            return []
        finally:
            conn.close()
    return []

# Points and Achievement Functions
def award_points_to_user(user_id, points):
    """
    Awards points to a user and checks for achievement unlocks.
    Returns True if successful, False otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE users
            SET points = points + ?
            WHERE user_id = ?
            ''', (points, user_id))
            conn.commit()
            
            # Check for achievements based on total points
            cursor.execute('''
            SELECT points FROM users WHERE user_id = ?
            ''', (user_id,))
            total_points = cursor.fetchone()[0]
            
            # Check for point-based achievements
            cursor.execute('''
            SELECT achievement_id, name, points_required
            FROM achievements
            WHERE points_required <= ?
            ''', (total_points,))
            possible_achievements = cursor.fetchall()
            
            for achievement in possible_achievements:
                # Check if user already has this achievement
                cursor.execute('''
                SELECT COUNT(*) FROM user_achievements
                WHERE user_id = ? AND achievement_id = ?
                ''', (user_id, achievement[0]))
                
                if cursor.fetchone()[0] == 0:
                    # Award the achievement
                    cursor.execute('''
                    INSERT INTO user_achievements (user_id, achievement_id)
                    VALUES (?, ?)
                    ''', (user_id, achievement[0]))
                    conn.commit()
                    print(f"User {user_id} unlocked achievement: {achievement[1]}")
            
            return True
        except sqlite3.Error as e:
            print(f"Error awarding points: {e}")
            return False
        finally:
            conn.close()
    return False

# Challenge Management Functions
def create_challenge(title, description, goal_count, goal_type, points_reward, start_date, end_date):
    """
    Creates a new environmental challenge in the system.
    Returns the challenge_id if successful, None otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO challenges (title, description, goal_count, goal_type, points_reward, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, goal_count, goal_type, points_reward, start_date, end_date))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating challenge: {e}")
            return None
        finally:
            conn.close()
    return None

def join_challenge(user_id, challenge_id):
    """
    Registers a user for a challenge.
    Returns True if successful, False otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO user_challenges (user_id, challenge_id)
            VALUES (?, ?)
            ''', (user_id, challenge_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error joining challenge: {e}")
            return False
        finally:
            conn.close()
    return False

def update_user_challenges(user_id, activity_type):
    """
    Updates user's progress on challenges based on their activity.
    Returns the number of challenges updated.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Find relevant active challenges for this user and activity type
            cursor.execute('''
            SELECT uc.id, uc.challenge_id, uc.current_count, c.goal_count, c.points_reward
            FROM user_challenges uc
            JOIN challenges c ON uc.challenge_id = c.challenge_id
            WHERE uc.user_id = ? AND c.goal_type = ? AND uc.completed = 0
            AND c.start_date <= date('now') AND c.end_date >= date('now')
            ''', (user_id, activity_type))
            
            active_challenges = cursor.fetchall()
            updates = 0
            
            for challenge in active_challenges:
                uc_id, challenge_id, current_count, goal_count, points_reward = challenge
                
                # Increment progress
                new_count = current_count + 1
                cursor.execute('''
                UPDATE user_challenges
                SET current_count = ?
                WHERE id = ?
                ''', (new_count, uc_id))
                updates += 1
                
                # Check if challenge is now complete
                if new_count >= goal_count:
                    cursor.execute('''
                    UPDATE user_challenges
                    SET completed = 1, date_completed = datetime('now')
                    WHERE id = ?
                    ''', (uc_id,))
                    
                    # Award points for completing the challenge
                    award_points_to_user(user_id, points_reward)
                    
            conn.commit()
            return updates
        except sqlite3.Error as e:
            print(f"Error updating challenges: {e}")
            return 0
        finally:
            conn.close()
    return 0

def get_active_challenges():
    """
    Retrieves all currently active challenges.
    Returns a list of challenges if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT challenge_id, title, description, goal_count, goal_type, 
                   points_reward, start_date, end_date
            FROM challenges
            WHERE start_date <= date('now') AND end_date >= date('now')
            ORDER BY end_date
            ''')
            challenges = cursor.fetchall()
            
            result = []
            for challenge in challenges:
                result.append({
                    'challenge_id': challenge[0],
                    'title': challenge[1],
                    'description': challenge[2],
                    'goal_count': challenge[3],
                    'goal_type': challenge[4],
                    'points_reward': challenge[5],
                    'start_date': challenge[6],
                    'end_date': challenge[7]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving active challenges: {e}")
            return []
        finally:
            conn.close()
    return []

def get_user_challenges(user_id):
    """
    Retrieves all challenges a user is participating in.
    Returns a list of challenges with progress if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT c.challenge_id, c.title, c.description, c.goal_count, c.goal_type,
                   c.points_reward, c.start_date, c.end_date, 
                   uc.current_count, uc.completed, uc.date_joined, uc.date_completed
            FROM challenges c
            JOIN user_challenges uc ON c.challenge_id = uc.challenge_id
            WHERE uc.user_id = ?
            ORDER BY c.end_date
            ''', (user_id,))
            challenges = cursor.fetchall()
            
            result = []
            for challenge in challenges:
                result.append({
                    'challenge_id': challenge[0],
                    'title': challenge[1],
                    'description': challenge[2],
                    'goal_count': challenge[3],
                    'goal_type': challenge[4],
                    'points_reward': challenge[5],
                    'start_date': challenge[6],
                    'end_date': challenge[7],
                    'current_count': challenge[8],
                    'completed': bool(challenge[9]),
                    'date_joined': challenge[10],
                    'date_completed': challenge[11]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving user challenges: {e}")
            return []
        finally:
            conn.close()
    return []

# Map Points Functions
def add_map_point(name, description, point_type, latitude, longitude, address=None):
    """
    Adds a new point on the interactive map (recycling point, meeting spot, allied store).
    Returns the point_id if successful, None otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO map_points (name, description, point_type, latitude, longitude, address)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, description, point_type, latitude, longitude, address))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error adding map point: {e}")
            return None
        finally:
            conn.close()
    return None

def get_map_points(point_type=None):
    """
    Retrieves map points, optionally filtered by type.
    Returns a list of points if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            query = '''
            SELECT point_id, name, description, point_type, latitude, longitude, address, creation_date
            FROM map_points
            '''
            
            params = []
            if point_type:
                query += " WHERE point_type = ?"
                params.append(point_type)
                
            query += " ORDER BY name"
            
            cursor.execute(query, params)
            points = cursor.fetchall()
            
            result = []
            for point in points:
                result.append({
                    'point_id': point[0],
                    'name': point[1],
                    'description': point[2],
                    'point_type': point[3],
                    'latitude': point[4],
                    'longitude': point[5],
                    'address': point[6],
                    'creation_date': point[7]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving map points: {e}")
            return []
        finally:
            conn.close()
    return []

# Organization Management Functions
def create_organization(name, description, interests=None):
    """
    Creates a new organization in the system.
    Returns the org_id if successful, None otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO organizations (name, description, interests)
            VALUES (?, ?, ?)
            ''', (name, description, interests))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating organization: {e}")
            return None
        finally:
            conn.close()
    return None

def get_organizations():
    """
    Retrieves all organizations in the system.
    Returns a list of organizations if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT org_id, name, description, interests, creation_date
            FROM organizations
            ORDER BY name
            ''')
            orgs = cursor.fetchall()
            
            result = []
            for org in orgs:
                result.append({
                    'org_id': org[0],
                    'name': org[1],
                    'description': org[2],
                    'interests': org[3],
                    'creation_date': org[4]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving organizations: {e}")
            return []
        finally:
            conn.close()
    return []

# Achievement Management Functions
def create_achievement(name, description, points_required, badge_icon=None):
    """
    Creates a new achievement in the system.
    Returns the achievement_id if successful, None otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO achievements (name, description, points_required, badge_icon)
            VALUES (?, ?, ?, ?)
            ''', (name, description, points_required, badge_icon))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating achievement: {e}")
            return None
        finally:
            conn.close()
    return None

def get_user_achievements(user_id):
    """
    Retrieves all achievements earned by a user.
    Returns a list of achievements if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT a.achievement_id, a.name, a.description, a.points_required, 
                   a.badge_icon, ua.date_earned
            FROM achievements a
            JOIN user_achievements ua ON a.achievement_id = ua.achievement_id
            WHERE ua.user_id = ?
            ORDER BY ua.date_earned
            ''', (user_id,))
            achievements = cursor.fetchall()
            
            result = []
            for achievement in achievements:
                result.append({
                    'achievement_id': achievement[0],
                    'name': achievement[1],
                    'description': achievement[2],
                    'points_required': achievement[3],
                    'badge_icon': achievement[4],
                    'date_earned': achievement[5]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving user achievements: {e}")
            return []
        finally:
            conn.close()
    return []

def get_all_achievements():
    """
    Retrieves all achievements in the system.
    Returns a list of achievements if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT achievement_id, name, description, points_required, badge_icon
            FROM achievements
            ORDER BY points_required
            ''')
            achievements = cursor.fetchall()
            
            result = []
            for achievement in achievements:
                result.append({
                    'achievement_id': achievement[0],
                    'name': achievement[1],
                    'description': achievement[2],
                    'points_required': achievement[3],
                    'badge_icon': achievement[4]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving achievements: {e}")
            return []
        finally:
            conn.close()
    return []

# Messaging Functions
def send_direct_message(sender_id, recipient_id, content):
    """
    Sends a direct message from one user to another.
    Returns the message_id if successful, None otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO messages (sender_id, recipient_id, content)
            VALUES (?, ?, ?)
            ''', (sender_id, recipient_id, content))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error sending message: {e}")
            return None
        finally:
            conn.close()
    return None

def get_user_messages(user_id, limit=50):
    """
    Retrieves recent messages sent to a user.
    Returns a list of messages if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT m.message_id, m.sender_id, u.username as sender_name, 
                   m.content, m.sent_date, m.is_read
            FROM messages m
            JOIN users u ON m.sender_id = u.user_id
            WHERE m.recipient_id = ?
            ORDER BY m.sent_date DESC
            LIMIT ?
            ''', (user_id, limit))
            messages = cursor.fetchall()
            
            result = []
            for msg in messages:
                result.append({
                    'message_id': msg[0],
                    'sender_id': msg[1],
                    'sender_name': msg[2],
                    'content': msg[3],
                    'sent_date': msg[4],
                    'is_read': bool(msg[5])
                })
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving messages: {e}")
            return []
        finally:
            conn.close()
    return []

def mark_message_as_read(message_id):
    """
    Marks a message as read.
    Returns True if successful, False otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE messages
            SET is_read = 1
            WHERE message_id = ?
            ''', (message_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error marking message as read: {e}")
            return False
        finally:
            conn.close()
    return False

def get_conversation(user1_id, user2_id, limit=50):
    """
    Retrieves the conversation history between two users.
    Returns a list of messages in chronological order if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT m.message_id, m.sender_id, m.recipient_id, m.content, m.sent_date, m.is_read
            FROM messages m
            WHERE (m.sender_id = ? AND m.recipient_id = ?) OR (m.sender_id = ? AND m.recipient_id = ?)
            ORDER BY m.sent_date DESC
            LIMIT ?
            ''', (user1_id, user2_id, user2_id, user1_id, limit))
            messages = cursor.fetchall()
            
            result = []
            for msg in messages:
                result.append({
                    'message_id': msg[0],
                    'sender_id': msg[1],
                    'recipient_id': msg[2],
                    'content': msg[3],
                    'sent_date': msg[4],
                    'is_read': bool(msg[5])
                })
            return result[::-1]  # Reverse to get chronological order
        except sqlite3.Error as e:
            print(f"Error retrieving conversation: {e}")
            return []
        finally:
            conn.close()
    return []

# Search Functions
def search_users(query, limit=20):
    """
    Searches for users based on username, career, or interests.
    Returns a list of users if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT user_id, username, career, interests, points
            FROM users
            WHERE username LIKE ? OR career LIKE ? OR interests LIKE ?
            ORDER BY points DESC
            LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            users = cursor.fetchall()
            
            result = []
            for user in users:
                result.append({
                    'user_id': user[0],
                    'username': user[1],
                    'career': user[2],
                    'interests': user[3],
                    'points': user[4]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error searching users: {e}")
            return []
        finally:
            conn.close()
    return []

def search_events(query, limit=20):
    """
    Searches for events based on title, description, event type or location.
    Returns a list of events if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT event_id, title, description, event_type, location, event_date, event_time
            FROM events
            WHERE title LIKE ? OR description LIKE ? OR event_type LIKE ? OR location LIKE ?
            AND event_date >= date('now')
            ORDER BY event_date, event_time
            LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', limit))
            events = cursor.fetchall()
            
            result = []
            for event in events:
                result.append({
                    'event_id': event[0],
                    'title': event[1],
                    'description': event[2],
                    'event_type': event[3],
                    'location': event[4],
                    'event_date': event[5],
                    'event_time': event[6]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error searching events: {e}")
            return []
        finally:
            conn.close()
    return []

def search_groups(query, limit=20):
    """
    Searches for groups based on name, description or topic.
    Returns a list of groups if found, empty list otherwise.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT g.group_id, g.name, g.description, g.topic, g.creator_id,
                   (SELECT COUNT(*) FROM group_members WHERE group_id = g.group_id) as member_count
            FROM groups g
            WHERE g.name LIKE ? OR g.description LIKE ? OR g.topic LIKE ?
            ORDER BY member_count DESC
            LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            groups = cursor.fetchall()
            
            result = []
            for group in groups:
                result.append({
                    'group_id': group[0],
                    'name': group[1],
                    'description': group[2],
                    'topic': group[3],
                    'creator_id': group[4],
                    'member_count': group[5]
                })
            return result
        except sqlite3.Error as e:
            print(f"Error searching groups: {e}")
            return []
        finally:
            conn.close()
    return []

# Initialization data for testing
def create_sample_data():
    """
    Populates the database with sample data for testing.
    Returns True if successful, False otherwise.
    """
    try:
        # Create sample achievements
        create_achievement("Eco Novice", "Started your environmental journey", 0)
        create_achievement("Eco Enthusiast", "Earned 50 points through environmental actions", 50)
        create_achievement("Eco Champion", "Earned 100 points through environmental actions", 100)
        create_achievement("Eco Warrior", "Earned 250 points through environmental actions", 250)
        create_achievement("Eco Hero", "Earned 500 points through environmental actions", 500)
        
        # Create sample challenges
        now = datetime.now()
        end_date = now.replace(month=now.month + 1 if now.month < 12 else 1).strftime("%Y-%m-%d")
        start_date = now.strftime("%Y-%m-%d")
        
        create_challenge(
            "Event Enthusiast", 
            "Attend 3 environmental events this month", 
            3, 
            "event_attendance", 
            25, 
            start_date, 
            end_date
        )
        
        create_challenge(
            "Green Exchanger", 
            "Exchange or gift 5 items this month", 
            5, 
            "item_exchange", 
            30, 
            start_date, 
            end_date
        )
        
        create_challenge(
            "Community Builder", 
            "Join or create 2 environmental groups", 
            2, 
            "group_activity", 
            20, 
            start_date, 
            end_date
        )
        
        # Create sample map points
        add_map_point(
            "Punto Ecológico Central", 
            "Punto principal de reciclaje con contenedores para diferentes materiales", 
            "recycling", 
            4.602547, 
            -74.065559, 
            "Edificio Central, Universidad de los Andes"
        )
        
        add_map_point(
            "EcoCafé Uniandes", 
            "Café sostenible con descuentos para miembros de Comunidad Verde", 
            "allied_store", 
            4.603123, 
            -74.066432, 
            "Plazoleta de Comidas, Universidad de los Andes"
        )
        
        add_map_point(
            "Jardín Botánico Uniandino", 
            "Punto de encuentro para actividades de siembra y educación ambiental", 
            "meeting_point", 
            4.601875, 
            -74.064218, 
            "Sector Norte, Universidad de los Andes"
        )
        
        # Create sample organizations
        create_organization(
            "EcoUniandes", 
            "Organización estudiantil dedicada a promover prácticas sostenibles en el campus", 
            "reciclaje, educación ambiental, energías renovables"
        )
        
        create_organization(
            "Hidroconsciencia", 
            "Grupo enfocado en la conservación del agua y recursos hídricos", 
            "agua, conservación, educación"
        )
        
        print("Sample data created successfully")
        return True
    except Exception as e:
        print(f"Error creating sample data: {e}")
        return False

# Setup database if it doesn't exist
if not os.path.exists('comunidad_verde.db'):
    setup_database()
    create_sample_data()