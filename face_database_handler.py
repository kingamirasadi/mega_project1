from pymongo import MongoClient
from datetime import datetime

class FaceDatabaseHandler:
    def __init__(self, db_uri, db_name, collection_name):

        self.client = MongoClient(db_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_face(self, name, image_path, timestamp=None):

        if timestamp is None:
            timestamp = datetime.now()

        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        face_data = {
            "name": name,
            "image": image_data,
            "timestamp": timestamp
        }

        self.collection.insert_one(face_data)

    def close(self):

        self.client.close()