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


def modify_table(c, table_name, operation, column_name=None, data_type=None):
    """Add or drop a column in the table"""
    if operation == "add" and column_name and data_type:
        c.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type}")
    elif operation == "drop" and column_name:
        c.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
    elif operation == "show":
        rows = c.execute(f"PRAGMA table_info({table_name})")
        # Print the column names and types
        for row in rows:
            column_name = row[1]
            column_type = row[2]
            print(f"{column_name}: {column_type}")
    else:
        raise ValueError("Invalid operation or missing column name/data type")


def create_user(c, username, apikey):
    """Create a user with the given username and apikey, or update the apikey if the username already exists"""
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    result = c.fetchone()
    if result is not None:
        raise ValueError(f"found exisitng user {username}, please use update")
    else:
        c.execute(
            "INSERT INTO users (username, apikey) VALUES (?, ?)", (username, apikey)
        )


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
    c.execute(
        "DELETE FROM history WHERE apikey=(SELECT apikey FROM users WHERE username=?)",
        (username,),
    )
    c.execute("DELETE FROM users WHERE username=?", (username,))


def delete_job(c, uuid):
    """Delete the job with the given uuid, or ignore the operation if the uuid does not exist"""
    c.execute(
        "DELETE FROM history WHERE uuid=?",
        (uuid,),
    )


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
                c.execute(
                    "SELECT uuid, created_at, type, status, width, height, steps FROM history WHERE apikey=?",
                    (user[1],),
                )
                rows = c.fetchall()
                for row in rows:
                    print(row)
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
                c.execute(
                    "SELECT uuid, created_at, type, status, width, height, steps FROM history WHERE apikey=?",
                    (user[1],),
                )
                rows = c.fetchall()
                for row in rows:
                    print(row)


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
    update_subparsers = update_parser.add_subparsers(dest="update_type")

    # Sub-parser for updating a user
    update_user_parser = update_subparsers.add_parser("user")
    update_user_parser.add_argument("username")
    update_user_parser.add_argument("apikey")

    # Sub-parser for updating a table
    update_table_parser = update_subparsers.add_parser("table")
    update_table_subparsers = update_table_parser.add_subparsers(dest="table_action")

    # Sub-parser for adding a column to a table
    table_add_parser = update_table_subparsers.add_parser("add")
    table_add_parser.add_argument("table_name")
    table_add_parser.add_argument("column_name")
    table_add_parser.add_argument("column_type")

    # Sub-parser for dropping a column from a table
    table_drop_parser = update_table_subparsers.add_parser("drop")
    table_drop_parser.add_argument("table_name")
    table_drop_parser.add_argument("column_name")

    # Sub-parser for showing a table
    table_drop_parser = update_table_subparsers.add_parser("show")
    table_drop_parser.add_argument("table_name")

    # Sub-parser for the "delete" action
    delete_parser = subparsers.add_parser("delete")
    delete_subparsers = delete_parser.add_subparsers(dest="delete_type")
    user_parser = delete_subparsers.add_parser("user")
    user_parser.add_argument("username")
    job_parser = delete_subparsers.add_parser("job")
    job_parser.add_argument("job_id")

    # Sub-parser for the "list" action
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("username", nargs="?", default="")
    list_parser.add_argument(
        "--details", action="store_true", help="Showing more details"
    )

    # Sub-parser for the "modify" action
    modify_parser = subparsers.add_parser("modify")
    modify_parser.add_argument("table")
    modify_parser.add_argument("--add-column")
    modify_parser.add_argument("--drop-column")

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
    elif args.action == "update":
        if args.update_type == "user":
            update_user(c, args.username, args.apikey)
        elif args.update_type == "table":
            if args.table_action == "add":
                modify_table(c, args.table_name, args.table_action, args.column_name, args.column_type)
            elif args.table_action == "drop":
                modify_table(c, args.table_name, args.table_action, args.column_name)
            elif args.table_action == "show":
                modify_table(c, args.table_name, args.table_action)
    elif args.action == "delete":
        if args.delete_type == "user":
            delete_user(c, args.username)
        elif args.delete_type == "job":
            delete_job(c, args.job_id)
    elif args.action == "list":
        show_users(c, args.username, args.details)

    # Commit the changes to the database
    conn.commit()

    # Close the connection
    conn.close()


if __name__ == "__main__":
    main()
