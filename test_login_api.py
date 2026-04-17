import requests

def test_login():
    url = "http://127.0.0.1:8000/api/auth/login"
    data = {
        "email": "test@example.com",
        "password": "password"  # I don't know the password
    }
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        if response.headers.get('Content-Type') == 'application/json':
            print(f"JSON: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
