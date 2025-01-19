# In your terminal or script, run this to ensure MongoDB is accessible
from pymongo import MongoClient

try:
    client = MongoClient('mongodb://localhost:27017/')  # Change the URL if necessary
    client.admin.command('ping')  # Check if MongoDB is responsive
    print("MongoDB is connected!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")