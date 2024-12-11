import socket
import threading
import json
import deepl
from typing import Dict


class ChatServer:
    def __init__(self, host: str = '192.168.56.1', port: int = 5505):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        # Dictionary to store client connections and their details
        self.clients: Dict[socket.socket, dict] = {}
        # DeepL translator
        self.translator = deepl.Translator("a31fd91c-80c7-42d1-9ec8-f45e98f22eff:fx")

        print(f"Server started on {host}:{port}")

    def send_private_message(self, sender_socket: socket.socket, recipient_username: str, message: dict):
        """Send private message to specific user"""
        for client_socket, client_info in self.clients.items():
            if client_info['username'] == recipient_username:
                try:
                    # Translate message based on recipient's preferred language
                    translated_msg = message.copy()
                    if message['type'] == 'message':
                        translated_text = self.translator.translate_text(
                            message['content'],
                            target_lang=client_info['language']
                        )
                        translated_msg['content'] = str(translated_text)
                        translated_msg['is_private'] = True
                        translated_msg['from'] = self.clients[sender_socket]['username']

                    client_socket.send(json.dumps(translated_msg).encode())
                    return True
                except:
                    self.remove_client(client_socket)
                    return False
        return False

    def broadcast_active_users(self):
        """Broadcast list of active users to all clients"""
        active_users = {
            'type': 'active_users',
            'users': [{'username': info['username'], 'language': info['language']}
                      for info in self.clients.values()]
        }
        for client_socket in self.clients:
            try:
                client_socket.send(json.dumps(active_users).encode())
            except:
                self.remove_client(client_socket)

    def handle_client(self, client_socket: socket.socket):
        """Handle individual client connection"""
        try:
            # Get initial client info (username and preferred language)
            client_info = client_socket.recv(1024).decode()
            client_info = json.loads(client_info)

            # Store client information
            self.clients[client_socket] = {
                'username': client_info['username'],
                'language': client_info['language']
            }

            # Broadcast active users list
            self.broadcast_active_users()

            while True:
                message = client_socket.recv(1024).decode()
                if not message:
                    break

                message_data = json.loads(message)
                if message_data['type'] == 'message':
                    message_data['username'] = self.clients[client_socket]['username']
                    if 'recipient' in message_data:
                        # Handle private message
                        success = self.send_private_message(
                            client_socket,
                            message_data['recipient'],
                            message_data
                        )
                        if not success:
                            error_msg = {
                                'type': 'error',
                                'content': f"User {message_data['recipient']} not found or offline"
                            }
                            client_socket.send(json.dumps(error_msg).encode())

        except:
            self.remove_client(client_socket)

    def remove_client(self, client_socket: socket.socket):
        """Remove client and broadcast updated active users list"""
        if client_socket in self.clients:
            del self.clients[client_socket]
            client_socket.close()
            self.broadcast_active_users()

    def start(self):
        """Start the chat server"""
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"New connection from {address}")

                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            self.server_socket.close()


if __name__ == "__main__":
    server = ChatServer()
    server.start()