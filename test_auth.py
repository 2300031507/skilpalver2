import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_signup():
    print("Testing signup...")
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "role": "student",
        "university_id": "UNI001"
    }
    response = requests.post(f"{BASE_URL}/auth/signup", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")

def test_login():
    print("Testing login...")
    payload = {
        "email": "test@example.com",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")

if __name__ == "__main__":
    test_signup()
    test_login()
