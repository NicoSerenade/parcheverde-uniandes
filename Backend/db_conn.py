'''Initializing db, creating tables and connection'''

import sqlite3

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('comunidad_verde.db')
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn

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
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
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
                creator_student_code INTEGER,
                password TEXT NOT NULL,
                name TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                description TEXT,
                interests TEXT,
                points INTEGER DEFAULT 0,
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
            CREATE TABLE IF NOT EXISTS items (
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