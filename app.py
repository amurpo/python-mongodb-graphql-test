from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from flask_graphql import GraphQLView
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import os
import ssl


import pymongo
app = Flask(__name__)

# Load environment variables from .env
load_dotenv()

# Get MongoDB URI from environment variables or use a default value
mongo_uri = os.getenv("MONGO_URI")

if not mongo_uri:
    raise ValueError("MONGO_URI is not set in the .env file")

# Configure SSL context globally
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Apply SSL context globally to PyMongo
pymongo.ssl_context = ssl_context

# Create the MongoClient without specifying SSL
client = MongoClient(mongo_uri)
db = client.get_database()
users_collection = db['users']

@app.route('/', methods=['GET'])
def index():
    users = list(users_collection.find({}))
    return render_template('index.html', users=users)

@app.route('/create-user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'GET':
        return render_template('create_user.html')
    elif request.method == 'POST':
        # Get user data from the form.
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if username or email already exist in the database.
        existing_user = users_collection.find_one({"$or": [{"username": username}, {"email": email}]})

        if existing_user:
            return jsonify({"error": "Username or email already exists"})

        # Hash the password before storing it in the database.
        hashed_password = generate_password_hash(password)

        # Create a new user document.
        new_user = {
            "username": username,
            "email": email,
            "password": hashed_password
        }

        # Insert the new user into the database.
        users_collection.insert_one(new_user)

        # Return a JSON response indicating success.
        return jsonify({"success": True})

@app.route('/update/<user_id>', methods=['GET', 'POST'])
def update_user_form(user_id):
    if request.method == 'GET':
        # Get the user by ID from the database.
        user = users_collection.find_one({'_id': user_id})

        # Render the update user form with the user data.
        return render_template('update_user.html', user=user)
    else:
        # Get the updated user data from the request form.
        user_data = {
            "username": request.form.get('username'),
            "email": request.form.get('email'),
        }

        # Update the user's information in the database.
        users_collection.update_one({'_id': user_id}, {'$set': user_data})

        # Return a JSON response indicating that the update was successful.
        return jsonify({"success": True})

# New route for updating a user's password:

@app.route('/update-password', methods=['POST'])
def update_user_password():
    # Get the user ID from the request form.
    user_id = request.form.get('id')

    # Get the new password from the request form.
    new_password = request.form.get('new_password')

    # Hash the new password before storing it in the database.
    hashed_password = generate_password_hash(new_password)

    # Update the user's password in the database.
    users_collection.update_one({'_id': user_id}, {'$set': {'password': hashed_password}})

    # Return a JSON response indicating that the update was successful.
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)
