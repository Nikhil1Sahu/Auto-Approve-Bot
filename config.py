import os
from typing import List

# Bot & API details
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Owner / Admin
ADMIN = int(os.environ.get("ADMIN", 0))  # must set in env

# Start Pictures (multiple supported, optional)
PICS = os.environ.get("START_PIC", "").split()

# Channels
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", 0))  
AUTH_CHANNELS = list(map(int, os.environ.get("AUTH_CHANNELS", "").split()))  

# Database
DB_URI = os.environ.get("DB_URI", "")
DB_NAME = os.environ.get("DB_NAME", "")

# Features
NEW_REQ_MODE = os.environ.get("NEW_REQ_MODE", "False").lower() == "true"
IS_FSUB = os.environ.get("IS_FSUB", "False").lower() == "true"   # Force Subscribe enabled
