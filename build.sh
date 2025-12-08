#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Create media directories for uploads (ephemeral on Render free tier)
mkdir -p media/products
mkdir -p media/profile_pictures
mkdir -p media/business_permits
