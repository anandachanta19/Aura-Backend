#!/usr/bin/env bash

# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create migrations and migrate database
python manage.py makemigrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input
