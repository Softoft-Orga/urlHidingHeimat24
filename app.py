import mimetypes
from http import HTTPStatus

import requests
from bs4 import BeautifulSoup
from flask import Flask, Response, request

from tag_replacers import HTTP_PROTOCOL, HTML_PARSER, TAG_REPLACER_LIST, replace_chatbase, PROXY_URL_STRING, \
    undo_replacement

CHATBASE_ROOT_URL = "https://www.chatbase.co/"
CHATBASE_IFRAME_URL = CHATBASE_ROOT_URL + "chatbot-iframe/"

app = Flask(__name__)


def build_chatbot_iframe_url(chatbase_bot_id):
    return CHATBASE_IFRAME_URL + chatbase_bot_id


def change_url(url):
    if HTTP_PROTOCOL not in url:
        url = CHATBASE_ROOT_URL + url
    return url


def fetch_and_rewrite(url):
    response = requests.get(url)
    if response.status_code == HTTPStatus.OK:
        soup = BeautifulSoup(response.text, HTML_PARSER)
        for tag_replacer in TAG_REPLACER_LIST:
            tag_replacer.replace(soup)
        return replace_chatbase(str(soup))
    else:
        return None


@app.route('/<chatbase_bot_id>')
def home(chatbase_bot_id):
    rewritten_html = fetch_and_rewrite(build_chatbot_iframe_url(chatbase_bot_id))
    if rewritten_html:
        return Response(rewritten_html, content_type='text/html; charset=utf-8')
    else:
        return "Error fetching content", HTTPStatus.NOT_FOUND


@app.route(PROXY_URL_STRING)
def proxy():
    url = undo_replacement(request.args.get('url'))
    url = change_url(url)
    r = requests.get(url)
    if r.status_code == HTTPStatus.OK:
        content_type = r.headers.get('content-type', mimetypes.guess_type(url)[0])
        content = r.content
        if 'javascript' in content_type:
            content = replace_chatbase(r.text)
        return Response(content, content_type=content_type)
    else:
        return "Error fetching content", HTTPStatus.NOT_FOUND


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
