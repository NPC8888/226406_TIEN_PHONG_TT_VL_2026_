#!/usr/bin/env python3
"""
Alternative script to seed plans using raw SQL queries.
"""

import os
import pymysql
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()


def get_db_config():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        return {
            "host": parsed.hostname,
            "user": parsed.username,
            "password": parsed.password or "",
            "database": parsed.path.lstrip("/"),
            "port": parsed.port or 3306,
        }

    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "intener"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
    }

def seed_plans_sql():
    """Insert plans using raw SQL queries."""

    # Database connection
    connection = pymysql.connect(
        **get_db_config(),
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:
            # Read and execute SQL file
            sql_file_path = os.path.join(os.path.dirname(__file__), 'seed_plans.sql')
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Execute the SQL
            cursor.execute(sql_content)
            connection.commit()

            print("Plans seeded successfully using SQL queries!")

            # Verify the insertion
            cursor.execute("SELECT COUNT(*) as count FROM plans")
            result = cursor.fetchone()
            print(f"Total plans in database: {result['count']}")

    except Exception as e:
        print(f"Error seeding plans: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    seed_plans_sql()
