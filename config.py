import os
from typing import List

# Bot & API details
API_ID = int(os.environ.get("API_ID", 18466881))
API_HASH = os.environ.get("API_HASH", "8c8ca14ad8e416ce4e6ea717db7ec6af")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8483246378:AAFACrQv9a9rSfLjejyIAClK2b8iokIeARo")

# Owner / Admin
ADMIN = int(os.environ.get("ADMIN", 5565120414))  

# Start Pictures (multiple supported)
PICS = (os.environ.get("START_PIC", "https://envs.sh/dpP.jpg https://envs.sh/dpq.jpg https://envs.sh/dp0.jpg")).split()

# Channels
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -1002731391701))
AUTH_CHANNELS = list(map(int, os.environ.get("AUTH_CHANNELS", "-1002807337111 -1002269814881").split()))  

# Database
DB_URI = os.environ.get("DB_URI", "mongodb+srv://nikhilsahu7j:dTQKfvo0jABOYKOu@cluster0.n2csgvi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DB_NAME", "Cluster0")

# Features
NEW_REQ_MODE = os.environ.get("NEW_REQ_MODE", "False").lower() == "true"
IS_FSUB = os.environ.get("IS_FSUB", "True").lower() == "true"   # Force Subscribe enabled
