import os
import subprocess
import sys
import requests


# Flask server URL
BASE_URL = "http://127.0.0.1:5000"

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Dependencies to install
dependencies = [
    "requests"
]


def detect_os():
    """Detect the operating system."""
    if os.name == 'nt':
        return 'Windows'
    elif os.name == 'posix':
        if sys.platform == 'darwin':
            return 'MacOS'
        else:
            return 'Linux'
    else:
        return 'Unknown'


def check_and_install_dependencies(dependencies):
    """Check if specified Python modules are installed. If not, install them."""
    for package in dependencies:
        try:
            __import__(package)
        except ModuleNotFoundError:
            print(f"{Colors.WARNING}The '{package}' module is not installed. Installing now...{Colors.ENDC}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"{Colors.OKGREEN}Successfully installed the '{package}' module.{Colors.ENDC}")
            except subprocess.CalledProcessError as e:
                print(f"{Colors.FAIL}Failed to install the '{package}' module: {e}{Colors.ENDC}")


def send_message(username, message):
    """Send a message to the chat server."""
    url = f"{BASE_URL}/send"
    payload = {"username": username, "message": message}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"{Colors.OKGREEN}Message sent successfully!{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}Error: {response.json().get('message')}{Colors.ENDC}")
    except requests.exceptions.RequestException as e:
        print(f"{Colors.FAIL}Error communicating with the server: {e}{Colors.ENDC}")


def get_messages():
    """Retrieve all messages from the chat server."""
    url = f"{BASE_URL}/messages"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            messages = response.json().get("messages", [])
            print(f"{Colors.OKCYAN}Chat Messages:{Colors.ENDC}")
            for msg in messages:
                print(f"{msg['username']}: {msg['message']}")
        else:
            print(f"{Colors.FAIL}Error: {response.json().get('message')}{Colors.ENDC}")
    except requests.exceptions.RequestException as e:
        print(f"{Colors.FAIL}Error communicating with the server: {e}{Colors.ENDC}")


def register(username, password):
    """Register a new user."""
    payload = {"username": username, "password": password}
    try:
        response = requests.post(f"{BASE_URL}/register", json=payload)
        return response.json().get('message', "Unknown error occurred")
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"


def login(username, password):
    """Log in an existing user."""
    payload = {"username": username, "password": password}
    try:
        response = requests.post(f"{BASE_URL}/login", json=payload)
        if response.status_code == 200:
            print(f"{Colors.OKGREEN}Login successful!{Colors.ENDC}")
            # Return the session token
            return response.cookies.get('session_token')
        else:
            print(f"{Colors.FAIL}Error: {response.json().get('message')}{Colors.ENDC}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"{Colors.FAIL}Error: {str(e)}{Colors.ENDC}")
        return None


def show_help():
    """Display help commands."""
    print(f"{Colors.OKCYAN}/help - Show this help message")
    print("/register - Register a new account")
    print("/login - Log in to your account")
    print("/view - View all chat messages")
    print("Any other input will be sent as a message to the chat server.")


# Main interactive loop
def main():
    print(f"{Colors.HEADER}{Colors.BOLD}Detected Operating System: {detect_os()}{Colors.ENDC}")
    check_and_install_dependencies(dependencies)
    print(f"{Colors.OKCYAN}Welcome to the Chat Client! Type /help for a list of commands.{Colors.ENDC}")

    username = None
    while True:
        user_input = input(f"{Colors.BOLD}> {Colors.ENDC}").strip()

        if user_input == "/help":
            show_help()
        elif user_input == "/register":
            username = input("Enter a username: ").strip()
            password1 = input("Enter a password: ").strip()
            password2 = input("Confirm your password: ").strip()

            if password1 != password2:
                print(f"{Colors.FAIL}Passwords do not match!{Colors.ENDC}")
                continue

            message = register(username, password1)
            print(message)
        elif user_input == "/login":
            username = input("Enter your username: ").strip()
            password = input("Enter your password: ").strip()

            session_token = login(username, password)
            if session_token:
                print(f"{Colors.OKGREEN}Logged in as {username}!{Colors.ENDC}")
        elif user_input == "/view":
            get_messages()
        elif username is None:
            print(f"{Colors.FAIL}Please log in or register before sending messages.{Colors.ENDC}")
        else:
            # Treat other inputs as chat messages
            send_message(username, user_input)


if __name__ == "__main__":
    main()
