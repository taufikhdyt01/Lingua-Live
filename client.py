import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket
import json
import threading
from typing import Optional


class ChatClientGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Language Chat Client")
        self.root.geometry("800x600")

        # Socket connection
        self.client_socket: Optional[socket.socket] = None
        self.connected = False

        # Create and setup GUI elements
        self.setup_gui()

    def setup_gui(self):
        # Connection Frame
        connection_frame = ttk.LabelFrame(self.root, text="Connection Settings", padding=10)
        connection_frame.pack(fill="x", padx=5, pady=5)

        # Host input
        ttk.Label(connection_frame, text="Host:").grid(row=0, column=0, padx=5)
        self.host_entry = ttk.Entry(connection_frame)
        self.host_entry.insert(0, "192.168.56.1")
        self.host_entry.grid(row=0, column=1, padx=5)

        # Port input
        ttk.Label(connection_frame, text="Port:").grid(row=0, column=2, padx=5)
        self.port_entry = ttk.Entry(connection_frame)
        self.port_entry.insert(0, "5505")
        self.port_entry.grid(row=0, column=3, padx=5)

        # Username input
        ttk.Label(connection_frame, text="Username:").grid(row=1, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(connection_frame)
        self.username_entry.grid(row=1, column=1, padx=5, pady=5)

        # Language selection
        ttk.Label(connection_frame, text="Language:").grid(row=1, column=2, padx=5)
        self.language_var = tk.StringVar()
        languages = [
            ('English (UK)', 'EN-GB'),
            ('English (US)', 'EN-US'),
            ('Indonesian', 'ID'),
            ('Spanish', 'ES'),
            ('French', 'FR'),
            ('German', 'DE'),
            ('Italian', 'IT'),
            ('Portuguese (BR)', 'PT-BR'),
            ('Portuguese (PT)', 'PT-PT'),
            ('Russian', 'RU'),
            ('Chinese (Simplified)', 'ZH-HANS'),
            ('Chinese (Traditional)', 'ZH-HANT'),
            ('Japanese', 'JA'),
            ('Korean', 'KO')
        ]
        self.language_names = [lang[0] for lang in languages]
        self.language_codes = {lang[0]: lang[1] for lang in languages}
        self.language_combo = ttk.Combobox(connection_frame, values=self.language_names, textvariable=self.language_var)
        self.language_combo.set('English (US)')
        self.language_combo.grid(row=1, column=3, padx=5)

        # Connect button
        self.connect_btn = ttk.Button(connection_frame, text="Connect", command=self.connect_to_server)
        self.connect_btn.grid(row=1, column=4, padx=5)

        # Main chat area
        chat_frame = ttk.Frame(self.root)
        chat_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Users list
        users_frame = ttk.LabelFrame(chat_frame, text="Active Users", width=200)
        users_frame.pack(side="left", fill="y", padx=5)

        self.users_listbox = tk.Listbox(users_frame, width=25)
        self.users_listbox.pack(fill="both", expand=True)

        # Chat display and input area
        chat_display_frame = ttk.Frame(chat_frame)
        chat_display_frame.pack(side="left", fill="both", expand=True)

        # Chat history
        self.chat_display = scrolledtext.ScrolledText(chat_display_frame, wrap=tk.WORD, height=20)
        self.chat_display.pack(fill="both", expand=True, pady=5)

        # Message input
        input_frame = ttk.Frame(chat_display_frame)
        input_frame.pack(fill="x", pady=5)

        self.message_entry = ttk.Entry(input_frame)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.send_btn = ttk.Button(input_frame, text="Send", command=self.send_message)
        self.send_btn.pack(side="right")

        # Bind enter key to send message
        self.message_entry.bind("<Return>", lambda e: self.send_message())

        # Initially disable chat controls
        self.toggle_chat_controls(False)

    def toggle_chat_controls(self, enabled: bool):
        state = 'normal' if enabled else 'disabled'
        self.message_entry.configure(state=state)
        self.send_btn.configure(state=state)
        self.users_listbox.configure(state=state)

    def connect_to_server(self):
        if self.connected:
            self.disconnect_from_server()
            return

        host = self.host_entry.get()
        try:
            port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            return

        username = self.username_entry.get()
        if not username:
            messagebox.showerror("Error", "Username cannot be empty")
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))

            # Send initial client info with correct language code
            selected_language = self.language_var.get()
            language_code = self.language_codes[selected_language]
            client_info = {
                "username": username,
                "language": language_code
            }
            self.client_socket.send(json.dumps(client_info).encode())

            # Start receiving thread
            self.connected = True
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

            # Update GUI
            self.toggle_chat_controls(True)
            self.connect_btn.configure(text="Disconnect")
            self.chat_display.insert(tk.END, "Connected to server\n")

        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def disconnect_from_server(self):
        if self.client_socket:
            self.client_socket.close()
        self.connected = False
        self.toggle_chat_controls(False)
        self.connect_btn.configure(text="Connect")
        self.users_listbox.delete(0, tk.END)
        self.chat_display.insert(tk.END, "Disconnected from server\n")

    def send_message(self):
        if not self.connected:
            return

        message = self.message_entry.get().strip()
        if not message:
            return

        # Check if it's a private message
        selected_indices = self.users_listbox.curselection()
        message_data = {
            "type": "message",
            "content": message
        }

        if selected_indices:
            recipient = self.users_listbox.get(selected_indices[0]).split(" ")[0]  # Get username without language
            message_data["recipient"] = recipient
            self.chat_display.insert(tk.END, f"[Private to {recipient}] {message}\n")
        else:
            self.chat_display.insert(tk.END, f"[You] {message}\n")

        try:
            self.client_socket.send(json.dumps(message_data).encode())
            self.message_entry.delete(0, tk.END)
        except:
            self.disconnect_from_server()

    def receive_messages(self):
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode()
                if not message:
                    break

                message_data = json.loads(message)

                if message_data["type"] == "active_users":
                    self.update_users_list(message_data["users"])
                elif message_data["type"] == "message":
                    prefix = f"[Private from {message_data['from']}]" if message_data.get(
                        'is_private') else f"[{message_data['username']}]"
                    self.chat_display.insert(tk.END, f"{prefix} {message_data['content']}\n")
                    self.chat_display.see(tk.END)
                elif message_data["type"] == "error":
                    self.chat_display.insert(tk.END, f"Error: {message_data['content']}\n")
                    self.chat_display.see(tk.END)

            except:
                if self.connected:
                    self.disconnect_from_server()
                break

    def update_users_list(self, users):
        self.users_listbox.delete(0, tk.END)
        current_username = self.username_entry.get()
        for user in users:
            # Hanya tampilkan user lain, bukan diri sendiri
            if user['username'] != current_username:
                self.users_listbox.insert(tk.END, f"{user['username']} ({user['language']})")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    client = ChatClientGUI()
    client.run()