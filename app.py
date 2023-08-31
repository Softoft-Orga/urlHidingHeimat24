import mimetypes
from http import HTTPStatus

import requests
from bs4 import BeautifulSoup
from flask import Flask, Response, request, send_from_directory

from tag_replacers import HTTP_PROTOCOL, HTML_PARSER, TAG_REPLACER_LIST, PROXY_URL_STRING, \
    undo_replacement

CHATBASE_ROOT_URL = "https://www.chatbase.co/"
CHATBASE_ROOT_URL_NO_TRAILING_SLASH = "https://www.chatbase.co"
CHATBASE_IFRAME_URL = CHATBASE_ROOT_URL + "chatbot-iframe/"

app = Flask(__name__)

def build_chatbot_iframe_url(chatbase_bot_id):
    return CHATBASE_IFRAME_URL + chatbase_bot_id


def change_url(url: str):
    if HTTP_PROTOCOL not in url:
        if url.startswith('/'):
            url = CHATBASE_ROOT_URL_NO_TRAILING_SLASH + url
        else:
            url = CHATBASE_ROOT_URL + url

    return url


def fetch_and_rewrite(url):
    response = requests.get(url)
    if response.status_code == HTTPStatus.OK:
        soup = BeautifulSoup(response.text, HTML_PARSER)
        for tag_replacer in TAG_REPLACER_LIST:
            tag_replacer.replace(soup)
        new_script = soup.new_tag("script", src="/index.js")
        soup.head.append(new_script)
        return str(soup)
    else:
        return None


@app.route('/index.js')
def serve_js_file():
    return send_from_directory('.', 'index.js')


@app.route('/chatbot/<chatbase_bot_id>')
def home(chatbase_bot_id):
    rewritten_html = fetch_and_rewrite(build_chatbot_iframe_url(chatbase_bot_id))
    if rewritten_html:
        return Response(rewritten_html, content_type='text/html; charset=utf-8')
    else:
        return "Error fetching content", HTTPStatus.NOT_FOUND


@app.route(PROXY_URL_STRING, methods=['GET', 'POST'])
def proxy():
    url = undo_replacement(request.args.get('url'))
    url = change_url(url)
    if request.method == 'POST':
        incoming_data = request.json
        response = requests.post(url, json=incoming_data)
        return response.text, response.status_code

    print(url)
    r = requests.get(url)
    if r.status_code == HTTPStatus.OK:
        content_type = r.headers.get('content-type', mimetypes.guess_type(url)[0])
        content = r.content
        return Response(content, content_type=content_type)
    else:
        return "Error fetching content", HTTPStatus.NOT_FOUND


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
