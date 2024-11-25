
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from waitress import serve
import threading
import time

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# MongoDB Connection
try:
    # Connect to MongoDB Atlas
    client = MongoClient(
        "mongodb+srv://root:abc@cluster0.v0kkc.mongodb.net/incident_management?retryWrites=true&w=majority"
    )
    db = client["incident_management"]  # Database name
    collection = db["incidents"]  # Incidents collection
    counters = db["counters"]  # Counter collection
    print("Connected to MongoDB successfully!")

    # Ensure the counter exists
    if counters.count_documents({"name": "issue_number"}) == 0:
        counters.insert_one({"name": "issue_number", "value": 0})
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# Routes
@app.route("/api/incidents", methods=["GET"])
def get_incidents():
    try:
        # Fetch all incidents from the MongoDB collection
        incidents = list(collection.find({}, {"_id": 0}))  # Exclude _id field
        return jsonify(incidents), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/incidents", methods=["POST"])
def add_incident():
    try:
        # Add a new incident document
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Get and increment the counter
        counter = counters.find_one_and_update(
            {"name": "issue_number"}, {"$inc": {"value": 1}}, return_document=True
        )
        issue_number = counter["value"]

        # Add the issue_number to the data
        data["issue_number"] = issue_number

        # Insert the document into the incidents collection
        collection.insert_one(data)
        return jsonify({"message": "Incident added successfully!", "issue_number": issue_number}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/incidents/<int:issue_number>", methods=["DELETE"])
def delete_incident(issue_number):
    try:
        # Delete an incident by its issue_number
        result = collection.delete_one({"issue_number": issue_number})
        if result.deleted_count == 0:
            return jsonify({"message": "No incident found with that issue number"}), 404
        return jsonify({"message": "Incident deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/incidents/<int:issue_number>", methods=["PUT"])
def update_incident(issue_number):
    try:
        # Update an incident by its issue_number
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Update the document in the database
        result = collection.find_one_and_update(
            {"issue_number": issue_number},
            {"$set": data},
            return_document=True
        )

        # If no document was found
        if not result:
            return jsonify({"message": "No incident found with that issue number"}), 404

        # Convert ObjectId to string to avoid JSON serialization issues
        if "_id" in result:
            result["_id"] = str(result["_id"])

        return jsonify({"message": "Incident updated successfully!", "updated_data": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Function to run Flask app with Waitress
def run_flask():
    print("Starting Flask server with Waitress on localhost:5000...")
    serve(app, host="127.0.0.1", port=5000)


# Start Flask app
if __name__ == "__main__":
    run_flask()
