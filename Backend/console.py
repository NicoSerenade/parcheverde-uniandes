'''Testing console'''

from logic_idea import *

def console():
    # Initialize the database
    setup_database()
    
    functions = {
        # User Management
        "1": {"name": "Register User", "func": register_user, 
              "params": ["student_code", "username", "email", "password", "career (optional)", "interests (optional)"]},
        "2": {"name": "Authenticate User", "func": authenticate_user, 
              "params": ["student_code", "password"]},
        "3": {"name": "Update User Profile", "func": update_user_profile, 
              "params": ["user_id", "username (optional)", "email (optional)", "career (optional)", "interests (optional)"]},
        "4": {"name": "Get User by ID", "func": get_user_by_id, 
              "params": ["user_id"]},
        
        # Event Management
        "5": {"name": "Create Event", "func": create_event, 
              "params": ["title", "description", "event_type", "location", "event_date", "event_time", "organizer_id", "organizer_type"]},
        "6": {"name": "Register for Event", "func": register_for_event, 
              "params": ["event_id", "user_id"]},
        "7": {"name": "Mark Event Attendance", "func": mark_event_attendance, 
              "params": ["event_id", "user_id"]},
        "8": {"name": "Get Upcoming Events", "func": get_upcoming_events, 
              "params": ["limit (optional)", "event_type (optional)", "location (optional)"]},
        "9": {"name": "Get Event Participants", "func": get_event_participants, 
              "params": ["event_id"]},
        
        # Group Management
        "10": {"name": "Create Group", "func": create_group, 
               "params": ["name", "description", "topic", "creator_id"]},
        "11": {"name": "Join Group", "func": join_group, 
               "params": ["group_id", "user_id"]},
        "12": {"name": "Send Group Message", "func": send_group_message, 
               "params": ["group_id", "sender_id", "content"]},
        "13": {"name": "Get Group Messages", "func": get_group_messages, 
               "params": ["group_id", "limit (optional)"]},
        "14": {"name": "Get Groups by Topic", "func": get_groups_by_topic, 
               "params": ["topic (optional)", "limit (optional)"]},
        "15": {"name": "Get User Groups", "func": get_user_groups, 
               "params": ["user_id"]},
        "16": {"name": "Leave Group", "func": leave_group, 
               "params": ["group_id", "user_id"]},
        
        # Exchange Item Management
        "17": {"name": "Create Exchange Item", "func": create_exchange_item, 
               "params": ["user_id", "title", "description", "item_type"]},
        "18": {"name": "Update Item Status", "func": update_item_status, 
               "params": ["item_id", "status"]},
        "19": {"name": "Get Available Items", "func": get_available_items, 
               "params": ["item_type (optional)", "limit (optional)"]},
        "20": {"name": "Get User Items", "func": get_user_items, 
               "params": ["user_id"]},
        
        # Points and Achievements
        "21": {"name": "Award Points to User", "func": award_points_to_user, 
               "params": ["user_id", "points"]},
        "22": {"name": "Create Achievement", "func": create_achievement, 
               "params": ["name", "description", "points_required", "badge_icon (optional)"]},
        "23": {"name": "Get User Achievements", "func": get_user_achievements, 
               "params": ["user_id"]},
        "24": {"name": "Get All Achievements", "func": get_all_achievements, 
               "params": []},
        
        # Challenge Management
        "25": {"name": "Create Challenge", "func": create_challenge, 
               "params": ["title", "description", "goal_count", "goal_type", "points_reward", "start_date", "end_date"]},
        "26": {"name": "Join Challenge", "func": join_challenge, 
               "params": ["user_id", "challenge_id"]},
        "27": {"name": "Update User Challenges", "func": update_user_challenges, 
               "params": ["user_id", "activity_type"]},
        "28": {"name": "Get Active Challenges", "func": get_active_challenges, 
               "params": []},
        "29": {"name": "Get User Challenges", "func": get_user_challenges, 
               "params": ["user_id"]},
        
        # Map Points
        "30": {"name": "Add Map Point", "func": add_map_point, 
               "params": ["name", "description", "point_type", "latitude", "longitude", "address (optional)"]},
        "31": {"name": "Get Map Points", "func": get_map_points, 
               "params": ["point_type (optional)"]},
        
        # Organization Management
        "32": {"name": "Create Organization", "func": create_organization, 
               "params": ["name", "description", "interests (optional)"]},
        "33": {"name": "Get Organizations", "func": get_organizations, 
               "params": []},
        
        # Messaging
        "34": {"name": "Send Direct Message", "func": send_direct_message, 
               "params": ["sender_id", "recipient_id", "content"]},
        "35": {"name": "Get User Messages", "func": get_user_messages, 
               "params": ["user_id", "limit (optional)"]},
        "36": {"name": "Mark Message as Read", "func": mark_message_as_read, 
               "params": ["message_id"]},
        "37": {"name": "Get Conversation", "func": get_conversation, 
               "params": ["user1_id", "user2_id", "limit (optional)"]},
        
        # Search
        "38": {"name": "Search Users", "func": search_users, 
               "params": ["query", "limit (optional)"]},
        "39": {"name": "Search Events", "func": search_events, 
               "params": ["query", "limit (optional)"]},
        "40": {"name": "Search Groups", "func": search_groups, 
               "params": ["query", "limit (optional)"]},
    }
    
    # Categories for organization
    categories = {
        "User Management": ["1", "2", "3", "4"],
        "Event Management": ["5", "6", "7", "8", "9"],
        "Group Management": ["10", "11", "12", "13", "14", "15", "16"],
        "Exchange Item Management": ["17", "18", "19", "20"],
        "Points and Achievements": ["21", "22", "23", "24"],
        "Challenge Management": ["25", "26", "27", "28", "29"],
        "Map Points": ["30", "31"],
        "Organization Management": ["32", "33"],
        "Messaging": ["34", "35", "36", "37"],
        "Search": ["38", "39", "40"],
    }
    
    while True:
        print("\n===== Comunidad Verde Console =====")
        input("Presione enter para continuar: ")
        
        # Display functions by category
        for category, function_ids in categories.items():
            print(f"\n{category}:")
            for function_id in function_ids:
                func = functions[function_id]
                print(f"{function_id}. {func['name']}")
        
        print("\n0. Exit")
        
        choice = input("\nEnter function number to test: ")
        
        if choice == "0":
            print("Exiting Comunidad Verde Console.")
            break
        
        if choice in functions:
            func_info = functions[choice]
            print(f"\nTesting {func_info['name']}")
            
            # Collect parameter values
            args = []
            for param in func_info["params"]:
                value = input(f"Enter {param}: ")
                
                # Handle empty optional parameters
                if "(optional)" in param and value.strip() == "":
                    args.append(None)
                # Handle None values
                elif value.lower() == "none":
                    args.append(None)
                # Handle numbers
                elif value.isdigit():
                    args.append(int(value))
                elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                    args.append(float(value))
                # Regular string
                else:
                    args.append(value)
            
            try:
                # Call the function with collected arguments
                result = func_info["func"](*args)
                print("\nResult:")
                print(result)
            except Exception as e:
                print(f"Error executing function: {e}")
        else:
            print("Invalid function number. Please try again.")

if __name__ == "__main__":
    console()
