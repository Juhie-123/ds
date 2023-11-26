import sqlite3

def initialize_database():
    # Connect to SQLite database (creates a new database if it doesn't exist)
    conn = sqlite3.connect('database.db')

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Define the SQL queries to create tables
    create_user_table = '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT,
        first_name TEXT
    );
    '''

    create_note_table = '''
    CREATE TABLE IF NOT EXISTS note (
        id INTEGER PRIMARY KEY,
        data TEXT,
        date DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    '''

    # Execute the SQL queries
    cursor.execute(create_user_table)
    cursor.execute(create_note_table)
    print("run")
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
