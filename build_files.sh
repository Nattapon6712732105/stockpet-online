#!/bin/bash
# Install dependencies with --break-system-packages to comply with PEP 668 on Python 3.12+
python3 -m pip install -r requirements.txt --break-system-packages

# Collect static files
python3 petfood_warehouse/manage.py collectstatic --noinput --clear
