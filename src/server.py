from textual_serve.server import Server
import os

# Get absolute path to main.py
main_path = os.path.join(os.getcwd(), "src", "main.py")
server = Server(f"python {main_path}")
server.serve(debug=True)