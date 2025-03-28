#!/usr/bin/env python
"""
Setup script for Cocktail Exchange platform.
"""
import os
import subprocess
import sys
from getpass import getpass


def main():
    print("Setting up Cocktail Exchange platform...")

    # Check if Python 3.8+ is installed
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        sys.exit(1)

    # Check if pip is installed
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"])
    except subprocess.CalledProcessError:
        print("Error: pip is not installed. Please install pip first.")
        sys.exit(1)

    # # Install dependencies
    # print("Installing dependencies...")
    # subprocess.check_call(
    #     [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    # )

    # Run migrations
    print("Setting up database...")
    subprocess.check_call([sys.executable, "manage.py", "migrate"])

    # Seed data
    seed = input("Do you want to seed the database with initial data? (y/n): ")
    if seed.lower() == "y":
        subprocess.check_call([sys.executable, "manage.py", "seed_data"])

    # Create superuser
    create_admin = input("Do you want to create a superuser account? (y/n): ")
    if create_admin.lower() == "y":
        subprocess.check_call([sys.executable, "manage.py", "createsuperuser"])

    print("\nSetup complete! You can now run the server with:")
    print("python manage.py runserver")
    print("\nIn a separate terminal, you can simulate market movements with:")
    print("python manage.py simulate_market --interval 30")


if __name__ == "__main__":
    main()
