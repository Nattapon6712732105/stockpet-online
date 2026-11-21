#!/bin/bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Collect static files
python3 petfood_warehouse/manage.py collectstatic --noinput --clear
