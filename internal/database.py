from dotenv import dotenv_values
from pymongo import MongoClient
from pymongo.database import Database


class BettingDatabase:
    client: MongoClient
    database: Database

    def connect(self):
        config = dotenv_values(".env")

        self.client = MongoClient(config["DB_URI"])
        self.database = self.client[config["DB_NAME"]]
        print("Connected to the MongoDB database!")

    def shutdown(self):
        self.client.close()


database = BettingDatabase()
database.connect()
database = database.database
