# Import necessary modules
from pymongo import MongoClient  # MongoDB client to interact with the database
from werkzeug.security import generate_password_hash, check_password_hash  # Functions to hash passwords and check hashed passwords
from flask_login import UserMixin  # Mixin class for user objects in Flask-Login

# Initialize a connection to MongoDB
client = MongoClient('mongodb://localhost:27017/')  # Connects to the MongoDB server running on localhost at the default port 27017
db = client['smart_bin_db']  # Accesses the database named 'smart_bin_db'
users_collection = db['users']  # Accesses the 'users' collection within the database

# Define the User class, which extends the UserMixin class
class User(UserMixin):
    # Constructor for the User class
    def __init__(self, user_data):
        # Initialize user properties from the provided user data
        self.id = str(user_data['_id'])  # User's unique ID, converted to a string
        self.username = user_data['username']  # User's username
        self.password_hash = user_data['password_hash']  # Hashed password
        self.role = user_data['role']  # User's role (e.g., admin, user)

    # Method to check if a given password matches the stored password hash
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)  # Returns True if the password matches the hash

# Function to retrieve a user from the database by username
def get_user(username):
    # Find a user document in the collection by username
    user_data = users_collection.find_one({'username': username})
    if user_data:
        return User(user_data)  # If a user is found, return a User object
    return None  # Return None if no user is found

# Function to create a new user in the database
def create_user(username, password, role):
    # Generate a hashed password from the plain text password
    password_hash = generate_password_hash(password)
    # Insert a new user document into the users collection
    users_collection.insert_one({
        'username': username,  # Username field
        'password_hash': password_hash,  # Hashed password field
        'role': role  # Role field
    })
