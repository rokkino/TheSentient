"""
Script to manually create the bots table
Run this if the table doesn't exist: python create_bots_table.py
"""
from models.user import init_db

if __name__ == "__main__":
    print("Initializing database and creating bots table...")
    init_db()
    print("Done! The bots table should now exist.")


