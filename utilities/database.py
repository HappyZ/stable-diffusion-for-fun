import os
import datetime
import sqlite3
import uuid

from utilities.constants import APIKEY
from utilities.constants import UUID
from utilities.constants import KEY_PRIORITY
from utilities.constants import KEY_JOB_TYPE
from utilities.constants import VALUE_JOB_TXT2IMG
from utilities.constants import VALUE_JOB_IMG2IMG
from utilities.constants import VALUE_JOB_INPAINTING
from utilities.constants import KEY_JOB_STATUS
from utilities.constants import VALUE_JOB_PENDING
from utilities.constants import VALUE_JOB_RUNNING
from utilities.constants import VALUE_JOB_DONE

from utilities.constants import OUTPUT_ONLY_KEYS
from utilities.constants import OPTIONAL_KEYS
from utilities.constants import REQUIRED_KEYS

from utilities.constants import REFERENCE_IMG
from utilities.constants import BASE64IMAGE

from utilities.constants import HISTORY_TABLE_NAME
from utilities.constants import USERS_TABLE_NAME
from utilities.logger import DummyLogger


class Database:
    """This class represents a SQLite database and assumes single-thread usage."""

    def __init__(self, logger: DummyLogger = DummyLogger()):
        """Initialize the class with a logger instance, but without a database connection or cursor."""
        self.__connect = None  # the database connection object
        self.__cursor = None  # the cursor object for executing SQL statements
        self.__logger = logger  # the logger object for logging messages

    def connect(self, db_filepath) -> bool:
        """
        Connect to the SQLite database file specified by `db_filepath`.

        Returns True if the connection was successful, otherwise False.
        """
        if not os.path.isfile(db_filepath):
            self.__logger.error(f"{db_filepath} does not exist!")
            return False
        self.__connect = sqlite3.connect(db_filepath, check_same_thread=False)
        self.__cursor = self.__connect.cursor()
        self.__logger.info(f"Connected to database {db_filepath}")
        return True

    def validate_user(self, apikey: str) -> str:
        """
        Validate if the provided API key exists in the users table and return the corresponding
        username if found, or an empty string otherwise.
        """
        if self.__cursor is None:
            self.__logger.error("Did you forget to connect to the database?")
            return ""

        query = f"SELECT username FROM {USERS_TABLE_NAME} WHERE {APIKEY}=?"
        self.__cursor.execute(query, (apikey,))
        result = self.__cursor.fetchone()

        self.__logger.debug(result)

        if result is not None:
            return result[0]  # the first column is the username

        return ""

    def get_all_pending_jobs(self, apikey: str = "") -> list:
        return self.get_jobs(apikey=apikey, job_status=VALUE_JOB_PENDING)

    def count_all_pending_jobs(self, apikey: str) -> int:
        """
        Count the number of pending jobs in the HISTORY_TABLE_NAME table for the specified API key.

        Returns the number of pending jobs found.
        """
        if self.__cursor is None:
            self.__logger.error("Did you forget to connect to the database?")
            return 0

        # Construct the SQL query string and list of arguments
        query_string = f"SELECT COUNT(*) FROM {HISTORY_TABLE_NAME} WHERE {APIKEY}=? AND {KEY_JOB_STATUS}=?"
        query_args = (apikey, VALUE_JOB_PENDING)

        # Execute the query and return the count
        self.__cursor.execute(query_string, query_args)
        result = self.__cursor.fetchone()
        return result[0]

    def get_jobs(self, job_uuid="", apikey="", job_status="") -> list:
        """
        Get a list of jobs from the HISTORY_TABLE_NAME table based on optional filters.

        If `job_uuid` or `apikey` or `job_status` is provided, the query will include that filter.

        Returns a list of jobs matching the filters provided.
        """
        if self.__cursor is None:
            self.__logger.error("Did you forget to connect to the database?")
            return []

        # construct the SQL query string and list of arguments based on the provided filters
        query_args = []
        query_filters = []
        if job_uuid:
            query_filters.append(f"{UUID} = ?")
            query_args.append(job_uuid)
        if apikey:
            query_filters.append(f"{APIKEY} = ?")
            query_args.append(apikey)
        if job_status:
            query_filters.append(f"{KEY_JOB_STATUS} = ?")
            query_args.append(job_status)
        columns = OUTPUT_ONLY_KEYS + REQUIRED_KEYS + OPTIONAL_KEYS
        query_string = f"SELECT {', '.join(columns)} FROM {HISTORY_TABLE_NAME}"
        if query_filters:
            query_string += f" WHERE {' AND '.join(query_filters)}"

        # execute the query and return the results
        self.__cursor.execute(query_string, tuple(query_args))
        rows = self.__cursor.fetchall()

        jobs = []
        for row in rows:
            job = {
                columns[i]: row[i] for i in range(len(columns)) if row[i] is not None
            }
            jobs.append(job)

        return jobs

    def insert_new_job(self, job_dict: dict, job_uuid="") -> bool:
        """
        Insert a new job into the HISTORY_TABLE_NAME table.

        If `job_uuid` is not provided, a new UUID will be generated automatically.

        Returns True if the insertion was successful, otherwise False.
        """
        if self.__cursor is None:
            self.__logger.error("Did you forget to connect to the database?")
            return False

        if not job_uuid:
            job_uuid = str(uuid.uuid4())
        self.__logger.info(f"inserting a new job with {job_uuid}")

        values = [job_uuid, VALUE_JOB_PENDING]
        columns = [UUID, KEY_JOB_STATUS] + REQUIRED_KEYS + OPTIONAL_KEYS
        for column in REQUIRED_KEYS + OPTIONAL_KEYS:
            values.append(job_dict.get(column, None))
        
        query = f"INSERT INTO {HISTORY_TABLE_NAME} ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])})"
        self.__cursor.execute(query, tuple(values))
        self.__connect.commit()
        return True

    def update_job(self, job_dict: dict, job_uuid: str) -> bool:
        """
        Update an existing job in the HISTORY_TABLE_NAME table with the given `job_uuid`.

        Returns True if the update was successful, otherwise False.
        """
        if self.__cursor is None:
            self.__logger.error("Did you forget to connect to the database?")
            return False

        values = []
        columns = []
        for column in OUTPUT_ONLY_KEYS + REQUIRED_KEYS + OPTIONAL_KEYS:
            value = job_dict.get(column, None)
            if value is not None:
                columns.append(column)
                values.append(value)

        set_clause = ", ".join([f"{column}=?" for column in columns])
        # Add current timestamp to update query
        set_clause += ", updated_at=?"
        values.append(datetime.datetime.now())

        query = f"UPDATE {HISTORY_TABLE_NAME} SET {set_clause} WHERE {UUID}=?"

        values.append(job_uuid)

        self.__cursor.execute(query, tuple(values))
        self.__connect.commit()
        return True

    def cancel_job(self, job_uuid: str = "", apikey: str = "") -> bool:
        """Cancel the job with the given job_uuid or apikey.
        If job_uuid or apikey is provided, delete corresponding rows from table history if "status" matches "pending".

        Args:
            job_uuid (str, optional): Unique job identifier. Defaults to "".
            apikey (str, optional): API key associated with the job. Defaults to "".

        Returns:
            bool: True if the job was cancelled successfully, False otherwise.
        """
        if not job_uuid and not apikey:
            self.__logger.error(f"either {UUID} or {APIKEY} must be provided.")
            return False

        if job_uuid:
            self.__cursor.execute(
                f"DELETE FROM {HISTORY_TABLE_NAME} WHERE {UUID}=? AND {KEY_JOB_STATUS}=?",
                (
                    job_uuid,
                    VALUE_JOB_PENDING,
                ),
            )
        else:
            self.__cursor.execute(
                f"DELETE FROM {HISTORY_TABLE_NAME} WHERE {APIKEY}=? AND {KEY_JOB_STATUS}=?",
                (
                    apikey,
                    VALUE_JOB_PENDING,
                ),
            )

        if self.__cursor.rowcount == 0:
            self.__logger.info("No matching rows found.")
            return False
        else:
            self.__logger.info(f"{self.__cursor.rowcount} rows cancelled.")

        self.__connect.commit()
        return True

    def delete_job(self, job_uuid: str = "", apikey: str = "") -> bool:
        """Delete the job with the given uuid or apikey"""
        if job_uuid:
            self.__cursor.execute(
                f"DELETE FROM {HISTORY_TABLE_NAME} WHERE {UUID}=?", (job_uuid,)
            )
        elif apikey:
            self.__cursor.execute(
                f"DELETE FROM {HISTORY_TABLE_NAME} WHERE {APIKEY}=?", (apikey,)
            )
        else:
            self.logger.error(f"either {UUID} or {APIKEY} must be provided.")
            return False

        if self.__cursor.rowcount == 0:
            print("No matching rows found.")
        else:
            self.logger.info(f"{self.__cursor.rowcount} rows deleted.")
        self.__connect.commit()
        return True

    def safe_disconnect(self):
        if self.__connect is not None:
            self.__connect.commit()
            self.__connect.close()
            self.__logger.info("Disconnected from database.")
        else:
            self.__logger.warn("No database connection to close.")
