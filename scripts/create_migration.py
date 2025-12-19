# scripts/create_migration.py
"""Helper script to create Alembic migrations."""
import sys
import os
import subprocess

if __name__ == "__main__":
    message = input("Enter migration message: ")
    if message:
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", message])
    else:
        print("Migration message is required!")

