# db.py
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

def run_query(sql_query: str):
    """
    Executes a SQL query on the Sakila database and returns results.
    """
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,     
            user=DB_USER,          
            password=DB_PASS, 
            database=DB_NAME  
        )

        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql_query)

        if sql_query.strip().lower().startswith("select"):
            results = cursor.fetchall()
            return results
        else:
            connection.commit()
            return {"message": "Query executed successfully."}

    except Error as e:
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()