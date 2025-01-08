import mysql.connector
import os
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from jinja2 import Environment, FileSystemLoader
from urllib.parse import parse_qs
from dotenv import load_dotenv
import secrets

# Load environment variables
load_dotenv()
env = Environment(loader=FileSystemLoader('G:/Projects/aapli mess/templates'))

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Set up Jinja2 for HTML templating
env = Environment(loader=FileSystemLoader('templates'))  # Store HTML templates in a "templates" folder

# Sessions dictionary to handle user sessions
sessions = {}

def connect_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def signup_user(form_data):
    username = form_data['username']
    password = form_data['password']
    mob = form_data['mob']
    usertype = form_data['usertype']
    
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("INSERT INTO login (username, password, usertype, mob) VALUES (%s, %s, %s, %s)", 
                   (username, password, usertype, mob))
    db.commit()

    if usertype == 'customer':
        name = form_data['name']
        cursor.execute("INSERT INTO customer (cname, username, mob) VALUES (%s, %s, %s)", 
                       (name, username, mob))
    elif usertype == 'mess':
        mess_name = form_data['mess_name']
        cursor.execute("INSERT INTO mess (mess_name, username, mob) VALUES (%s, %s, %s)", 
                       (mess_name, username, mob))
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {username}_menu (fid INT AUTO_INCREMENT PRIMARY KEY, fooditem VARCHAR(100), price DECIMAL(5,2))")

    db.commit()
    cursor.close()
    db.close()

def login_user(form_data):
    username = form_data['username']
    password = form_data['password']

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT usertype FROM login WHERE username=%s AND password=%s", (username, password))
    result = cursor.fetchone()
    cursor.close()
    db.close()
    
    return result[0] if result else None

def get_mess_menu(username):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT fid, fooditem, price FROM {username}_menu")
    menu_data = cursor.fetchall()
    cursor.close()
    db.close()
    return menu_data

def add_menu_item(form_data, username):
    fooditem = form_data['food_item']
    price = form_data['price']
    
    db = connect_db()
    cursor = db.cursor()
    cursor.execute(f"INSERT INTO {username}_menu (fooditem, price) VALUES (%s, %s)", (fooditem, price))
    db.commit()
    cursor.close()
    db.close()

def delete_menu_item(username, fid):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute(f"DELETE FROM `{username}_menu` WHERE fid = %s", (fid,))
    db.commit()
    cursor.close()
    db.close()

def get_all_mess_names():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT mess_name FROM mess")
    mess_names = cursor.fetchall()
    cursor.close()
    db.close()
    return [name[0] for name in mess_names]

class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    
    def set_session(self, username):
        session_id = secrets.token_hex(16)
        sessions[session_id] = username
        return session_id

    def get_session_username(self):
        if "Cookie" in self.headers:
            cookie = SimpleCookie(self.headers["Cookie"])
            session_id = cookie.get("session_id").value
            return sessions.get(session_id)
        return None

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('index.html', 'r') as file:
                self.wfile.write(file.read().encode())

        elif self.path == '/login.html':
            self.send_html('login.html')

        elif self.path == '/signup_customer.html':
            self.send_html('signup_customer.html')

        elif self.path == '/signup_mess.html':
            self.send_html('signup_mess.html')

        elif self.path == '/update_menu.html':
            self.send_html('update_menu.html')

    def send_html(self, filename, context=None):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        template = filename
        self.wfile.write(template.render(context or {}).encode())

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(length)
        form_data = {k: v[0] for k, v in parse_qs(post_data.decode()).items()}
        
        if self.path == "/signup":
            signup_user(form_data)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Signup successful!")

        elif self.path == "/login":
            usertype = login_user(form_data)
            if usertype:
                username = form_data['username']
                session_id = self.set_session(username)
                self.send_response(200)
                self.send_header("Set-Cookie", f"session_id={session_id}; HttpOnly")
                self.end_headers()
                if usertype == 'mess':
                    self.show_mess_menu(username)
                elif usertype == 'customer':
                    self.show_all_messes()
            else:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Invalid credentials!")

        elif self.path == "/update_menu":
            username = self.get_session_username()
            if username:
                add_menu_item(form_data, username)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Item added successfully!")

        elif self.path == "/delete_item":
            username = self.get_session_username()
            if username:
                fid = int(form_data['item_id'])
                delete_menu_item(username, fid)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Item deleted successfully!")

    def show_mess_menu(self, username):
        menu_data = get_mess_menu(username)
        self.send_html("mess_menu.html", {"menu": menu_data, "username": username})

    def show_all_messes(self):
        mess_names = get_all_mess_names()
        self.send_html("customer_mess_list.html", {"messes": mess_names})

def runserver():
    port = 8080
    httpd = HTTPServer(('0.0.0.0', port), MyHTTPRequestHandler)
    print(f"Server running on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    runserver()
