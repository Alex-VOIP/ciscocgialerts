# Authors: Unity Networx, Alex R
print("Authors: Unity Networx, Alex R")

from flask import Flask, render_template_string, request, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
import requests
import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Disable SSL warnings for insecure HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    "admin": generate_password_hash("password") #Username and Password for the Web-UI
}

# Fixed IPs and auth
IP_ADDRESSES = ["10.0.0.109"] # IP's of phones (if multiple use format like this ["192.168.5.22", "192.168.5.30"])
PORT = "443" #HTTPS port
USERNAME = "Cisco" #phones username
PASSWORD = "Cisco" # phones password

def create_session():
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Shortcusts You can change the as you want :)
EMERGENCY_TEMPLATES = {
    "lockdown": {
        "name": "Lockdown",
        "xml": '''<?xml version="1.0" encoding="UTF-8"?>
<CiscoIPPhoneText>
<Title>905 ALERT - SECURE</Title>
<prompt>Select an Action</prompt>
<Text>Secure the building. Bring all students inside and lock all exterior doors. Continue business as usual </Text>
<SoftKeyItem>
<Name>Stop</Name>
<URL>SoftKey:Exit</URL>
<Position>1</Position>
</SoftKeyItem>
<SoftKeyItem>
<Name>Exit</Name>
<URL>SoftKey:Exit</URL>
<Position>4</Position>
</SoftKeyItem>
</CiscoIPPhoneText>'''
    },
    "tornado": {
        "name": "Tornado",
        "xml": '''<?xml version="1.0" encoding="UTF-8"?>
<CiscoIPPhoneText>
<Title>906 ALERT - SEVERE WEATHER</Title>
<prompt>Select an Action</prompt>
<Text>SEVERE WEATHER WARNING! Proceed to designated shelter areas immediately. Stay away from windows and doors.</Text>
<SoftKeyItem>
<Name>Stop</Name>
<URL>SoftKey:Exit</URL>
<Position>1</Position>
</SoftKeyItem>
<SoftKeyItem>
<Name>Exit</Name>
<URL>SoftKey:Exit</URL>
<Position>4</Position>
</SoftKeyItem>
</CiscoIPPhoneText>'''
    },
    "active_shooter": {
        "name": "Active Shooter",
        "xml": '''<?xml version="1.0" encoding="UTF-8"?>
<CiscoIPPhoneText>
<Title>904 ALERT - ACTIVE SHOOTER</Title>
<prompt>Select an Action</prompt>
<Text>LOCKDOWN! THIS IS NOT A DRILL! An active shooter has been spotted on campus. Lights Out! Out of Sight! </Text>
<SoftKeyItem>
<Name>Stop</Name>
<URL>SoftKey:Exit</URL>
<Position>1</Position>
</SoftKeyItem>
<SoftKeyItem>
<Name>Exit</Name>
<URL>SoftKey:Exit</URL>
<Position>4</Position>
</SoftKeyItem>
</CiscoIPPhoneText>'''
    }
}

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
        .emergency-btn { background-color: #dc3545 !important; }
        .emergency-btn:hover { background-color: #c82333 !important; }
        .weather-btn { background-color: #ffc107 !important; color: black !important; }
        .weather-btn:hover { background-color: #e0a800 !important; }
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
        <h2>Emergency Alerts</h2>
        <div class="shortcut">
            <form method="post" action="/send_emergency">
                <input type="hidden" name="alert_type" value="lockdown">
                <input type="submit" value="Lockdown" class="emergency-btn">
            </form>
        </div>
        <div class="shortcut">
            <form method="post" action="/send_emergency">
                <input type="hidden" name="alert_type" value="tornado">
                <input type="submit" value="Tornado" class="weather-btn">
            </form>
        </div>
        <div class="shortcut">
            <form method="post" action="/send_emergency">
                <input type="hidden" name="alert_type" value="active_shooter">
                <input type="submit" value="Active Shooter" class="emergency-btn">
            </form>
        </div>
    </div>

</body>
</html>
"""

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

def send_direct_xml(xml_content):
    session = create_session()
    
    for ip in IP_ADDRESSES:
        try:
            response = session.post(
                f'https://{ip}:{PORT}/CGI/Execute',
                auth=(USERNAME, PASSWORD),
                timeout=10,
                data={'XML': xml_content},
                verify=False
            )
            response.raise_for_status()
            print(f"Emergency alert sent successfully to {ip}")
        except requests.RequestException as e:
            print(f"Failed to send emergency alert to {ip}: {e}")
        finally:
            session.close()

def send_cgi_execute(url):
    session = create_session()
    
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<CiscoIPPhoneExecute>
    <ExecuteItem URL="{url}" Priority="0" />
</CiscoIPPhoneExecute>'''
    
    for ip in IP_ADDRESSES:
        try:
            response = session.post(
                f'https://{ip}:{PORT}/CGI/Execute',
                auth=(USERNAME, PASSWORD),
                timeout=10,
                data={'XML': xml},
                verify=False
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send to {ip}: {e}")
        finally:
            session.close()

def send_cgi_text(title, text):
    session = create_session()
    
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
            response = session.post(
                f'https://{ip}:{PORT}/CGI/Execute',
                auth=(USERNAME, PASSWORD),
                timeout=10,
                data={'XML': xml},
                verify=False
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send to {ip}: {e}")
        finally:
            session.close()

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

@app.route('/send_emergency', methods=['POST'])
@auth.login_required
def send_emergency():
    alert_type = request.form.get('alert_type')
    
    if alert_type in EMERGENCY_TEMPLATES:
        xml_content = EMERGENCY_TEMPLATES[alert_type]['xml']
        send_direct_xml(xml_content)
        print(f"Emergency alert '{alert_type}' sent to all phones")
    else:
        print(f"Unknown emergency alert type: {alert_type}")
    
    return redirect(url_for('index'))

@app.route('/send_shortcut', methods=['POST'])
@auth.login_required
def send_shortcut():
    url = request.form.get('url')
    send_cgi_execute(url)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=False)
