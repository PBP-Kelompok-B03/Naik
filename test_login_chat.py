import requests

# Test login and then chat API
def test_login_and_chat():
    session = requests.Session()

    # First login
    login_url = 'http://127.0.0.1:8000/auth/login/'
    login_data = {
        'username': 'admin',
        'password': 'admin'
    }

    login_response = session.post(login_url, data=login_data)
    print('Login status:', login_response.status_code)

    if login_response.status_code == 200:
        print('Login successful, cookies:', session.cookies)

        # Now test chat API
        chat_url = 'http://127.0.0.1:8000/chat/api/list/'
        chat_response = session.get(chat_url)
        print('Chat API status:', chat_response.status_code)

        if chat_response.status_code == 200:
            try:
                data = chat_response.json()
                print('Chat API successful, conversations:', len(data.get('conversations', [])))
            except:
                print('Chat API returned non-JSON:', chat_response.text[:200])
        else:
            print('Chat API failed:', chat_response.text[:200])
    else:
        print('Login failed:', login_response.text)

if __name__ == '__main__':
    test_login_and_chat()