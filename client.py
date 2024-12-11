import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket
import json
import threading
from typing import Optional, Dict
from datetime import datetime


class ChatWindow(tk.Toplevel):
    def __init__(self, parent, username: str, send_callback):
        super().__init__(parent)
        self.username = username
        self.send_callback = send_callback

        # Set window title and size
        self.title(f"Chat with {username}")
        self.geometry("400x500")

        # Store window position
        self.position_set = False

        # Bind window movement
        self.bind('<Configure>', self.on_window_move)

        # Chat history
        self.chat_display = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=20)
        self.chat_display.pack(fill="both", expand=True, padx=5, pady=5)

        # Configure text tags
        self.chat_display.tag_configure('sent', foreground='blue')
        self.chat_display.tag_configure('received', foreground='green')
        self.chat_display.tag_configure('timestamp', foreground='gray')

        # Message input area
        input_frame = ttk.Frame(self)
        input_frame.pack(fill="x", padx=5, pady=5)

        self.message_entry = ttk.Entry(input_frame)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        send_btn = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_btn.pack(side="right")

        # Bind enter key
        self.message_entry.bind("<Return>", lambda e: self.send_message())

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def send_message(self):
        message = self.message_entry.get().strip()
        if message:
            self.send_callback(self.username, message)
            self.message_entry.delete(0, tk.END)

    def add_message(self, message: str, is_sent: bool = True):
        timestamp = datetime.now().strftime("%H:%M:%S")
        tag = 'sent' if is_sent else 'received'

        self.chat_display.insert(tk.END, f"\n[{timestamp}]\n", 'timestamp')
        self.chat_display.insert(tk.END, f"{'You' if is_sent else self.username}: ", tag)
        self.chat_display.insert(tk.END, f"{message}\n", tag)
        self.chat_display.see(tk.END)

        # Make sure window maintains its position when receiving messages
        if not self.position_set:
            # Center window on first message
            self.center_window()
            self.position_set = True

    def center_window(self):
        # Get parent window position and size
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()

        # Calculate center position
        x = parent_x + parent_width + 10  # Position to the right of main window
        y = parent_y

        # Set window position
        self.geometry(f"+{x}+{y}")

    def on_window_move(self, event):
        if event.widget == self:
            self.position_set = True  # User has manually positioned the window

    def on_closing(self):
        self.withdraw()  # Hide window instead of destroying


class ChatClientGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Language Chat Client")
        self.root.geometry("600x600")  # Increased width to 400

        # Socket connection
        self.client_socket: Optional[socket.socket] = None
        self.connected = False

        # Store chat windows
        self.chat_windows: Dict[str, ChatWindow] = {}

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
        self.connect_btn.grid(row=2, column=0, columnspan=4, pady=10)

        # Users List Frame
        users_frame = ttk.LabelFrame(self.root, text="Active Users")
        users_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.users_listbox = tk.Listbox(users_frame)
        self.users_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Bind double-click on user to open chat
        self.users_listbox.bind('<Double-Button-1>', self.open_chat_window)

        # Initially disable users list
        self.users_listbox.configure(state='disabled')

    def open_chat_window(self, event=None):
        selection = self.users_listbox.curselection()
        if selection:
            username = self.users_listbox.get(selection[0]).split(" ")[0]
            self.get_chat_window(username).deiconify()

    def get_chat_window(self, username: str) -> ChatWindow:
        if username not in self.chat_windows:
            self.chat_windows[username] = ChatWindow(
                self.root,
                username,
                self.send_private_message
            )
        return self.chat_windows[username]

    def send_private_message(self, recipient: str, message: str):
        if not self.connected:
            return

        message_data = {
            "type": "message",
            "content": message,
            "recipient": recipient
        }

        try:
            self.client_socket.send(json.dumps(message_data).encode())
            chat_window = self.get_chat_window(recipient)
            chat_window.add_message(message, is_sent=True)
        except:
            self.disconnect_from_server()

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

            # Send initial client info
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
            self.users_listbox.configure(state='normal')
            self.connect_btn.configure(text="Disconnect")
            messagebox.showinfo("Success", "Connected to server")

        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def disconnect_from_server(self):
        if self.client_socket:
            self.client_socket.close()
        self.connected = False
        self.users_listbox.configure(state='disabled')
        self.connect_btn.configure(text="Connect")
        self.users_listbox.delete(0, tk.END)

        # Hide all chat windows
        for window in self.chat_windows.values():
            window.withdraw()

        messagebox.showinfo("Disconnected", "Disconnected from server")

    def update_users_list(self, users):
        self.users_listbox.delete(0, tk.END)
        current_username = self.username_entry.get()
        for user in users:
            if user['username'] != current_username:
                self.users_listbox.insert(tk.END, f"{user['username']} ({user['language']})")

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
                    if message_data.get('is_private') and 'from' in message_data:
                        # Get or create chat window for sender
                        sender = message_data['from']
                        chat_window = self.get_chat_window(sender)
                        chat_window.add_message(message_data['content'], is_sent=False)
                        chat_window.deiconify()  # Show window when new message arrives
                elif message_data["type"] == "error":
                    messagebox.showerror("Error", message_data['content'])

            except:
                if self.connected:
                    self.disconnect_from_server()
                break

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    client = ChatClientGUI()
    client.run()