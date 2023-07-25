from dotenv import load_dotenv

load_dotenv()
import os

name = os.environ.get("name-of-sender")

filter_words = ['apples', 'oranges','twitter']

def filterList(data):
    for fw in filter_words:
        print(fw)
        if fw in data:
            return False
    return True

def filter(data):
    print(name)
    #print(data[0]['content'])
    if data[0]['author']['username'] == name and filterList(data[0]['content']):
        return True
    
    return False
