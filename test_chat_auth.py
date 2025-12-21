import requests
import json
from django.test import Client
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naik.settings')
django.setup()

# Test chat API with proper authentication
def test_chat_api_authenticated():
    client = Client()

    # First login
    login_response = client.post('/auth/login/', {
        'username': 'testuser',  # You'll need to create this user
        'password': 'testpass'
    })

    print('Login status:', login_response.status_code)
    if login_response.status_code != 200:
        print('Login failed, trying with existing user...')

        # Try to get first user and login
        from django.contrib.auth.models import User
        try:
            user = User.objects.filter(is_active=True).first()
            if user:
                # Force login
                client.force_login(user)
                print(f'Force logged in as: {user.username}')
            else:
                print('No users found')
                return
        except Exception as e:
            print('Error:', e)
            return

    # Now test chat API
    response = client.get('/chat/api/list/')
    print('Chat API status:', response.status_code)
    print('Response content type:', response.get('Content-Type', 'Unknown'))

    if response.status_code == 200:
        try:
            data = response.json()
            print('JSON parsed successfully')
            print('Response:', json.dumps(data, indent=2))
        except json.JSONDecodeError as e:
            print('JSON decode error:', e)
            print('Raw response:', response.content[:500])
    else:
        print('Error response:', response.content[:500])

if __name__ == '__main__':
    test_chat_api_authenticated()