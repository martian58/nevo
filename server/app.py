from flask import Flask, request, jsonify, make_response
import uuid
import sqlite3
import bcrypt

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('chat_app.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQIUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQIUE NOT NULL,
            sender TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            username TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# A list to store chat messages
chat_messages = []

@app.route('/')
def index():
    response = {
        "status": "success",
        "message": "Welcome to Nevo Chat!",
    }
    return jsonify(response)

@app.route('/register', methods=["POST"])
def register():
    data = request.get_json()

    # Validate input
    if 'username' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "Missing 'username' or 'password'"}), 400

    username = data['username']
    password = data['password']

    try:
        conn = sqlite3.connect('chat_app.db')
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            return jsonify({"status": "error", "message": "Username already exists"}), 409

        # Hash the password using bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert the new user into the database
        cursor.execute('INSERT INTO users (user_id, username, password) VALUES (?, ?, ?)', (str(uuid.uuid4()), username, password_hash))
        conn.commit()
        return jsonify({"status": "success", "message": "Registration successful!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/login', methods=["POST"])
def login():
    data = request.get_json()

    # Validate input
    if 'username' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "Missing 'username' or 'password'"}), 400

    username = data['username']
    password = data['password']

    try:
        conn = sqlite3.connect('chat_app.db')
        cursor = conn.cursor()

        # Fetch the user record
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        user_record = cursor.fetchone()

        if not user_record:
            return jsonify({"status": "error", "message": "Invalid username or password"}), 401

        stored_password_hash = user_record[0]

        # Verify the password
        if not bcrypt.checkpw(password.encode('utf-8'), stored_password_hash):
            return jsonify({"status": "error", "message": "Invalid username or password"}), 401

        # Generate a session token
        session_token = str(uuid.uuid4())
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        user_id = cursor.fetchone()[0]
        # Save the session token
        cursor.execute('INSERT INTO sessions (session_token, user_id, username) VALUES (?, ?, ?)', (session_token, user_id, username))
        conn.commit()

        # Set the session token as a secure HTTP-only cookie
        response = make_response(jsonify({"status": "success", "message": "Login successful!"}))
        response.set_cookie('session_token', session_token, httponly=True, secure=False)  # Set secure=True in production
        return response
    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500
    finally:
        conn.close()


@app.route('/logout', methods=["POST"])
def logout():
    data = request.get_json()

    # Validate input
    if 'username' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "Missing 'username' or 'password'"}), 400

    username = data['username']
    password = data['password']

    try:
        conn = sqlite3.connect('chat_app.db')
        cursor = conn.cursor()

        # Fetch the user record
        cursor.execute('SELECT session_token FROM users WHERE username = ?', (username,))
        token = cursor.fetchone()

        if not token:
            return jsonify({"status": "error", "message": "Invalid username or password"}), 401


        cursor.execute('DELETE FROM sessions WHERE username = ?', (username,))
        conn.commit()

        # Set the session token as a secure HTTP-only cookie
        response = make_response(jsonify({"status": "success", "message": "Logged out!"}))
        return response
    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500
    finally:
        conn.close()


# Endpoint to send a message
@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()  # Parse JSON data from the client
    if 'username' not in data or 'message' not in data or data['message'] == "":
        return jsonify({"status": "error", "message": "Missing 'username' or 'message' field."}), 400
    
    # Save the message
    chat_messages.append({"message_id": str(uuid.uuid4()), "username": data['username'], "message": data['message']})
    try:
        conn = sqlite3.connect('chat_app.db')
        cursor = conn.cursor()

        # Insert the new user into the database
        cursor.execute('INSERT INTO messages (message_id, sender, content) VALUES (?, ?, ?)', (str(uuid.uuid4()), data['username'], data['message']))
        conn.commit()
    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500
    finally:
        conn.close()

    return jsonify({"status": "success", "message": "Message sent!"})




# Endpoint to retrieve all messages
@app.route('/messages', methods=['GET'])
def get_messages():
    try:
        conn = sqlite3.connect('chat_app.db')
        cursor = conn.cursor()

        # Fetch all messages from the database
        cursor.execute('SELECT message_id, sender, content FROM messages ORDER BY rowid ASC')
        rows = cursor.fetchall()

        # Transform rows into a list of dictionaries
        messages = [{"message_id": row[0], "username": row[1], "message": row[2]} for row in rows]
    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500
    finally:
        conn.close()

    return jsonify({"status": "success", "messages": messages})

if __name__ == "__main__":
    app.run(debug=True)
