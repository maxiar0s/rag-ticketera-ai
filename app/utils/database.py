# app/utils/database.py
import mysql.connector
import os
import time

def get_db_connection():
    """
    Intenta conectar a la base de datos MySQL con reintentos.
    Retorna el objeto de conexión.
    """
    max_retries = 5
    retry_delay = 2  # segundos

    for attempt in range(max_retries):
        try:
            connection = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST"),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                database=os.getenv("MYSQL_DB"),
                port=int(os.getenv("MYSQL_PORT", 3306))
            )
            return connection
            
        except mysql.connector.Error as err:
            print(f"Intento {attempt + 1} fallido: {err}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print("No se pudo conectar a MySQL después de varios intentos.")
                raise err