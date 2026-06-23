import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
uri=os.getenv("mongo_URI")

client=MongoClient(uri)

db=client["school"]

students = db["students"]

print("Database created successfully")
# try:
#     client.admin.command('ping')
#     print("database has connected")
# except Exception as e:
#     print (e)    
    
new_student ={
    "name": "john doe",
    "age": 20,
    "grade": "A",

}
results = students.insert_one(new_student)
print(f"created student id id {results.inserted_id}")
