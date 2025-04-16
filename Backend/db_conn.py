'''Initializing db, creating tables and connection'''
''' ABSTRACT COLUMNS FORMAT-separated by ", "
BOOLEANS: False = 0, True = 1
interests: --siembra, reciclaje, caridad, enseñanza, software
goal_type: --siembra, reciclaje, caridad, enseñanza, software
event_status: active, completed
exchange_status: pending, accepted, rejected
item_type: --ropa, libros, hogar, otros
item_terms: --gift, loan, exchange (NO SE PUEDEN VENDER)
item_status: --available, borrowed, unavailable
challenge_status: active, completed
datetime format ISO 8601 YYYY-MM-DD HH:MM:SS
'''

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
                user_type TEXT NOT NULL, --user
                student_code TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                career TEXT,
                interests TEXT, --siembra, reciclaje, caridad, enseñanza, software
                points INTEGER DEFAULT 0,
                creation_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Organizations table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS organizations (
                org_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_type TEXT NOT NULL, --org
                creator_student_code INTEGER,
                password TEXT NOT NULL,
                name TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                description TEXT,
                interests TEXT, --siembra, reciclaje, caridad, enseñanza, software
                points INTEGER DEFAULT 0,
                creation_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Org Members table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS organization_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER, 
                user_id INTEGER,
                registered_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE (org_id, user_id)

            )
            ''')

            # Events table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                organizer_id INTEGER,
                organizer_type TEXT NOT NULL, 
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                event_type TEXT NOT NULL,
                location TEXT NOT NULL,
                event_datetime TEXT NOT NULL,
                event_status TEXT DEFAULT 'active', --active, completed
                points_value INTEGER DEFAULT 0, --poits it gives to creators and participants
                creation_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_event_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                user_id INTEGER,
                registered_date TEXT DEFAULT CURRENT_TIMESTAMP,
                attended BOOLEAN DEFAULT 0,
                FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE (event_id, user_id)
            )
            ''')

            # Orgs event Participants table 
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS org_event_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                org_id INTEGER,
                registered_date TEXT DEFAULT CURRENT_TIMESTAMP,
                attended BOOLEAN DEFAULT 0,
                FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
                FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
                UNIQUE (event_id, org_id)
            )
            ''')
        
            # Items table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                item_type TEXT NOT NULL, -- ropa, libros, hogar, otros
                item_terms TEXT NOT NULL, --gift, loan, exchange (CAN'T BE SOLD)
                item_status TEXT DEFAULT 'available', --available, borrowed, unavailable
                creation_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE (user_id, name, item_type)
            )
            ''')

            # exchange_requests table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_requests (
                exchange_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                requester_id INTEGER NOT NULL,
                owner_id INTEGER NOT NULL, -- The user_id of the item's owner
                message TEXT,
                exchange_status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'accepted', 'rejected'
                request_date TEXT NOT NULL, -- ISO 8601 format: YYYY-MM-DD HH:MM:SS
                decision_date TEXT, -- ISO 8601 format, filled when accepted/rejected
                FOREIGN KEY (item_id) REFERENCES items (item_id) ON DELETE CASCADE,
                FOREIGN KEY (requester_id) REFERENCES users (user_id) ON DELETE CASCADE,
                FOREIGN KEY (owner_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
            ''')
            
            #  achievements for users table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements_for_users (
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                points_required INTEGER,
                badge_icon TEXT --this is a unique identifier for badge icons stored in the images folder
            )
            ''')

            # achievements for orgs table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements_for_orgs (
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
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
                FOREIGN KEY (achievement_id) REFERENCES achievements_for_users(achievement_id)
            )
            ''')

            # orgs Achievements table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS org_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER,
                achievement_id INTEGER,
                date_earned TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES organizations(org_id),
                FOREIGN KEY (achievement_id) REFERENCES achievements_for_orgs(achievement_id)
            )
            ''')
            

            # Challenges for users
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS challenges_for_users (
                challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,  
                description TEXT NOT NULL,          
                goal_type TEXT NOT NULL, --siembra, reciclaje, caridad, enseñanza, software
                goal_target INTEGER DEFAULT 0,       -- The numeric target for the goal_type (e.g., 5, 100)
                points_reward INTEGER NOT NULL DEFAULT 0,    -- Points awarded upon successful completion
                time_allowed INTEGER DEFAULT NULL -- Time allowed in seconds (NULL = no limit)
            )
            ''')

            # Challenges for orgs
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS challenges_for_orgs (
                challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                goal_type TEXT NOT NULL, --siembra, reciclaje, caridad, enseñanza, software
                goal_target INTEGER DEFAULT 0,
                points_reward INTEGER DEFAULT 0,
                time_allowed INTEGER DEFAULT NULL
            )
            ''')

            # Individual users progress in challenges
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,           
                challenge_id INTEGER NOT NULL,     
                goal_progress INTEGER DEFAULT 0, 
                challenge_status TEXT NOT NULL DEFAULT 'active', --active, completed
                start_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deadline TEXT DEFAULT NULL,
                date_completed TEXT DEFAULT NULL,

                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (challenge_id) REFERENCES challenges_for_users(challenge_id) ON DELETE CASCADE,
                UNIQUE (user_id, challenge_id)
            )
            ''')

            # Individual organization progress in challenges
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS org_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,  
                challenge_id INTEGER NOT NULL,    
                goal_progress INTEGER DEFAULT 0,
                challenge_status TEXT NOT NULL DEFAULT 'active', --active, completed
                start_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deadline TEXT DEFAULT NULL,
                date_completed TEXT DEFAULT NULL,

                FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
                FOREIGN KEY (challenge_id) REFERENCES challenges_for_orgs(challenge_id) ON DELETE CASCADE,
                UNIQUE (org_id, challenge_id)
            )
            ''')



            # Map Points table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS map_points (
                point_id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                point_type TEXT NOT NULL, --tienda, reciclaje, punto_de_encuentro,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                address TEXT,
                creation_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
        except sqlite3.Error as e:
            print(f"Error setting up database: {e}")
        finally:
            conn.close()
    else:
        print("Error: Could not establish database connection.")

#FUNCTIONS FOR MANIPULATING DB 
def drop_table():
    database_file = "comunidad_verde.db"
    table_to_drop = input("table to drop: " )


    # Confirmation step (highly recommended)
    confirm = input(f"Are you absolutely sure you want to permanently delete the table '{table_to_drop}' and all its data? Type 'YES' to confirm: ")

    if confirm == "YES":
        conn = None 
        try:
            conn = sqlite3.connect(database_file)
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table_to_drop}")
            conn.commit()
            print(f"Table '{table_to_drop}' dropped successfully.")
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            # No rollback needed for DROP TABLE usually, but doesn't hurt
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    else:
        print("Operation cancelled. Table was not dropped.")

setup_database()








