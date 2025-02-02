from pymongo import MongoClient

# Connect to the MongoDB server
client = MongoClient('mongodb://localhost:27017')

# Access the database and collection
my_db = client['face_recognition_db']
my_collection = my_db['recognized_faces']

# Iterate through the documents in the collection
for item in my_collection.find():
    # Access specific fields (e.g., 'name' and 'time')
    name = item.get('name')  # Use .get() to safely access the field
    time = item.get('timestamp')  # Use .get() to avoid KeyError if the field is missing

    # Print the values
    print(f"Name: {name}, Time: {time}")