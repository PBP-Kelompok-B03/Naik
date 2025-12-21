import requests
import json

# Test chat API list
def test_chat_api_list():
    url = 'http://127.0.0.1:8000/chat/api/list-test/'

    try:
        response = requests.get(url)
        print('Status:', response.status_code)
        print('Response:', response.text[:500])  # Limit output

        if response.status_code == 200:
            try:
                data = response.json()
                print('JSON parsed successfully')
                print('Conversations count:', len(data.get('conversations', [])))
            except json.JSONDecodeError as e:
                print('JSON decode error:', e)
        else:
            print('Error response')

    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    test_chat_api_list()