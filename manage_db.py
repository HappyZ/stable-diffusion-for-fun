import os
import argparse
import sqlite3
import fcntl
import uuid

from utilities.constants import APIKEY
from utilities.constants import UUID
from utilities.constants import USERS_TABLE_NAME
from utilities.constants import HISTORY_TABLE_NAME


# Function to acquire a lock on the database file
def acquire_lock(lock_file):
    lock_fd = open(lock_file, "w")
    fcntl.flock(lock_fd, fcntl.LOCK_EX)


# Function to release the lock on the database file
def release_lock(lock_file):
    lock_fd = open(lock_file, "w")
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    lock_fd.close()


USERS_TABLE_COLUMNS = [
    "id INTEGER PRIMARY KEY AUTOINCREMENT",
    "username TEXT UNIQUE",
    f"{APIKEY} TEXT",
    "quota INT DEFAULT 50",
]

HISTORY_TABLE_COLUMNS = [
    f"{UUID} TEXT PRIMARY KEY",
    "created_at TIMESTAMP",
    "updated_at TIMESTAMP",
    f"{APIKEY} TEXT",
    "priority INT",
    "type TEXT",
    "status TEXT",
    "prompt TEXT",
    "lang TEXT",
    "neg_prompt TEXT",
    "seed TEXT",
    "ref_img TEXT",
    "mask_img TEXT",
    "img TEXT",
    "width INT",
    "height INT",
    "guidance_scale FLOAT",
    "steps INT",
    "scheduler TEXT",
    "strength FLOAT",
    "base_model TEXT",
    "lora_model TEXT",
    "is_private BOOLEAN DEFAULT False",
]


def create_or_update_table(c, table_name):
    c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    )
    existing_table = c.fetchone()

    if table_name == USERS_TABLE_NAME:
        target_columns = USERS_TABLE_COLUMNS
    elif table_name == HISTORY_TABLE_NAME:
        target_columns = HISTORY_TABLE_COLUMNS
    else:
        target_columns = []

    if existing_table is None:
        # Table doesn't exist, so create it
        create_table_query = f"CREATE TABLE {table_name} {', '.join(target_columns)}"
        c.execute(create_table_query)
        print(f"Table '{table_name}' created successfully.")
    else:
        # Table exists, check if any columns are missing
        c.execute(f"PRAGMA table_info({table_name})")
        existing_columns = [column[1] for column in c.fetchall()]
        missing_columns = [
            column
            for column in target_columns
            if column.strip().split()[0] not in existing_columns
        ]

        if len(missing_columns) > 0:
            # Update the table to add missing columns
            for column in missing_columns:
                alter_table_query = (
                    f"ALTER TABLE {table_name} ADD COLUMN {column.strip()}"
                )
                c.execute(alter_table_query)
                print(f"Column '{column.strip()}' added to table '{table_name}'.")


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
    c.execute(f"SELECT * FROM {USERS_TABLE_NAME} WHERE username=?", (username,))
    result = c.fetchone()
    if result is not None:
        raise ValueError(f"found exisitng user {username}, please use update")
    else:
        c.execute(
            f"INSERT INTO {USERS_TABLE_NAME} (username, {APIKEY}) VALUES (?, ?)",
            (username, apikey),
        )


def update_user(c, username, apikey):
    """Update the apikey for the user with the given username"""
    c.execute(f"SELECT {APIKEY} FROM {USERS_TABLE_NAME} WHERE username=?", (username,))
    result = c.fetchone()
    if result is not None:
        old_apikey = result[0]
        c.execute(
            f"UPDATE {HISTORY_TABLE_NAME} SET {APIKEY}=? WHERE {APIKEY}=?",
            (apikey, old_apikey),
        )
        c.execute(
            f"UPDATE {USERS_TABLE_NAME} SET {APIKEY}=? WHERE username=?",
            (apikey, username),
        )
    else:
        raise ValueError("username does not exist! create it first?")


def update_quota(c, apikey, quota):
    c.execute(f"SELECT username FROM {USERS_TABLE_NAME} WHERE {APIKEY}=?", (apikey,))
    result = c.fetchone()
    if result is not None:
        c.execute(
            f"UPDATE {USERS_TABLE_NAME} SET quota=? WHERE {APIKEY}=?", (quota, apikey)
        )
    raise ValueError(f"{apikey} does not exist")


def update_username(c, apikey, username):
    c.execute(f"SELECT username FROM {USERS_TABLE_NAME} WHERE {APIKEY}=?", (apikey,))
    result = c.fetchone()
    if result is not None:
        c.execute(
            f"UPDATE {USERS_TABLE_NAME} SET username=? WHERE {APIKEY}=?",
            (username, apikey),
        )


def delete_user(c, username):
    """Delete the user with the given username, or ignore the operation if the user does not exist"""
    delete_jobs(c, username=username)
    c.execute(f"DELETE FROM {USERS_TABLE_NAME} WHERE username=?", (username,))
    print(f"removed {c.rowcount} entries")


def delete_jobs(c, job_uuid="", username=""):
    """Delete the job with the given uuid, or ignore the operation if the uuid does not exist"""
    if username:
        c.execute(
            f"SELECT img, ref_img, mask_img FROM {HISTORY_TABLE_NAME} WHERE apikey=(SELECT {APIKEY} FROM {USERS_TABLE_NAME} WHERE username=?)",
            (username,),
        )
        rows = c.fetchall()
        for row in rows:
            for filepath in row:
                if (
                    filepath is None
                    or "base64" in filepath
                    or not os.path.isfile(filepath)
                ):
                    continue
                try:
                    os.remove(filepath)
                except BaseException:
                    print(f"failed to remove {filepath}")
                    raise
        c.execute(
            f"DELETE FROM {HISTORY_TABLE_NAME} WHERE {APIKEY}=(SELECT {APIKEY} FROM {USERS_TABLE_NAME} WHERE username=?)",
            (username,),
        )
        print(f"removed {c.rowcount} entries")
    elif job_uuid:
        c.execute(
            f"SELECT img, ref_img, mask_img FROM {HISTORY_TABLE_NAME} WHERE uuid=?",
            (job_uuid,),
        )
        result = c.fetchone()
        if result is None:
            print(f"nothing is found with {job_uuid}")
            return
        for filepath in result:
            if filepath is None or "base64" in filepath or not os.path.isfile(filepath):
                continue
            try:
                os.remove(filepath)
            except BaseException:
                print(f"failed to remove {filepath}")
                raise
        c.execute(
            f"DELETE FROM {HISTORY_TABLE_NAME} WHERE uuid=?",
            (job_uuid,),
        )
        print(f"removed {c.rowcount} entries")


def show_users(c, username="", details=False):
    """Print all users in the users table if username is not specified,
    or only the user with the given username otherwise"""
    if username:
        c.execute(
            f"SELECT username, {APIKEY} FROM {USERS_TABLE_NAME} WHERE username=?",
            (username,),
        )
        user = c.fetchone()
        if user:
            c.execute(
                f"SELECT COUNT(*) FROM {HISTORY_TABLE_NAME} WHERE {APIKEY}=?",
                (user[1],),
            )
            count = c.fetchone()[0]
            print(f"Username: {user[0]}, API Key: {user[1]}, Number of jobs: {count}")
            if details:
                c.execute(
                    f"SELECT {UUID}, created_at, updated_at, type, status, width, height, steps, img, ref_img, mask_img, is_private FROM {HISTORY_TABLE_NAME} WHERE apikey=?",
                    (user[1],),
                )
                rows = c.fetchall()
                for row in rows:
                    print(row)
        else:
            print(f"No user with username '{username}' found")
    else:
        c.execute(f"SELECT username, {APIKEY} FROM {USERS_TABLE_NAME}")
        users = c.fetchall()
        for user in users:
            c.execute(
                f"SELECT COUNT(*) FROM {HISTORY_TABLE_NAME} WHERE {APIKEY}=?",
                (user[1],),
            )
            count = c.fetchone()[0]
            print(f"Username: {user[0]}, API Key: {user[1]}, Number of jobs: {count}")
            if details:
                c.execute(
                    f"SELECT * FROM {HISTORY_TABLE_NAME} WHERE {APIKEY}=?",
                    (user[1],),
                )
                rows = c.fetchall()
                for row in rows:
                    print(row)


def manage(args):
    # Path to the database file
    db_path = "happysd.db"
    # Path to the lock file
    lock_file = "/tmp/happysd_db.lock"

    if args.debug:
        db_path = "happysd_debug.db"

    # Connect to the database (creates a new file if it doesn't exist)
    conn = sqlite3.connect(db_path)

    # Acquire the lock
    acquire_lock(lock_file)

    try:
        # Access the database
        c = conn.cursor()

        # Create the users and history tables if they don't exist
        create_or_update_table(c, USERS_TABLE_NAME)
        create_or_update_table(c, HISTORY_TABLE_NAME)

        # Perform the requested action
        if args.action == "create":
            create_user(c, args.username, args.apikey)
        elif args.action == "update":
            if args.update_type == "user":
                update_user(c, args.username, args.apikey)
            elif args.update_type == "table":
                if args.table_action == "add":
                    modify_table(
                        c,
                        args.table_name,
                        args.table_action,
                        args.column_name,
                        args.column_type,
                    )
                elif args.table_action == "drop":
                    modify_table(
                        c, args.table_name, args.table_action, args.column_name
                    )
                elif args.table_action == "show":
                    modify_table(c, args.table_name, args.table_action)
            elif args.update_type == "quota":
                update_quota(c, args.apikey, args.quota)
        elif args.action == "delete":
            if args.delete_type == "user":
                delete_user(c, args.username)
            elif args.delete_type == "job":
                delete_jobs(c, job_uuid=args.job_id)
            elif args.delete_type == "jobs":
                delete_jobs(c, username=args.username)
        elif args.action == "list":
            show_users(c, args.username, args.details)
        elif args.action == "vacuum":
            c.execute("vacuum")

        # Commit the changes to the database
        conn.commit()

    finally:
        # Release the lock
        release_lock(lock_file)
        conn.close()


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debugging mode")
    subparsers = parser.add_subparsers(dest="action", required=True)

    # Sub-parser for the "create" action
    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("username")
    create_parser.add_argument("apikey")

    # Sub-parser for the "update" action
    update_parser = subparsers.add_parser("update")
    update_subparsers = update_parser.add_subparsers(dest="update_type", required=True)

    # Sub-parser for updating a user
    update_user_parser = update_subparsers.add_parser("user")
    update_user_parser.add_argument("username")
    update_user_parser.add_argument("apikey")

    # Sub-parser for updating a quota
    update_quota_parser = update_subparsers.add_parser("quota")
    update_quota_parser.add_argument("apikey")
    update_quota_parser.add_argument("quota")

    # Sub-parser for updating a table
    update_table_parser = update_subparsers.add_parser("table")
    update_table_subparsers = update_table_parser.add_subparsers(
        dest="table_action", required=True
    )

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
    delete_subparsers = delete_parser.add_subparsers(dest="delete_type", required=True)
    user_parser = delete_subparsers.add_parser("user")
    user_parser.add_argument("username")
    job_parser = delete_subparsers.add_parser("job")
    job_parser.add_argument("job_id")
    jobs_parser = delete_subparsers.add_parser("jobs")
    jobs_parser.add_argument("username")

    # Sub-parser for the "list" action
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("username", nargs="?", default="")
    list_parser.add_argument(
        "--details", action="store_true", help="Showing more details"
    )

    vacuum_parser = subparsers.add_parser("vacuum")

    args = parser.parse_args()

    manage(args)


if __name__ == "__main__":
    main()
