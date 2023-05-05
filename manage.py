import argparse
import sqlite3
import uuid


def create_table_users(c):
    """Create the users table if it doesn't exist"""
    c.execute(
        """CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  apikey TEXT)"""
    )


def create_table_history(c):
    """Create the history table if it doesn't exist"""
    c.execute(
        """CREATE TABLE IF NOT EXISTS history
                 (uuid TEXT PRIMARY KEY,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP,
                  apikey TEXT,
                  priority INT,
                  type TEXT,
                  status TEXT,
                  prompt TEXT,
                  neg_prompt TEXT,
                  seed TEXT,
                  ref_img TEXT,
                  img TEXT,
                  width INT,
                  height INT,
                  guidance_scale FLOAT,
                  steps INT,
                  scheduler TEXT,
                  strength FLOAT,
                  base_model TEXT,
                  lora_model TEXT
                 )"""
    )


def create_user(c, username, apikey):
    """Create a user with the given username and apikey, or update the apikey if the username already exists"""
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    result = c.fetchone()
    if result is not None:
        raise ValueError(f"found exisitng user {username}, please use update")
    else:
        c.execute("INSERT INTO users (username, apikey) VALUES (?, ?)", (username, apikey))


def update_user(c, username, apikey):
    """Update the apikey for the user with the given username"""
    c.execute("SELECT apikey FROM users WHERE username=?", (username,))
    result = c.fetchone()
    if result is not None:
        old_apikey = result[0]
        c.execute("UPDATE history SET apikey=? WHERE apikey=?", (apikey, old_apikey))
        c.execute("UPDATE users SET apikey=? WHERE username=?", (apikey, username))
    else:
        raise ValueError("username does not exist! create it first?")


def delete_user(c, username):
    """Delete the user with the given username, or ignore the operation if the user does not exist"""
    c.execute("DELETE FROM history WHERE apikey=(SELECT apikey FROM users WHERE username=?)", (username,))
    c.execute("DELETE FROM users WHERE username=?", (username,))

def show_users(c, username="", details=False):
    """Print all users in the users table if username is not specified,
    or only the user with the given username otherwise"""
    if username:
        c.execute("SELECT username, apikey FROM users WHERE username=?", (username,))
        user = c.fetchone()
        if user:
            c.execute("SELECT COUNT(*) FROM history WHERE apikey=?", (user[1],))
            count = c.fetchone()[0]
            print(f"Username: {user[0]}, API Key: {user[1]}, Number of jobs: {count}")
            if details:
                c.execute("SELECT * FROM history WHERE apikey=?", (user[1],))
                result = c.fetchall()
                print(result)
        else:
            print(f"No user with username '{username}' found")
    else:
        c.execute("SELECT username, apikey FROM users")
        users = c.fetchall()
        for user in users:
            c.execute("SELECT COUNT(*) FROM history WHERE apikey=?", (user[1],))
            count = c.fetchone()[0]
            print(f"Username: {user[0]}, API Key: {user[1]}, Number of jobs: {count}")
            if details:
                c.execute("SELECT * FROM history WHERE apikey=?", (user[1],))
                result = c.fetchall()
                print(result)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")

    # Sub-parser for the "create" action
    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("username")
    create_parser.add_argument("apikey")

    # Sub-parser for the "update" action
    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("username")
    update_parser.add_argument("apikey")

    # Sub-parser for the "delete" action
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("username")

    # Sub-parser for the "delete" action
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("username", nargs="?", default="")
    list_parser.add_argument("--details", action="store_true", help="Showing more details")

    args = parser.parse_args()

    # Connect to the database (creates a new file if it doesn't exist)
    conn = sqlite3.connect("happysd.db")
    c = conn.cursor()

    # Create the users and history tables if they don't exist
    create_table_users(c)
    create_table_history(c)

    # Perform the requested action
    if args.action == "create":
        create_user(c, args.username, args.apikey)
        print("User created")
    elif args.action == "update":
        update_user(c, args.username, args.apikey)
        print("User updated")
    elif args.action == "delete":
        delete_user(c, args.username)
        print("User deleted")
    elif args.action == "list":
        show_users(c, args.username, args.details)

    # Commit the changes to the database
    conn.commit()

    # Close the connection
    conn.close()


if __name__ == "__main__":
    main()
