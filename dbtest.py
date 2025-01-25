from pymongo import MongoClient

# Connect to the MongoDB server
client = MongoClient('mongodb://localhost:27017')

# List all database names
databases = client.list_database_names()

# Print the list of databases
p