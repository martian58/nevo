import os
import subprocess
import sys
import requests
import curses
from threading import Thread
from time import sleep

# Flask server URL
BASE_URL = "http://127.0.0.1:5000"

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
            print(f"The '{package}' module is not installed. Installing now...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"Successfully installed the '{package}' module.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install the '{package}' module: {e}")


def get_messages():
    """Retrieve all messages from the chat server."""
    url = f"{BASE_URL}/messages"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("messages", [])
        else:
            return [{"username": "Error", "message": response.json().get('message', 'Unknown error')}]
    except requests.exceptions.RequestException as e:
        return [{"username": "Error", "message": str(e)}]


def send_message(username, message):
    """Send a message to the chat server."""
    url = f"{BASE_URL}/send"
    payload = {"username": username, "message": message}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            return response.json().get('message', 'Unknown error occurred')
    except requests.exceptions.RequestException as e:
        return str(e)
    return "Message sent successfully!"


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
            return response.cookies.get('session_token'), "Login successful!"
        else:
            return None, response.json().get('message', 'Unknown error occurred')
    except requests.exceptions.RequestException as e:
        return None, f"Error: {str(e)}"


def curses_main(stdscr):
    """Main curses application."""
    curses.curs_set(1)
    stdscr.clear()

    # Chat window dimensions
    height, width = stdscr.getmaxyx()
    message_win_height = height - 3
    input_win_height = 3

    chat_win = curses.newwin(message_win_height, width, 0, 0)
    input_win = curses.newwin(input_win_height, width, message_win_height, 0)

    chat_win.scrollok(True)
    input_win.keypad(True)

    username = None
    session_token = None

    def update_chat():
        """Update the chat messages in the chat window."""
        while True:
            messages = get_messages()
            chat_win.clear()
            for msg in messages[-message_win_height:]:
                chat_win.addstr(f"{msg['username']}: {msg['message']}\n")
            chat_win.refresh()
            sleep(1)

    # Start thread for updating chat
    chat_thread = Thread(target=update_chat, daemon=True)
    chat_thread.start()

    while True:
        input_win.clear()
        input_win.addstr("Type /help for commands. Enter message: ")
        input_win.refresh()

        curses.echo()
        user_input = input_win.getstr().decode('utf-8').strip()
        curses.noecho()

        if user_input == "/help":
            chat_win.addstr("\n/help - Show this help message\n/register - Register a new account\n/login - Log in\n")
            chat_win.addstr("/view - View all chat messages\nAny other input will be sent as a message.\n")
        elif user_input.startswith("/register"):
            chat_win.addstr("\nRegistering new user...\n")
            input_win.addstr("Enter username: ")
            input_win.refresh()
            username = input_win.getstr().decode('utf-8').strip()
            input_win.addstr("Enter password: ")
            input_win.refresh()
            password = input_win.getstr().decode('utf-8').strip()
            result = register(username, password)
            chat_win.addstr(f"\n{result}\n")
        elif user_input.startswith("/login"):
            chat_win.addstr("\nLogging in...\n")
            input_win.addstr("Enter username: ")
            input_win.refresh()
            username = input_win.getstr().decode('utf-8').strip()
            input_win.addstr("Enter password: ")
            input_win.refresh()
            password = input_win.getstr().decode('utf-8').strip()
            session_token, message = login(username, password)
            chat_win.addstr(f"\n{message}\n")
        elif user_input == "/view":
            messages = get_messages()
            chat_win.addstr("\nChat messages:\n")
            for msg in messages:
                chat_win.addstr(f"{msg['username']}: {msg['message']}\n")
        elif username is None:
            chat_win.addstr("\nPlease log in or register before sending messages.\n")
        else:
            result = send_message(username, user_input)
            chat_win.addstr(f"\n{result}\n")

        chat_win.refresh()


if __name__ == "__main__":
    print(f"Detected Operating System: {detect_os()}")
    check_and_install_dependencies(dependencies)
    curses.wrapper(curses_main)
