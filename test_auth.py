import requests
import json

# Test register
data = {
    'username': 'testuser2',
    'password1': 'testpass123',
    'password2': 'testpass123',
    'role': 'buyer'
}

try:
    response = requests.post('http://127.0.0.1:8000/auth/register/',
                           json=data,
                           headers={'Content-Type': 'application/json'})
    print('Register Status:', response.status_code)
    print('Register Response:', response.json())
except Exception as e:
    print('Register Error:', e)

# Test login
login_data = {
    'username': 'testuser2',
    'password': 'testpass123'
}

try:
    response = requests.post('http://127.0.0.1:8000/auth/login/',
                           json=login_data,
                           headers={'Content-Type': 'application/json'})
    print('Login Status:', response.status_code)
    print('Login Response:', response.json())
except Exception as e:
    print('Login Error:', e)