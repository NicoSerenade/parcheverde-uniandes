# Project Backend

This folder contains the backend code for the project.

## Frontend Integration Guide

**Important:** All interactions between the frontend and the backend **must** go through the functions defined in the `Backend/logic.py` module.
* **Direct Database Access:** The frontend should **never** attempt to interact directly with `db_operator.py` or the database itself. The `logic.py` module handles all necessary database operations securely and consistently.

Please familiarize yourself with the functions available in `logic.py` and their returns before starting frontend development that requires backend interaction.

If you need new functions create a clickUP task in backend. But please note that a new function will make significant changes in the backend flow, so only ask for a new function if you consider is crucial for the MVP.

To get a better idea of which information we have in the database, open but NOT CHANGE the db_conn.py file, where there are the names of each table(mini database) and the columns with the information we have about them.