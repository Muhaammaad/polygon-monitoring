import pymysql
import mysql.connector
from db_setup import db_url, db_user, db_pass, db_db, db_monitoring_url, db_monitoring_user, db_monitoring_pass, db_monitoring_db
import logging
logger = logging.getLogger(__name__)

# Database connection helper for BI database
def get_db_connection_bi():
    try:
        connection = pymysql.connect(host=db_url,
                                     user=db_user,
                                     password=db_pass,
                                     db=db_db,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        return connection
    except pymysql.MySQLError as e:
        logger.error(f"Error connecting to the MySQL database: {e}")
        print(f"Error connecting to the MySQL database: {e}")
        return None

# Database connection helper for BI MySQL database
def get_db_connection_bi_mysql():
    try:
        connection = mysql.connector.connect(
        host=db_url,
        database=db_db,
        user=db_user,
        password=db_pass
    )

        return connection
    except mysql.MySQLError as e:
        logger.error(f"Error connecting to the MySQL database: {e}")
        print(f"Error connecting to the MySQL database: {e}")
        return None

# Database connection helper for Monitoring database
def get_db_connection_api2():
    try:
        connection = pymysql.connect(host=db_monitoring_url,
                                     user=db_monitoring_user,
                                     password=db_monitoring_pass,
                                     db=db_monitoring_db,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        return connection
    except pymysql.MySQLError as e:
        logger.error(f"Error connecting to the MySQL database: {e}")
        print(f"Error connecting to the MySQL database: {e}")
        return None
    
