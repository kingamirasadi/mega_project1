from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

class AuthenticationDB:
    def __init__(self, db_uri='mongodb://localhost:27017/', db_name='authentication_db', collection_name='users'):
        self.client = MongoClient(db_uri)  # Connect to the MongoDB client
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def create_user(self, username, password, email=None):
        """Create a new user with a hashed password"""
        password_hash = generate_password_hash(password)
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
        }
        result = self.collection.insert_one(user_data)  # Insert the user into the collection
        return result.inserted_id

    def get_user_by_username(self, username):
        """Get user data by username"""
        user = self.collection.find_one({'username': username})
        return user

    def get_user_by_email(self, email):
        """Get user data by email"""
        user = self.collection.find_one({'email': email})
        return user

    def get_user_by_id(self, user_id):
        """Get user data by _id"""
        try:
            object_id = ObjectId(user_id)  # Convert the user_id string to ObjectId
            user = self.collection.find_one({'_id': object_id})
            return user
        except Exception as e:
            print(f"Error: {e}")
            return None
