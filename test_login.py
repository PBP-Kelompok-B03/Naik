import requests

# Test login endpoint
def test_login():
    url = 'http://127.0.0.1:8000/auth/login/'

    # Test data - use admin user
    login_data = {
        'username': 'admin',
        'password': 'admin'
    }

    try:
        response = requests.post(url, data=login_data)
        print('Login status:', response.status_code)
        print('Response headers:', dict(response.headers))
        print('Cookies:', response.cookies)

        if response.status_code == 200:
            print('Login successful')
        else:
            print('Login failed')
            print('Response content:', response.text[:500])

    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    test_login()