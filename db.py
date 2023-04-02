import mariadb
import config
from datetime import datetime
from utils import voda_logger

# import logging
# logger = logging.getLogger(__name__)

# logging.basicConfig(
#     format="[%(levelname)s] %(asctime)s %(message)s",
#     level=logging.DEBUG,
#     datefmt="%Y-%m-%d %H:%M:%S :",
# )


class DatabaseInstance:
    def dbConnect(
        self,
        user=config.MARIADB_USERNAME,
        password=config.MARIADB_PASSWORD,
        host=config.MARIADB_HOST,
        port=config.MARIADB_PORT,
        database=config.MARIADB_DATABASE,
    ):
        try:
            self.db_conn = mariadb.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database=database,
            )
            # logging.info(f"✅ Connected to MariaDB host: {config.MARIADB_HOST}")

        except mariadb.Error as e:
            # logging.error(f"❌ Error connecting to MariaDB on {config.MARIADB_HOST}: {e}")
            voda_logger.critical(
                f"❌ Error connecting to MariaDB on {config.MARIADB_HOST}: {e}"
            )
            return False, None

        self.db_cur = self.db_conn.cursor()
        return True, self.db_cur

    def dbTablePrep(self):
        self.db_cur.execute(
            f"""
                CREATE TABLE IF NOT EXISTS sms (
                    sms_hash varchar(64) not null, 
                    timestamp timestamp not null, 
                    sender varchar(15), 
                    content varchar(160), 
                    sms_index int,
                    primary key(sms_hash)
                );
            """
        )
        return True

    def storeSms(self, smsDict):
        try:
            self.db_cur.execute(
                "INSERT INTO sms(sms_hash, timestamp, sender, content, sms_index) VALUES (%s, %s, %s, %s, %s);",
                (
                    smsDict["sms_hash"],
                    smsDict["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    smsDict["sender"],
                    smsDict["content"],
                    smsDict["sms_index"],
                ),
            )
            self.db_conn.commit()
            return True
        except mariadb.IntegrityError as e:
            voda_logger.warning(f"{smsDict['sms_hash']} is already in the database")
            self.db_conn.commit()
            return False
