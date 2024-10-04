from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import psycopg2 
import joblib
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scr.demo import make_prediction

model_path = r'C:\Users\Sufrimiento\Documents\UADE\2024\Tesis - Proyecto Final de Ingeniería\Algoritmo de ML - Repo\PFI-Tesis-2024\models\decision_tree_model.pkl'

dtc = joblib.load(model_path)


app = Flask(__name__)

CORS(app)

# Connect to PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(database="nureon", user="postgres", 
                            password="1307Juanma", host="localhost", port="5432")
    return conn

@app.route("/testConnection", methods=["GET"])
def test_connection():
    conn = get_db_connection()
    if conn is not None:
        return "Connection successful!", 200
    else:
        return "Connection failed.", 500


@app.route("/getUserByUsername/<username>", methods=["GET"])
def getUserByUsername(username):
    conn= get_db_connection()
    cur = conn.cursor() 

    cur.execute("SELECT * FROM users WHERE username=%s;", (username,))
    user = cur.fetchall()
    cur.close()
    conn.close()
    return make_response(jsonify(usuarios=user), 200)

#create endpoint
@app.route("/createUser", methods=["POST"])
def create_user():
    # Get data from the request
    data = request.get_json()
    
    # Extract fields
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    birth_date = data.get('birthDate')
    gender = data.get('gender')
    user_type = data.get('userType')
    
    # Connect to the database
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Insert the new user into the database
    cur.execute("""
        INSERT INTO users (username, email, pass, birthdate, gender, usertype)
        VALUES (%s, %s, %s, %s, %s, %s);
    """, (username, email, password, birth_date, gender, user_type))
    
    conn.commit()
    
    # Fetch the inserted user to return it
    cur.execute("SELECT * FROM users WHERE username = %s;", (username,))
    user = cur.fetchone()
    
    cur.close()
    conn.close()
    
    # Return the inserted user as JSON
    return make_response(jsonify(user=user), 201)

@app.route("/loginUser", methods=["POST"])
def loginUser():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT pass FROM users WHERE username = %s;", (username,))
    user = cur.fetchone()

    if user is None:
        return make_response(jsonify(message="User not found"), 404)
    
    cur.close()
    conn.close()

    if password == user[0]:
        return make_response(jsonify(message="Login successful"), 200)
    else:
        return make_response(jsonify(message="Invalid password"), 401)

#update endpoint
@app.route("/updateUser", methods=["PUT"])
def update_user():
    data = request.get_json()
    user_id = data.get('id')  # Get the user ID from the request
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Connect to the database
    conn = get_db_connection()
    cur = conn.cursor()

    # Update user information in the database
    cur.execute("""
        UPDATE users
        SET username = %s, email = %s, pass = %s
        WHERE id = %s;
    """, (username, email, password, user_id))

    conn.commit()
    cur.close()
    conn.close()

    return make_response(jsonify(message="User updated successfully"), 200)

def make_prediction(user_answers):
    # Convert the user_answers dictionary to a DataFrame
    input_data = pd.DataFrame([user_answers])
    
    # Ensure the DataFrame has the same columns as the model expects
    # If you need to preprocess it further, do so here

    # Make predictions
    prediction = dtc.predict(input_data)
    
    return prediction[0]

@app.route('/sendAnswers', methods=['POST'])
def sendAnswers():
    try:
        # Get the JSON data from the request
        data = request.get_json()

        # Extract answers and username from the data
        answers = data.get('answers', {})
        username = data.get('username', '')

        # Log the received data
        print(f"Received answers from {username}: {answers}")

        # Validate that answers contains the expected structure
        if not answers:  # Check if answers is empty
            return jsonify(message="No answers provided"), 400

        # Make a prediction
        prediction = make_prediction(answers)
        print(f"Predicted Enneatype: {prediction}")

        # Convert prediction to a standard Python integer
        prediction_int = int(prediction)  # Convert numpy.int64 to int

        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()

        # Update the user's prediction result in the database
        cur.execute("""
            UPDATE users 
            SET enneatype = %s 
            WHERE username = %s;
        """, (int(prediction), username))

        # Commit the changes
        conn.commit()

        # Close the cursor and connection
        cur.close()
        conn.close()

        # Return the prediction as a JSON response
        return jsonify(predicted_enneatype=prediction_int), 200

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify(message="Internal Server Error"), 500

    
@app.errorhandler(Exception)
def handle_exception(e):
    print(f"Error occurred: {e}")
    return make_response(jsonify(message="Internal Server Error"), 500)

#update endpoint
if __name__ == "__main__":
    app.run(debug=True, port=5000)