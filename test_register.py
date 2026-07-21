import urllib.request
import json

url = "http://127.0.0.1:8080/api/v1/register"
data = {
    "org_name": "test-script.org.com",
    "email": "test-script@test.com",
    "password": "Test1234!",
    "agent_url": "http://cello-docker-agent:8080/api/v1/"
}
req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req, timeout=5) as response:
        print("Status:", response.status)
        print("Body:", response.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print("Body:", e.read().decode())
except Exception as e:
    print("Error:", str(e))
