import cgi
import mysql.connector
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as parse


def connect_db():
    return mysql.connector.connect(
        
        host="mysql-37574cf7-shrikeshgaikwad-ce36.c.aivencloud.com",
        user="avnadmin",
        password="AVNS_5nwZrS0wA0tshwvjzFw", 
        database="defaultdb",
        port = "12662",
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
    query = f"SELECT * FROM {username}_menu"
    cursor.execute(query)
    menu_data = cursor.fetchall()
    cursor.close()
    db.close()
    return menu_data


def add_menu_item(form_data,username):
    
    fooditem = form_data['food_item']
    price = form_data['price']
    
    db = connect_db()
    cursor = db.cursor()
    

    cursor.execute(f"INSERT INTO {username}_menu (fooditem, price) VALUES (%s, %s)", (fooditem, price))
    db.commit()

    cursor.close()
    db.close()


def delete_menu_item(username, fooditem):
    try:
        db = connect_db()
        cursor = db.cursor()

        # Use parameterized query to safely pass fooditem as a parameter
        query = f"DELETE FROM `{username}_menu` WHERE fooditem = %s"
        cursor.execute(query, (fooditem,))  # Passing fooditem as a tuple

        db.commit()
        cursor.close()
        db.close()
        return True
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False


def get_all_mess_names():
    try:
        db = connect_db()
        cursor = db.cursor()
        query = "SELECT mess_name,username FROM mess"
        cursor.execute(query)
        mess_names = cursor.fetchall()
        cursor.close()
        db.close()
        return [name for name in mess_names]  # Return a list of mess names
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []















class MyHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('index.html', 'r') as file:
                self.wfile.write(file.read().encode())


        elif self.path == '/login.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('login.html', 'r') as file:
                self.wfile.write(file.read().encode())


        elif self.path == '/signup_customer.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('signup_customer.html', 'r') as file:
                self.wfile.write(file.read().encode())


        elif self.path == '/signup_mess.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('signup_mess.html', 'r') as file:
                self.wfile.write(file.read().encode())


        elif self.path == '/update_menu.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('update_menu.html', 'r') as file:
                self.wfile.write(file.read().encode())


        elif self.path == '/signup.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('signup.html', 'r') as file:
                self.wfile.write(file.read().encode())

        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('error.html', 'r') as file:
                self.wfile.write(file.read().encode())





                

    def do_POST(self):

        if self.path == "/signup":
            
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
            form_data = {key: form.getvalue(key) for key in form.keys()}
            signup_user(form_data)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Signup successful!")


        elif self.path == "/login":
    
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
            form_data = {key: form.getvalue(key) for key in form.keys()}

            usertype = login_user(form_data)
            
            username = form_data['username']


            if usertype:

                if usertype == 'mess':
                    menu_data = get_mess_menu(username)
            
                    if menu_data:
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                         
                        html_response = f"""
                        <html><body>
                        <h2>Menu for Mess: {username}</h2>
                        <table border="1">
                        <tr><th>Menu Item</th><th>Price</th><th>Action</th></tr>
                        """
                        for row in menu_data:
                            html_response += f"""
                            <tr>
                                <td>{row[1]}</td>
                                <td>{row[2]}</td>
                                <td>
                                    <form action="/delete_item" method="POST" style="display:inline;">
                                        <input type="hidden" name="username" value="{username}">
                                        <input type="hidden" name="fooditem" value="{row[1]}">
                                        <input type="submit" value="Delete">
                                    </form>
                                </td>
                            </tr>
                            """
                        html_response += """
                        </table>
                        <p><a href="/update_menu.html">UPDATE MENU</a></p>
                        """
                        self.wfile.write(html_response.encode())         
                        
                       
                         

                    else:
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()

                        html_response=f"""
                        <html><body>
                        <h2>NO DATA AVAILABALE</h2>
                        <p><a href="/update_menu.html">UPDATE MENU</a></p>
                        """
                        html_response += "</table></body></html>"
                        self.wfile.write(html_response.encode())





                elif usertype== 'customer':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()

        
                    mess_names = get_all_mess_names()
                    
                    html_response = f"""
                                        <html><body>
                                        <style>
                                            body {{
                                                font-family: Arial, sans-serif;
                                                display: flex;
                                                justify-content: center;
                                                align-items: center;
                                                height: 100vh;
                                                margin: 0;
                                                background-color: #f4f4f9;
                                            }}
                                            h2 {{
                                                text-align: justified;
                                                color: black;
                                            }}
                                            table {{
                                                border-collapse: collapse;
                                                width: 60%;
                                                margin: 20px auto;
                                                background-color: #ffffff;
                                                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                                            }}
                                            th, td {{
                                                padding: 12px;
                                                text-align: center;
                                                border-bottom: 1px solid #ddd;
                                            }}
                                            th {{
                                                background-color: #4CAF50;
                                                color: white;
                                            }}
                                            tr:hover {{ background-color: #f1f1f1; }}
                                            input[type="submit"] {{
                                                background-color: #4CAF50;
                                                color: white;
                                                border: none;
                                                padding: 8px 12px;
                                                cursor: pointer;
                                                border-radius: 4px;
                                            }}
                                            input[type="submit"]:hover {{
                                                background-color: #45a049;
                                            }}
                                        </style>
                                        <h2>Available Mess</h2>
                                        <table border="1">
                                        <tr><th>Mess Name</th><th>Action</th></tr>
                                        """
                    for row in mess_names:
                        html_response += f"""
                                            <tr> 
                                                <td>{row[0]}</td>
                                
                                                <td>
                                                    <form action="/view_menu" method="POST" style="display:inline;">
                                                        <input type="hidden" name="messname" value="{row[1]}">
                                                        <input type="submit" value="View Menu">
                                                    </form>
                                                </td>   
                                            </tr>
                                        """
                    html_response += """
                                        </table>
                                        </body>
                                        </html>
                                        """ 
                    self.wfile.write(html_response.encode())

                    



            else:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Invalid credentials!")
                

        elif self.path == "/update_menu":
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
            form_data = {key: form.getvalue(key) for key in form.keys()}
            add_menu_item(form_data,username)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Item added successfully!")


        elif self.path=="/delete_item":
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
            form_data = {key: form.getvalue(key) for key in form.keys()}
            print()
            fooditem=(form_data['fooditem'])
            
           
            if fooditem and username:
                delete_menu_item(username,(fooditem))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Item deleted successfully!")


        elif self.path=="/view_menu":
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
            form_data = {key: form.getvalue(key) for key in form.keys()}
            print()
            messusername=(form_data['messname'])
            
           
            if messusername:
                menu_data=get_mess_menu(messusername)
                
                if menu_data:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()

                    html_response = f"""
                    <html><body>
                    <h2>Menu for Mess: {messusername}</h2>
                    <table border="1">
                    <tr><th>Menu Item</th><th>Price</th></tr>
                    """
                    for row in menu_data:
                        html_response += f"""
                        <tr>
                            <td>{row[1]}</td>
                            <td>{row[2]}</td>
                        </tr>
                        """
                    html_response += """
                    </table>
                    """
                    self.wfile.write(html_response.encode())

                else:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()

                    html_response=f"""
                    <html><body>
                    <h2>NO DATA AVAILABALE</h2>
                    """
                    html_response += "</table></body></html>"
                    self.wfile.write(html_response.encode())


        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Error Occured, please check your inputs!")




def runserver():
    port = 8081
    httpd = HTTPServer(('0.0.0.0', port), MyHTTPRequestHandler)
    print(f"Server running on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    runserver()
