import os
import datetime
import sqlite3
import fcntl
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
from utilities.constants import VALUE_JOB_DONE
from utilities.constants import LOCK_FILEPATH

from utilities.constants import OUTPUT_ONLY_KEYS
from utilities.constants import ANONYMOUS_KEYS
from utilities.constants import OPTIONAL_KEYS
from utilities.constants import REQUIRED_KEYS
from utilities.constants import INTERNAL_KEYS

from utilities.constants import REFERENCE_IMG
from utilities.constants import MASK_IMG
from utilities.constants import BASE64IMAGE
from utilities.constants import IMAGE_NOT_FOUND_BASE64

from utilities.constants import HISTORY_TABLE_NAME
from utilities.constants import USERS_TABLE_NAME
from utilities.logger import DummyLogger

from utilities.times import get_epoch_now
from utilities.times import epoch_to_string
from utilities.images import save_image
from utilities.images import load_image


# Function to acquire a lock on the database file
def acquire_lock():
    lock_fd = open(LOCK_FILEPATH, "w")
    fcntl.flock(lock_fd, fcntl.LOCK_EX)


# Function to release the lock on the database file
def release_lock():
    lock_fd = open(LOCK_FILEPATH, "w")
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    lock_fd.close()


class Database:
    """This class represents a SQLite database and assumes single-thread usage."""

    def __init__(self, logger: DummyLogger = DummyLogger(), image_folderpath=""):
        """Initialize the class with a logger instance, but without a database connection or cursor."""
        self.__connect = None  # the database connection object
        self.is_connected = False
        self.__cursor = None  # the cursor object for executing SQL statements
        self.__logger = logger  # the logger object for logging messages

        self.__image_output_folder = ""
        self.set_image_output_folder(image_folderpath)

    def set_image_output_folder(self, image_folderpath):
        self.__image_output_folder = image_folderpath  # output image to a folder instead of storing it in sqlite3
        if image_folderpath:
            try:
                os.makedirs(image_folderpath, exist_ok=True)
            except OSError as err:
                self.__logger.warn(f"{image_folderpath} failed to create: {err}")
                self.__image_output_folder = ""

    def connect(self, db_filepath) -> bool:
        """
        Connect to the SQLite database file specified by `db_filepath`.

        Returns True if the connection was successful, otherwise False.
        """
        if not os.path.isfile(db_filepath):
            self.__logger.error(f"{db_filepath} does not exist!")
            return False
        self.__connect = sqlite3.connect(db_filepath, check_same_thread=False)
        self.__logger.info(f"Connected to database {db_filepath}")
        self.is_connected = True
        return True

    def get_cursor(self):
        if not self.is_connected:
            raise RuntimeError("Did you forget to connect() to the database?")
        return self.__connect.cursor()

    def commit(self):
        if not self.is_connected:
            raise RuntimeError("Did you forget to connect() to the database?")
        return self.__connect.commit()

    def validate_user(self, apikey: str) -> str:
        """
        Validate if the provided API key exists in the users table and return the corresponding
        username if found, or an empty string otherwise.
        """
        query = f"SELECT username FROM {USERS_TABLE_NAME} WHERE {APIKEY}=?"

        c = self.get_cursor()
        result = c.execute(query, (apikey,)).fetchone()

        if result is not None:
            return result[0]
        return ""

    def get_one_pending_job(self, apikey: str = "") -> list:
        return self.get_jobs(apikey=apikey, job_status=VALUE_JOB_PENDING, limit_count=1)

    def count_all_pending_jobs(self, apikey: str) -> int:
        """
        Count the number of pending jobs in the HISTORY_TABLE_NAME table for the specified API key.

        Returns the number of pending jobs found.
        """
        # Construct the SQL query string and list of arguments
        query_string = f"SELECT COUNT(*) FROM {HISTORY_TABLE_NAME} WHERE {APIKEY}=? AND {KEY_JOB_STATUS}=?"
        query_args = (apikey, VALUE_JOB_PENDING)

        # Execute the query and return the count
        c = self.get_cursor()
        result = c.execute(query_string, query_args).fetchone()
        return result[0]

    def get_random_jobs(self, limit_count=0) -> list:
        query = f"SELECT {', '.join(ANONYMOUS_KEYS)} FROM {HISTORY_TABLE_NAME} WHERE {KEY_JOB_STATUS} = '{VALUE_JOB_DONE}' AND RANDOM() <= .3 LIMIT {limit_count}"

        # execute the query and return the results
        c = self.get_cursor()
        rows = c.execute(query).fetchall()

        jobs = []
        for row in rows:
            job = {
                ANONYMOUS_KEYS[i]: row[i]
                for i in range(len(ANONYMOUS_KEYS))
                if row[i] is not None
            }
            # load image to job if has one
            for key in [BASE64IMAGE, REFERENCE_IMG, MASK_IMG]:
                if key in job and "base64" not in job[key]:
                    data = load_image(job[key], to_base64=True)
                    job[key] = data if data else IMAGE_NOT_FOUND_BASE64
            jobs.append(job)

        return jobs

    def get_jobs(self, job_uuid="", apikey="", job_status="", limit_count=0) -> list:
        """
        Get a list of jobs from the HISTORY_TABLE_NAME table based on optional filters.

        If `job_uuid` or `apikey` or `job_status` is provided, the query will include that filter.

        Returns a list of jobs matching the filters provided.
        """
        # construct the SQL query string and list of arguments based on the provided filters
        values = []
        query_filters = []
        if job_uuid:
            query_filters.append(f"{UUID} = ?")
            values.append(job_uuid)
        if apikey:
            query_filters.append(f"{APIKEY} = ?")
            values.append(apikey)
        if job_status:
            query_filters.append(f"{KEY_JOB_STATUS} = ?")
            values.append(job_status)

        columns = OUTPUT_ONLY_KEYS + REQUIRED_KEYS + OPTIONAL_KEYS
        query = f"SELECT {', '.join(columns)} FROM {HISTORY_TABLE_NAME}"
        if query_filters:
            query += f" WHERE {' AND '.join(query_filters)}"
        query += f" ORDER BY created_at DESC"
        if limit_count:
            query += f" LIMIT {limit_count}"

        # execute the query and return the results
        c = self.get_cursor()
        rows = c.execute(query, tuple(values)).fetchall()

        jobs = []
        for row in rows:
            job = {
                columns[i]: row[i] for i in range(len(columns)) if row[i] is not None
            }
            # load image to job if has one
            for key in [BASE64IMAGE, REFERENCE_IMG, MASK_IMG]:
                if key in job and "base64" not in job[key]:
                    data = load_image(job[key], to_base64=True)
                    job[key] = data if data else IMAGE_NOT_FOUND_BASE64
            jobs.append(job)

        return jobs

    def insert_new_job(self, job_dict: dict, job_uuid="") -> bool:
        """
        Insert a new job into the HISTORY_TABLE_NAME table.

        If `job_uuid` is not provided, a new UUID will be generated automatically.

        Returns True if the insertion was successful, otherwise False.
        """
        if not job_uuid:
            job_uuid = str(uuid.uuid4())
        self.__logger.info(f"inserting a new job with {job_uuid}")

        current_epoch = get_epoch_now()
        # store image to job_dict if has one
        if (
            self.__image_output_folder
            and REFERENCE_IMG in job_dict
            and "base64" in job_dict[REFERENCE_IMG]
        ):
            ref_img_filepath = f"{self.__image_output_folder}/{current_epoch}_ref.png"
            self.__logger.info(f"saving reference image to {ref_img_filepath}")
            if save_image(job_dict[REFERENCE_IMG], ref_img_filepath):
                job_dict[REFERENCE_IMG] = ref_img_filepath
        if (
            self.__image_output_folder
            and MASK_IMG in job_dict
            and "base64" in job_dict[MASK_IMG]
        ):
            mask_img_filepath = f"{self.__image_output_folder}/{current_epoch}_mask.png"
            self.__logger.info(f"saving mask image to {mask_img_filepath}")
            if save_image(job_dict[MASK_IMG], mask_img_filepath):
                job_dict[MASK_IMG] = mask_img_filepath

        values = [job_uuid, VALUE_JOB_PENDING, datetime.datetime.now()]
        columns = [UUID, KEY_JOB_STATUS, "created_at"] + REQUIRED_KEYS + OPTIONAL_KEYS
        for column in REQUIRED_KEYS + OPTIONAL_KEYS:
            values.append(job_dict.get(column, None))

        query = f"INSERT INTO {HISTORY_TABLE_NAME} ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])})"

        acquire_lock()
        try:
            c = self.get_cursor()
            c.execute(query, tuple(values))
            self.commit()
        finally:
            release_lock()
        return True

    def update_job(self, job_dict: dict, job_uuid: str) -> bool:
        """
        Update an existing job in the HISTORY_TABLE_NAME table with the given `job_uuid`.

        Returns True if the update was successful, otherwise False.
        """
        # store image to job_dict if has one
        if (
            self.__image_output_folder
            and BASE64IMAGE in job_dict
            and "base64" in job_dict[BASE64IMAGE]
        ):
            out_img_filepath = f"{self.__image_output_folder}/{get_epoch_now()}_out.png"
            self.__logger.info(f"saving output image to {out_img_filepath}")
            if save_image(job_dict[BASE64IMAGE], out_img_filepath):
                job_dict[BASE64IMAGE] = out_img_filepath

        values = []
        columns = []
        for column in INTERNAL_KEYS + OUTPUT_ONLY_KEYS + REQUIRED_KEYS + OPTIONAL_KEYS:
            value = job_dict.get(column, None)
            if value is not None:
                columns.append(column)
                values.append(value)

        set_clause = ", ".join([f"{column}=?" for column in columns])
        # Add current timestamp to update query
        set_clause += ", updated_at=?"
        values.append(datetime.datetime.now())
        values.append(job_uuid)

        query = f"UPDATE {HISTORY_TABLE_NAME} SET {set_clause} WHERE {UUID}=?"

        acquire_lock()
        try:
            c = self.get_cursor()
            c.execute(query, tuple(values))
            self.commit()
        finally:
            release_lock()
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
        return self.delete_job(
            job_uuid=job_uuid, apikey=apikey, status=VALUE_JOB_PENDING
        )

    def delete_job(
        self, job_uuid: str = "", apikey: str = "", status: str = ""
    ) -> bool:
        if not job_uuid and not apikey:
            self.__logger.error(f"either {UUID} or {APIKEY} must be provided.")
            return False

        query = f"DELETE FROM {HISTORY_TABLE_NAME} WHERE {UUID}=?"
        if status:
            query += f" AND {KEY_JOB_STATUS}=?"
        values = []
        if job_uuid:
            values.append(job_uuid)
        elif apikey:
            values.append(apikey)
        if status:
            values.append(status)

        rows_removed = 0

        acquire_lock()
        try:
            c = self.get_cursor()
            c.execute(query, tuple(values))
            rows_removed = c.rowcount
            self.commit()
        finally:
            release_lock()

        if rows_removed == 0:
            self.__logger.info("No matching rows found.")
            return False
        self.__logger.info(f"{rows_removed} rows removed.")
        return True

    def safe_disconnect(self):
        if not self.is_connected:
            raise RuntimeError("Did you forget to connect() to the database?")
        self.commit()
        self.__connect.close()
        self.__logger.info("Disconnected from database.")
