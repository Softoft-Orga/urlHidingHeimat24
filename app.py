from bs4 import BeautifulSoup
from flask import Flask, Response, request
import requests

CHATBASE_BASE_URL = "https://www.chatbase.co/chatbot-iframe/Z7FWEuyvj1NI_k1GtlE0v"

app = Flask(__name__)


def fetch_and_rewrite(url):
    r = requests.get(url)

    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')

        # Update the URLs for script and link tags to go through the proxy
        for script_tag in soup.find_all('script', {'src': True}):
            script_tag['src'] = change_url(script_tag['src'])

        for link_tag in soup.find_all('link', {'href': True}):
            link_tag['href'] = change_url(link_tag['href'])

        return str(soup)
    else:
        return None


@app.route('/')
def home():
    rewritten_html = fetch_and_rewrite(CHATBASE_BASE_URL)
    if rewritten_html:
        return Response(rewritten_html, content_type='text/html; charset=utf-8')
    else:
        return "Error fetching content", 404


def change_url(url):
    if "http" not in url:
        url = "https://www.chatbase.co/" + url
    return url


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
