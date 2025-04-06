'''Testing console'''
import db_conn as c
import db_operator as op

c.setup_database()

def test_functions():
    while True:
       print("\n==== DB OPERATIONS MENU ====")
       print("0. Exit")
       print("1. Register New User")
       print("2. Authenticate User")
       print("3. Update User Profile")
       print("4. Get User by ID")
       print("5. Get User by ID")
        
        
       choice = input("\nSelect option: ")

       if choice == "0":
              print("Exiting...")
              break
        
       elif choice == "1":
              print("\n-- REGISTER USER --")
              student_code = input("Student code: ")
              username = input("Username: ")
              email = input("Email: ")
              password = input("Password: ")
              career = input("Career (optional): ") or None
              interests = input("Interests (optional): ") or None
       
              result = op.register_user(
              student_code, username, email, password, career, interests
              )
              print(f"Result: {result}")
       
       elif choice == "2":
              print("\n-- AUTHENTICATE USER --")
              student_code = input("Student code: ")
              password = input("Password: ")
              
              result = op.authenticate_user(student_code, password)
              print(f"Result: {result}")
       
       elif choice == "3":
              print("\n-- UPDATE USER PROFILE --")
              user_id = int(input("User ID: "))
              student_code = input("New student code (optional): ") or None
              username = input("New username (optional): ") or None
              email = input("New email (optional): ") or None
              password = input("New password (optional): ") or None
              career = input("New career (optional): ") or None
              interests = input("New interests (optional): ") or None
              
              result = op.update_user_profile(
                     user_id, student_code, username, email, 
                     password, career, interests
              )
              print(f"Result: {result}")
       
       elif choice == "4":
              print("\n-- GET USER BY ID --")
              user_id = int(input("User ID: "))
              
              result = op.get_user_by_id(user_id)
              print(f"Result: {result}")
       
       elif choice == "5":
              print("\n-- DELETE USER BY ID --")
              user_id = int(input("User ID: "))
              
              result = op.delete_user_by_id(user_id)
              print(f"Result: {result}")
       
       else:
              print("Invalid option. Try again.")
       
       # Ask to continue
       cont = input("\nContinue? (y/n): ")
       if cont.lower() != 'y':
              print("Exiting...")
              break

if __name__ == "__main__":
    test_functions()
