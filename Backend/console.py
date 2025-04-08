'''Testing console'''

import db_conn as c
import db_operator as op

c.setup_database()

def test_functions():
    choice = None
    while choice != 0:
       input("Press enter to cotinue: ")
       print("\n==== DB OPERATIONS MENU ====")
       print("\n0. Exit")
       
       print("\n==== USER OPERATIONS ====")
       print("1. Register New User")
       print("2. Authenticate User")
       print("3. Update User Profile")
       print("4. Delete My User Account")
       
       print("\n==== ORGANIZATION OPERATIONS ====")
       print("5. Register New Organization")
       print("6. Authenticate Organization")
       print("7. Update Organization Profile")
       print("8. Delete My Organization")
       
       print("\n==== ADMIN FUNCTIONS ====")
       print("9. Get User by ID")
       print("10. Delete User by ID")
       print("11. Get Organization by ID")
       print("12. Delete Organization by ID")
       
       print("\n==== EVENT OPERATIONS ====")
       print("13. Create New Event")
       print("14. Delete Event")
       print("15. Register for Event")
       
       choice = input("\nSelect option: ")
       
       if choice == "0":
              print("Exiting...")

       
       # USER OPERATIONS
       elif choice == "1":
              print("\n-- REGISTER USER --")
              student_code = input("Student code: ")
              password = input("Password: ")
              name = input("Name: ")
              email = input("Email: ")
              career = input("Career (optional): ") or None
              interests = input("Interests (optional): ") or None
              result = op.register_user(
                     student_code, password, name, email, career, interests
              )
              print(f"Result: {result}")
       
       elif choice == "2":
              print("\n-- AUTHENTICATE USER --")
              student_code = input("Student code: ")
              password = input("Password: ")
              result = op.authenticate_user(student_code, password)
              print(f"Result: {result}")
              logged_entity = result
       
       elif choice == "3":
              print("\n-- UPDATE USER PROFILE --")
              user_id = int(input("User ID: "))
              student_code = input("New student code (optional): ") or None
              password = input("New password (optional): ") or None
              name = input("New name (optional): ") or None
              email = input("New email (optional): ") or None
              career = input("New career (optional): ") or None
              interests = input("New interests (optional): ") or None
              result = op.update_user_profile(
                     user_id, student_code, password, name, email, career, interests
              )
              print(f"Result: {result}")
              
       elif choice == "4":
              print("\n-- DELETE MY USER ACCOUNT --")
              student_code = input("Student code: ")
              password = input("Password: ")
              result = op.delete_my_user(student_code, password)
              print(f"Result: {result}")
       
       # ORGANIZATION OPERATIONS
       elif choice == "5":
              print("\n-- REGISTER ORGANIZATION --")
              creator_student_code = input("Creator student code: ")
              password = input("Password: ")
              name = input("Organization name: ")
              email = input("Email: ")
              description = input("Description (optional): ") or None
              interests = input("Interests (optional): ") or None
              result = op.register_org(
                     creator_student_code, password, name, email, description, interests
              )
              print(f"Result: {result}")
              
       elif choice == "6":
              print("\n-- AUTHENTICATE ORGANIZATION --")
              name = input("Organization name: ")
              password = input("Password: ")
              result = op.authenticate_org(name, password)
              print(f"Result: {result}")
              
       elif choice == "7":
              print("\n-- UPDATE ORGANIZATION PROFILE --")
              org_id = int(input("Organization ID: "))
              creator_student_code = input("New creator student code (optional): ") or None
              password = input("New password (optional): ") or None
              name = input("New organization name (optional): ") or None
              email = input("New email (optional): ") or None
              description = input("New description (optional): ") or None
              interests = input("New interests (optional): ") or None
              result = op.update_org_profile(
                     org_id, creator_student_code, password, name, email, description, interests
              )
              print(f"Result: {result}")
              
       elif choice == "8":
              print("\n-- DELETE MY ORGANIZATION --")
              creator_student_code = input("Creator student code: ")
              password = input("Password: ")
              result = op.delete_my_org(creator_student_code, password)
              print(f"Result: {result}")
       
       # ADMIN FUNCTIONS
       elif choice == "9":
              print("\n-- GET USER BY ID --")
              user_id = int(input("User ID: "))
              result = op.get_user_by_id(user_id)
              print(f"Result: {result}")
       
       elif choice == "10":
              print("\n-- DELETE USER BY ID --")
              user_id = int(input("User ID: "))
              result = op.delete_user_by_id(user_id)
              print(f"Result: {result}")
              
       elif choice == "11":
              print("\n-- GET ORGANIZATION BY ID --")
              org_id = int(input("Organization ID: "))
              result = op.get_org_by_id(org_id)
              print(f"Result: {result}")
       
       elif choice == "12":
              print("\n-- DELETE ORGANIZATION BY ID --")
              org_id = int(input("Organization ID: "))
              result = op.delete_org_by_id(org_id)
              print(f"Result: {result}")

       # EVENT OPERATIONS
       elif choice == "13":
              print("\n-- CREATE NEW EVENT --")
              organizer_id = int(input("Organizer ID: "))
              organizer_type = input("Organizer Type (user/org): ")
              name = input("Event Name: ")
              description = input("Event Description: ")
              event_type = input("Event Type: ")
              location = input("Location: ")
              event_datetime = input("Event Date and Time (YYYY-MM-DD HH:MM:SS): ")
              result = op.create_event(
                     organizer_id, organizer_type, name, description, event_type, location, event_datetime
              )
              print(f"Event created with ID: {result}")
            
       elif choice == "14":
              print("\n-- DELETE EVENT --")
              event_id = int(input("Event ID to delete: "))
              entity_id = int(input("Your ID (as organizer): "))
              user_type = input("Your user type: ")
              result = op.delete_event(event_id, entity_id, user_type)
              print(f"Event deletion result: {result}")

       elif choice == "15":
              print("\n-- REGISTER FOR EVENT --")
              event_id = int(input("Event ID: "))
              entity_id = int(input("User/Organization ID: "))
              user_type = input("Entity Type (user/org): ")
              result = op.register_for_event(event_id, entity_id, user_type)
              print(f"Registration result: {result}")

       else:
              print("Invalid option. Try again.")

if __name__ == "__main__":
    test_functions()
