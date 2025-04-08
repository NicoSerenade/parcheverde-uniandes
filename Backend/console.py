'''Testing console'''

import db_conn as c
import db_operator as op
import pprint # For pretty printing results like lists/dictionaries

# Ensure database and tables exist before starting
c.setup_database()

# Simple helper for optional input
def optional_input(prompt):
    """Gets input, returns None if empty, otherwise the stripped string."""
    value = input(prompt).strip()
    return value if value else None

# Helper for integer input
def get_int_input(prompt):
    """Gets integer input, loops until valid."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a whole number.")

# Helper for float input
def get_float_input(prompt):
    """Gets float input, loops until valid."""
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a number (e.g., 4.712).")

def test_functions():
    choice = None
    while choice != "0":
        print("\n==============================")
        print("    COMUNIDAD VERDE CONSOLE   ")
        print("==============================")
        print("0. Exit")

        # --- USER REGISTRATION ---
        print("\n---- USER REGISTRATION ----")
        print(" 1. Register New User")
        print(" 2. Authenticate User")
        print(" 3. Update User Profile")
        print(" 4. Delete My User Account")

        # --- ORGANIZATION REGISTRATION ---
        print("\n---- ORGANIZATION REGISTRATION ----")
        print(" 5. Register New Organization")
        print(" 6. Authenticate Organization")
        print(" 7. Update Organization Profile")
        print(" 8. Delete My Organization")

        # --- ADMIN FUNCTIONS ---
        print("\n---- ADMIN FUNCTIONS ----")
        print(" 9. Get User by ID")
        print("10. Delete User by ID")
        print("11. Get Organization by ID")
        print("12. Delete Organization by ID")
        print("13. Create Achievement")
        print("14. Delete Achievement")
        print("15. Create Challenge")
        print("16. Delete Challenge")

        # --- USER/ORG INTERACTIONS ---
        print("\n---- USER/ORG INTERACTIONS ----")
        print("17. Search Organizations")
        print("18. Get Organization Members")
        print("19. Join Organization (User)")
        print("20. Leave Organization (User)")

        # --- EVENT OPERATIONS ---
        print("\n---- EVENT OPERATIONS ----")
        print("21. Search Events")
        print("22. Get Event Participants")
        print("23. Create Event")
        print("24. Delete Event")
        print("25. Join Event (User/Org)")
        print("26. Leave Event (User/Org)")
        print("27. Mark Event Attendance (User/Org)")

        # --- ITEM OPERATIONS ---
        print("\n---- ITEM OPERATIONS ----")
        print("28. Get Available Items")
        print("29. Create Item (User)")
        print("30. Update Item Status")

        # --- CHALLENGE OPERATIONS ---
        print("\n---- CHALLENGE OPERATIONS ----")
        print("31. Search Challenges (User/Org)")
        print("32. Get Active Challenges (User/Org)")
        print("33. Join Challenge (User/Org)")
        print("34. Update Challenge Progress (User/Org)")

        # --- ACHIEVEMENT OPERATIONS ---
        print("\n---- ACHIEVEMENT OPERATIONS ----")
        print("35. Search Achievements (User/Org)")
        print("36. [DEBUG] Add Points to User/Org") # Direct call to update_entity_points

        # --- USER-TO-USER INTERACTIONS ---
        print("\n---- USER-TO-USER INTERACTIONS ----")
        print("37. Search Users")

        # --- MAP OPERATIONS ---
        print("\n---- MAP OPERATIONS ----")
        print("38. Add Map Point")
        print("39. Delete Map Point")
        print("40. Get Map Points")
        print("------------------------------")

        choice = input("Select option: ").strip()
        print("------------------------------") # Separator after choice

        result = None # Reset result for each loop

        try: # Wrap main logic in try-except for potential input errors etc.
            # --- USER REGISTRATION ---
            if choice == "1":
                print("\n-- REGISTER USER --")
                student_code = input("Student code: ")
                password = input("Password: ")
                name = input("Name: ")
                email = input("Email (@uniandes.edu.co): ")
                career = optional_input("Career (optional): ")
                interests = optional_input("Interests (optional, comma-separated): ")
                result = op.register_user(student_code, password, name, email, career, interests)
                print(f"\nUser registered with ID: {result}" if result else "\nRegistration failed.")

            elif choice == "2":
                print("\n-- AUTHENTICATE USER --")
                student_code = input("Student code: ")
                password = input("Password: ")
                result = op.authenticate_user(student_code, password)
                if result:
                    print("\nAuthentication successful:")
                    pprint.pprint(result)
                else:
                    print("\nAuthentication failed.")

            elif choice == "3":
                print("\n-- UPDATE USER PROFILE --")
                user_id = get_int_input("User ID to update: ")
                print("Enter new values or press Enter to skip.")
                student_code = optional_input("New student code: ")
                password = optional_input("New password: ")
                name = optional_input("New name: ")
                email = optional_input("New email (@uniandes.edu.co): ")
                career = optional_input("New career: ")
                interests = optional_input("New interests (comma-separated): ")
                result = op.update_user_profile(user_id, student_code, password, name, email, career, interests)
                print(f"\nUpdate successful: {result}")

            elif choice == "4":
                print("\n-- DELETE MY USER ACCOUNT --")
                student_code = input("Your student code: ")
                password = input("Your password: ")
                confirm = input(f"Type 'DELETE {student_code}' to confirm deletion: ")
                if confirm == f"DELETE {student_code}":
                    result = op.delete_my_user(student_code, password)
                    print(f"\nDeletion successful: {result}")
                else:
                    print("\nDeletion cancelled or confirmation mismatch.")

            # --- ORGANIZATION REGISTRATION ---
            elif choice == "5":
                print("\n-- REGISTER ORGANIZATION --")
                creator_student_code = input("Your Student code (as creator): ")
                password = input("Organization Password: ")
                name = input("Organization Name: ")
                email = input("Organization Email (@uniandes.edu.co): ")
                description = optional_input("Description (optional): ")
                interests = optional_input("Interests (optional, comma-separated): ")
                result = op.register_org(creator_student_code, password, name, email, description, interests)
                print(f"\nOrg registered with ID: {result}" if result else "\nRegistration failed.")

            elif choice == "6":
                print("\n-- AUTHENTICATE ORGANIZATION --")
                name = input("Organization name: ")
                password = input("Password: ")
                result = op.authenticate_org(name, password)
                if result:
                    print("\nAuthentication successful:")
                    pprint.pprint(result)
                else:
                    print("\nAuthentication failed.")

            elif choice == "7":
                print("\n-- UPDATE ORGANIZATION PROFILE --")
                org_id = get_int_input("Organization ID to update: ")
                print("Enter new values or press Enter to skip.")
                creator_student_code = optional_input("New creator student code: ")
                password = optional_input("New password: ")
                name = optional_input("New organization name: ")
                email = optional_input("New email (@uniandes.edu.co): ")
                description = optional_input("New description: ")
                interests = optional_input("New interests (comma-separated): ")
                result = op.update_org_profile(org_id, creator_student_code, password, name, email, description, interests)
                print(f"\nUpdate successful: {result}")

            elif choice == "8":
                print("\n-- DELETE MY ORGANIZATION --")
                creator_student_code = input("Your student code (as creator): ")
                password = input("Organization password: ")
                confirm = input(f"Type 'DELETE ORG {creator_student_code}' to confirm: ")
                if confirm == f"DELETE ORG {creator_student_code}":
                    result = op.delete_my_org(creator_student_code, password)
                    print(f"\nDeletion successful: {result}")
                else:
                    print("\nDeletion cancelled or confirmation mismatch.")

            # --- ADMIN FUNCTIONS ---
            elif choice == "9":
                 print("\n-- GET USER BY ID --")
                 user_id = get_int_input("User ID: ")
                 result = op.get_user_by_id(user_id)
                 pprint.pprint(result)

            elif choice == "10":
                 print("\n-- DELETE USER BY ID --")
                 user_id = get_int_input("User ID to delete: ")
                 result = op.delete_user_by_id(user_id)
                 print(f"Deletion successful: {result}")

            elif choice == "11":
                 print("\n-- GET ORGANIZATION BY ID --")
                 org_id = get_int_input("Organization ID: ")
                 result = op.get_org_by_id(org_id)
                 pprint.pprint(result)

            elif choice == "12":
                 print("\n-- DELETE ORGANIZATION BY ID --")
                 org_id = get_int_input("Organization ID to delete: ")
                 result = op.delete_org_by_id(org_id)
                 print(f"Deletion successful: {result}")

            elif choice == "13":
                 print("\n-- CREATE ACHIEVEMENT --")
                 name = input("Achievement Name: ")
                 description = input("Description: ")
                 points_required = get_int_input("Points Required: ")
                 badge_icon = input("Badge Icon Path/URL: ")
                 user_type = input("For User or Org? (user/org): ").lower()
                 if user_type in ["user", "org"]:
                      result = op.create_achievement(name, description, points_required, badge_icon, user_type)
                      print(f"\nAchievement created with ID: {result}" if result else "\nCreation failed.")
                 else:
                      print("Invalid type. Must be 'user' or 'org'.")

            elif choice == "14":
                 print("\n-- DELETE ACHIEVEMENT --")
                 achievement_id = get_int_input("Achievement ID to delete: ")
                 user_type = input("From User or Org achievements? (user/org): ").lower()
                 if user_type in ["user", "org"]:
                      result = op.delete_achievement(achievement_id, user_type)
                      print(f"Deletion successful: {result}")
                 else:
                      print("Invalid type. Must be 'user' or 'org'.")

            elif choice == "15":
                 print("\n-- CREATE CHALLENGE --")
                 name = input("Challenge Name: ")
                 description = input("Description: ")
                 goal_type = input("Goal Type (e.g., siembra, reciclaje): ")
                 goal_target = get_int_input("Goal Target (numeric): ")
                 points_reward = get_int_input("Points Reward: ")
                 time_allowed_str = optional_input("Time Allowed (seconds, optional): ")
                 time_allowed = int(time_allowed_str) if time_allowed_str else None
                 user_type = input("For User or Org? (user/org): ").lower()
                 if user_type in ["user", "org"]:
                      result = op.create_challenge(name, description, goal_type, goal_target, points_reward, time_allowed, user_type)
                      print(f"\nChallenge created with ID: {result}" if result else "\nCreation failed.")
                 else:
                      print("Invalid type. Must be 'user' or 'org'.")

            elif choice == "16":
                 print("\n-- DELETE CHALLENGE --")
                 challenge_id = get_int_input("Challenge ID to delete: ")
                 user_type = input("From User or Org challenges? (user/org): ").lower()
                 if user_type in ["user", "org"]:
                      result = op.delete_challenge(challenge_id, user_type)
                      print(f"Deletion successful: {result}")
                 else:
                      print("Invalid type. Must be 'user' or 'org'.")

            # --- USER/ORG INTERACTIONS ---
            elif choice == "17":
                print("\n-- SEARCH ORGANIZATIONS --")
                query = optional_input("Search Query (name/desc, optional): ")
                interests = optional_input("Filter by Interests (optional): ")
                sort_by = optional_input("Sort by (name/points/creation_date, optional): ")
                result = op.search_orgs(query, interests, sort_by)
                print("\nSearch Results:")
                pprint.pprint(result)

            elif choice == "18":
                print("\n-- GET ORGANIZATION MEMBERS --")
                org_id = get_int_input("Organization ID: ")
                result = op.get_org_members(org_id)
                print("\nOrganization Members:")
                pprint.pprint(result)

            elif choice == "19":
                print("\n-- JOIN ORGANIZATION (User) --")
                user_id = get_int_input("Your User ID: ")
                org_id = get_int_input("Organization ID to join: ")
                result = op.join_org(org_id, user_id)
                print(f"\nJoin successful: {result}")

            elif choice == "20":
                print("\n-- LEAVE ORGANIZATION (User) --")
                user_id = get_int_input("Your User ID: ")
                org_id = get_int_input("Organization ID to leave: ")
                result = op.leave_org(org_id, user_id)
                print(f"\nLeave successful: {result}")

            # --- EVENT OPERATIONS ---
            elif choice == "21":
                print("\n-- SEARCH EVENTS --")
                query = optional_input("Search Query (name/desc, optional): ")
                event_type = optional_input("Filter by Event Type (optional): ")
                status = optional_input("Filter by Status (e.g., active, completed, optional): ")
                organizer_type = optional_input("Filter by Organizer Type (user/org, optional): ")
                start_date = optional_input("Start Date (YYYY-MM-DD HH:MM:SS, optional): ")
                end_date = optional_input("End Date (YYYY-MM-DD HH:MM:SS, optional): ")
                result = op.search_events(query, event_type, status, organizer_type, start_date, end_date)
                print("\nSearch Results:")
                pprint.pprint(result)

            elif choice == "22":
                 print("\n-- GET EVENT PARTICIPANTS --")
                 event_id = get_int_input("Event ID: ")
                 result = op.get_event_participants(event_id)
                 print("\nEvent Participants:")
                 pprint.pprint(result)

            elif choice == "23":
                 print("\n-- CREATE EVENT --")
                 organizer_id = get_int_input("Your User/Org ID (as organizer): ")
                 organizer_type = input("Are you 'user' or 'org'?: ").lower()
                 name = input("Event Name: ")
                 description = input("Description: ")
                 event_type = input("Event Type: ")
                 location = input("Location: ")
                 event_datetime = input("Date & Time (YYYY-MM-DD HH:MM:SS): ")
                 if organizer_type in ['user', 'org']:
                     result = op.create_event(organizer_id, organizer_type, name, description, event_type, location, event_datetime)
                     print(f"\nEvent created with ID: {result}" if result else "\nCreation failed.")
                 else:
                      print("Invalid organizer type.")

            elif choice == "24":
                 print("\n-- DELETE EVENT --")
                 event_id = get_int_input("Event ID to delete: ")
                 entity_id = get_int_input("Your User/Org ID (as organizer): ")
                 user_type = input("Your Type ('user' or 'org'): ").lower()
                 if user_type in ['user', 'org']:
                      result = op.delete_event(event_id, entity_id, user_type)
                      print(f"\nDeletion successful: {result}")
                 else:
                      print("Invalid type.")

            elif choice == "25":
                 print("\n-- JOIN EVENT (User/Org) --")
                 event_id = get_int_input("Event ID to join: ")
                 entity_id = get_int_input("Your User/Org ID: ")
                 user_type = input("Your Type ('user' or 'org'): ").lower()
                 if user_type in ['user', 'org']:
                      result = op.join_event(event_id, entity_id, user_type)
                      print(f"\nJoin successful: {result}")
                 else:
                      print("Invalid type.")

            elif choice == "26":
                 print("\n-- LEAVE EVENT (User/Org) --")
                 event_id = get_int_input("Event ID to leave: ")
                 entity_id = get_int_input("Your User/Org ID: ")
                 user_type = input("Your Type ('user' or 'org'): ").lower()
                 if user_type in ['user', 'org']:
                      result = op.leave_event(event_id, entity_id, user_type)
                      print(f"\nLeave successful: {result}")
                 else:
                      print("Invalid type.")

            elif choice == "27":
                 print("\n-- MARK EVENT ATTENDANCE (User/Org) --")
                 event_id = get_int_input("Event ID: ")
                 entity_id = get_int_input("Participant's User/Org ID: ")
                 user_type = input("Participant's Type ('user' or 'org'): ").lower()
                 if user_type in ['user', 'org']:
                     result = op.mark_event_attendance(event_id, entity_id, user_type)
                     print(f"\nAttendance marked successfully: {result}")
                 else:
                      print("Invalid type.")

            # --- ITEM OPERATIONS ---
            elif choice == "28":
                print("\n-- GET AVAILABLE ITEMS --")
                item_type = optional_input("Filter by Item Type (optional): ")
                item_terms = optional_input("Filter by Item Terms (regalo/prestamo/intercambio, optional): ")
                user_id_str = optional_input("Filter by User ID (optional): ")
                user_id = int(user_id_str) if user_id_str else None
                result = op.get_available_items(item_type, item_terms, user_id)
                print("\nAvailable Items:")
                pprint.pprint(result)

            elif choice == "29":
                print("\n-- CREATE ITEM (User) --")
                user_id = get_int_input("Your User ID: ")
                name = input("Item Name: ")
                description = input("Description: ")
                item_type = input("Item Type (e.g., ropa, tecnologia): ")
                item_terms = input("Terms (regalo/prestamo/intercambio): ")
                if item_terms in ['regalo', 'prestamo', 'intercambio']:
                    result = op.create_item(user_id, name, description, item_type, item_terms)
                    print(f"\nItem created with ID: {result}" if result else "\nCreation failed.")
                else:
                    print("Invalid terms. Must be 'regalo', 'prestamo', or 'intercambio'.")

            elif choice == "30":
                print("\n-- UPDATE ITEM STATUS --")
                item_id = get_int_input("Item ID to update: ")
                status = input("New Status (e.g., available, borrowed, unavailable): ")
                result = op.update_item_status(item_id, status)
                print(f"\nUpdate successful: {result}")

            # --- CHALLENGE OPERATIONS ---
            elif choice == "31":
                print("\n-- SEARCH CHALLENGES (User/Org) --")
                user_type = input("Search challenges for 'user' or 'org'?: ").lower()
                if user_type in ['user', 'org']:
                    result = op.search_challenges(user_type)
                    print(f"\nChallenges for {user_type}:")
                    pprint.pprint(result)
                else:
                    print("Invalid type.")

            elif choice == "32":
                print("\n-- GET ACTIVE CHALLENGES (User/Org) --")
                entity_id = get_int_input("User/Org ID: ")
                user_type = input("Type ('user' or 'org'): ").lower()
                if user_type in ['user', 'org']:
                    result = op.get_active_challenges(entity_id, user_type)
                    print(f"\nActive challenges for {user_type} {entity_id}:")
                    pprint.pprint(result)
                else:
                    print("Invalid type.")

            elif choice == "33":
                print("\n-- JOIN CHALLENGE (User/Org) --")
                entity_id = get_int_input("Your User/Org ID: ")
                user_type = input("Your Type ('user' or 'org'): ").lower()
                challenge_id = get_int_input("Challenge ID to join: ")
                if user_type in ['user', 'org']:
                     result = op.join_challenge(entity_id, user_type, challenge_id)
                     print(f"\nJoin successful: {result}")
                else:
                     print("Invalid type.")

            elif choice == "34":
                print("\n-- UPDATE CHALLENGE PROGRESS (User/Org) --")
                entity_id = get_int_input("Your User/Org ID: ")
                user_type = input("Your Type ('user' or 'org'): ").lower()
                challenge_id = get_int_input("Challenge ID to update: ")
                progress_increment = get_int_input("Progress Increment: ")
                if user_type in ['user', 'org']:
                    result = op.update_challenges_progress(entity_id, user_type, challenge_id, progress_increment)
                    print(f"\nProgress update successful: {result}")
                else:
                    print("Invalid type.")

            # --- ACHIEVEMENT OPERATIONS ---
            elif choice == "35":
                print("\n-- SEARCH ACHIEVEMENTS (User/Org) --")
                user_type = input("Search achievements for 'user' or 'org'?: ").lower()
                if user_type in ['user', 'org']:
                    result = op.search_achievements(user_type)
                    print(f"\nAchievements for {user_type}:")
                    pprint.pprint(result)
                else:
                    print("Invalid type.")

            elif choice == "36":
                print("\n-- [DEBUG] ADD POINTS TO USER/ORG --")
                entity_id = get_int_input("User/Org ID: ")
                user_type = input("Type ('user' or 'org'): ").lower()
                points_to_add = get_int_input("Points to Add: ")
                if user_type in ['user', 'org']:
                     result = op.update_entity_points(entity_id, user_type, points_to_add)
                     print(f"\nPoints added. Newly unlocked achievement: {result}")
                else:
                     print("Invalid type.")

            # --- USER-TO-USER INTERACTIONS ---
            elif choice == "37":
                print("\n-- SEARCH USERS --")
                query = optional_input("Search Query (name/email, optional): ")
                career = optional_input("Filter by Career (optional): ")
                interests = optional_input("Filter by Interests (optional): ")
                result = op.search_users(query, career, interests)
                print("\nSearch Results:")
                pprint.pprint(result)

            # --- MAP OPERATIONS ---
            elif choice == "38":
                 print("\n-- ADD MAP POINT --")
                 user_id = int(input("User id: "))
                 user_type = input("User type (must be admin or store): ")
                 name = input("Point Name: ")
                 description = input("Description: ")
                 point_type = input("Point Type (e.g., tienda, reciclaje): ")
                 latitude = get_float_input("Latitude: ")
                 longitude = get_float_input("Longitude: ")
                 address = optional_input("Address (optional): ")
                 result = op.add_map_point(user_id, user_type, name, description, point_type, latitude, longitude, address)
                 print(f"\nMap point created with ID: {result}" if result else "\nCreation failed.")

            elif choice == "39":
                 print("\n-- DELETE MAP POINTS --")
                 user_id = get_int_input("User ID: ")
                 user_type = input("User type (must be admin or store): ")
                 point_id = int(input("Point ID: "))
                 result = op.delete_map_point(user_id, user_type, point_id)
                 print("\nMap Points:")
                 pprint.pprint(result)


            elif choice == "40":
                 print("\n-- GET MAP POINTS --")
                 point_type = optional_input("Filter by Point Type (optional): ")
                 result = op.get_map_points(point_type)
                 print("\nMap Points:")
                 pprint.pprint(result)


            # --- EXIT ---
            elif choice == "0":
                print("Exiting console...")
            else:
                print("Invalid option. Please try again.")

        except Exception as e:
             print(f"\n--- An unexpected error occurred: {e} ---")
             # This catches errors during input conversion or other unexpected issues

        input("\nPress Enter to continue...") # Pause before showing the menu again

if __name__ == "__main__":
    print("Starting Test Console...")
    test_functions()
    print("Console finished.")