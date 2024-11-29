import socket
import threading
import json
import sys
from typing import List, Dict


class ChatClient:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.active_users = []
        self.current_recipient = None
        self.username = None
        self.running = True

    def connect_to_server(self, host: str = 'localhost', port: int = 5500):
        """Connect to chat server"""
        try:
            self.socket.connect((host, port))
            return True
        except Exception as e:
            print(f"Could not connect to server: {str(e)}")
            return False

    def login(self):
        """Handle user login"""
        self.username = input("Enter your username: ")
        print("\nAvailable languages:")
        languages = ["EN", "DE", "FR", "ES", "IT", "NL", "PL", "PT", "RU", "JA", "ZH", "KO", "ID", "TR", "AR", "TH"]
        for i, lang in enumerate(languages, 1):
            print(f"{i}. {lang}")

        while True:
            try:
                choice = int(input("\nSelect your preferred language (1-16): "))
                if 1 <= choice <= len(languages):
                    language = languages[choice - 1]
                    break
                print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")

        # Send login info to server
        user_info = {
            'type': 'login',
            'username': self.username,
            'language': language
        }
        self.socket.send(json.dumps(user_info).encode())

    def display_menu(self):
        """Display chat menu"""
        print("\n=== Chat Menu ===")
        print("1. Show active users")
        print("2. Select user to chat with")
        print("3. Exit")
        if self.current_recipient:
            print(f"\nCurrently chatting with: {self.current_recipient}")
        print("\nEnter message directly to chat")
        print("Enter /menu to show this menu again")

    def show_active_users(self):
        """Display list of active users"""
        print("\n=== Active Users ===")
        for i, user in enumerate(self.active_users, 1):
            print(f"{i}. {user['username']} ({user['language']})")

    def select_user(self):
        """Select user to chat with"""
        self.show_active_users()
        while True:
            try:
                choice = int(input("\nSelect user number (0 to cancel): "))
                if choice == 0:
                    self.current_recipient = None
                    print("Returned to broadcast mode")
                    break
                if 1 <= choice <= len(self.active_users):
                    selected_user = self.active_users[choice - 1]
                    if selected_user['username'] == self.username:
                        print("You cannot chat with yourself.")
                        continue
                    self.current_recipient = selected_user['username']
                    print(f"Now chatting with {self.current_recipient}")
                    break
                print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")

    def handle_user_input(self):
        """Handle user input for messages and commands"""
        self.display_menu()

        while self.running:
            try:
                message = input()

                if message.lower() == '/menu':
                    self.display_menu()
                    continue

                if message == '1':
                    self.show_active_users()
                    continue

                if message == '2':
                    self.select_user()
                    continue

                if message == '3':
                    self.running = False
                    self.socket.close()
                    print("Goodbye!")
                    sys.exit()

                if message.strip():
                    message_data = {
                        'type': 'message',
                        'content': message
                    }
                    if self.current_recipient:
                        message_data['recipient'] = self.current_recipient

                    self.socket.send(json.dumps(message_data).encode())

            except (EOFError, KeyboardInterrupt):
                self.running = False
                self.socket.close()
                print("\nGoodbye!")
                sys.exit()

    def receive_messages(self):
        """Receive and display messages from server"""
        while self.running:
            try:
                message = self.socket.recv(1024).decode()
                if not message:
                    break

                message_data = json.loads(message)

                if message_data['type'] == 'active_users':
                    self.active_users = message_data['users']
                    continue

                if message_data['type'] == 'error':
                    print(f"\nError: {message_data['content']}")
                    continue

                if message_data['type'] == 'message':
                    if 'is_private' in message_data:
                        print(f"\n[Private] {message_data['from']}: {message_data['content']}")
                    else:
                        print(f"\n{message_data['username']}: {message_data['content']}")

            except:
                print("\nLost connection to server")
                self.running = False
                break

    def start(self):
        """Start the chat client"""
        if not self.connect_to_server():
            return

        self.login()

        # Start receiving messages in a separate thread
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

        # Handle user input in the main thread
        self.handle_user_input()


if __name__ == "__main__":
    client = ChatClient()
    client.start()