# Copyright (c) 2025 Telegram:- @llFenixxll <llFenixxll>
# Location: Patna, Bihar 
#
# All rights reserved.
#
# This code is the intellectual property of @llFenixxll.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Contact for permissions:
# Contact: https://t.me/llFenixxll

from pymongo import MongoClient, TEXT
import certifi
from fenix_baby.config import MONGO_URI, MONGO_DB_NAME

# Initialize Connection (Optimized for 24/7 VPS)
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set. Please configure it.")

# Production-grade connection pooling
client_kwargs = {
    "minPoolSize": 10,
    "maxPoolSize": 100,
    "connectTimeoutMS": 10000,
    "socketTimeoutMS": None,
    "waitQueueTimeoutMS": 5000,
    "retryWrites": True
}

if "mongodb+srv://" in MONGO_URI:
    mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), **client_kwargs)
else:
    mongo_client = MongoClient(MONGO_URI, **client_kwargs)

db = mongo_client[MONGO_DB_NAME]

# --- DEFINING COLLECTIONS ---
users_collection = db["users"]
groups_collection = db["groups"]
sudoers_collection = db["sudoers"]
chatbot_collection = db["chatbot"]
riddles_collection = db["riddles"]

# --- INDEXES (Critical for Latency) ---
def setup_indexes():
    try:
        users_collection.create_index("user_id", unique=True)
        users_collection.create_index([("balance", -1)])
        groups_collection.create_index("chat_id", unique=True)
        chatbot_collection.create_index("chat_id", unique=True)
    except: pass

setup_indexes()

