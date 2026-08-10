import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hyperledger_fabric.settings")
django.setup()
