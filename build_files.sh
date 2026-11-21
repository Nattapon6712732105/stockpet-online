#!/bin/bash
# Install dependencies with --break-system-packages
python3 -m pip install -r requirements.txt --break-system-packages

# Migrate database
python3 petfood_warehouse/manage.py migrate --noinput

# Seed demo data
python3 petfood_warehouse/manage.py seed_demo

# Collect static files
python3 petfood_warehouse/manage.py collectstatic --noinput --clear
