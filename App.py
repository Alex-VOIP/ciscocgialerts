# Authors: Unity Networx, Alex R
print("Authors: Unity Networx, Alex R")

from flask import Flask, render_template_string, request, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
import requests

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    "admin": generate_password_hash("password") #Username and Password for the Web-UI
}

# Fixed IPs and auth
IP_ADDRESSES = ["10.0.0.109"] # IP's of phones (if multiple use format like this ["192.168.5.22", "192.168.5.30"])
PORT = "80" #for https use 443
USERNAME = "Cisco" #phones username
PASSWORD = "Cisco" # phones password

# Templates
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cisco Alerting System</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f4; }
        h1 { color: #333; }
        form { margin-bottom: 20px; }
        input[type=text], textarea { width: 100%; padding: 10px; margin-top: 5px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
        input[type=submit] { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        input[type=submit]:hover { background-color: #45a049; }
        .shortcuts { float: right; width: 30%; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .shortcut { margin-bottom: 15px; }
        .shortcut form { display: inline; }
        .main { width: 65%; float: left; }
    </style>
</head>
<body>
    <div class="main">
    <h1>Cisco Services</h1>
    <form method="post" action="/send_text">
        <label>Title:</label>
        <input type="text" name="title" required>
        <label>Text:</label>
        <textarea name="text" rows="5" required></textarea>
        <input type="submit" value="Send Text">
    </form>
    </div>

    <div class="shortcuts">
        <h2>Shortcuts</h2>
        <div class="shortcut">
            <form method="post" action="/send_shortcut">
                <input type="hidden" name="url" value="http://provisioning.csptech.org/executelockdown.xml">
                <input type="submit" value="Lockdown">
            </form>
        </div>
        <div class="shortcut">
            <form method="post" action="/send_shortcut">
                <input type="hidden" name="url" value="http://provisioning.csptech.org/weather.xml">
                <input type="submit" value="Tornado">
            </form>
        </div>
        <div class="shortcut">
            <form method="post" action="/send_shortcut">
                <input type="hidden" name="url" value="http://provisioning.csptech.org/activeshooter.xml">
                <input type="submit" value="Active Shooter">
            </form>
        </div>
    </div>

</body>
</html>
"""

# Auth handlers
@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

# Helper function to send CGI Execute

def send_cgi_execute(url):
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<CiscoIPPhoneExecute>
    <ExecuteItem URL="{url}" Priority="0" />
</CiscoIPPhoneExecute>'''
    for ip in IP_ADDRESSES:
        try:
            response = requests.post(
                f'http://{ip}:{PORT}/CGI/Execute',
                auth=(USERNAME, PASSWORD),
                timeout=5,
                data={'XML': xml}
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send to {ip}: {e}")

# Helper function to send text message

def send_cgi_text(title, text):
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<CiscoIPPhoneText>
    <Title>{title}</Title>
    <Text>{text}</Text>
    <SoftKeyItem>
        <Name>Exit</Name>
        <URL>SoftKey:Exit</URL>
        <Position>1</Position>
    </SoftKeyItem>
</CiscoIPPhoneText>'''
    for ip in IP_ADDRESSES:
        try:
            response = requests.post(
                f'http://{ip}:{PORT}/CGI/Execute',
                auth=(USERNAME, PASSWORD),
                timeout=5,
                data={'XML': xml}
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send to {ip}: {e}")

# Routes
@app.route('/')
@auth.login_required
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/send_text', methods=['POST'])
@auth.login_required
def send_text():
    title = request.form.get('title')
    text = request.form.get('text')
    send_cgi_text(title, text)
    return redirect(url_for('index'))

@app.route('/send_shortcut', methods=['POST'])
@auth.login_required
def send_shortcut():
    url = request.form.get('url')
    send_cgi_execute(url)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4570, debug=False)
