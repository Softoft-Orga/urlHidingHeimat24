import mimetypes
from http import HTTPStatus

import requests
from bs4 import BeautifulSoup
from flask import Flask, Response, request
from flask_caching import Cache
from flask_cors import CORS

from tag_replacers import HTTP_PROTOCOL, HTML_PARSER, TAG_REPLACER_LIST, PROXY_URL_STRING, replace_chatbase

CHATBASE_ROOT_URL = "https://www.chatbase.co/"
CHATBASE_ROOT_URL_NO_TRAILING_SLASH = "https://www.chatbase.co"
CHATBASE_IFRAME_URL = CHATBASE_ROOT_URL + "chatbot-iframe/"

app = Flask(__name__)
CORS(app, resources={
    r"*": {"origins": ["http://localhost:*", "http://127.0.0.1:*", "https://softoft.de/*", "https://*.softoft.de/*"]}})
cache = Cache(app, config={'CACHE_TYPE': 'simple'})


def remove_power_by(soup):
    target_form = soup.find('form')
    powered_by = target_form.find('p', {'class': 'text-center'}) if target_form else None
    if powered_by:
        powered_by.decompose()


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
        remove_power_by(soup)
        for tag_replacer in TAG_REPLACER_LIST:
            tag_replacer.replace(soup)
        return str(soup)
    else:
        return None


@cache.memoize(timeout=3600)
@app.route('/chatbot/<chatbase_bot_id>')
def home(chatbase_bot_id):
    rewritten_html = fetch_and_rewrite(build_chatbot_iframe_url(chatbase_bot_id))
    if rewritten_html:
        return Response(rewritten_html, content_type='text/html; charset=utf-8')
    else:
        return "Error fetching content", HTTPStatus.NOT_FOUND


def intercept_request(url):
    url = change_url(url)
    if request.method == 'POST':
        return intercept_post_request(url)
    else:
        return intercept_get_request(url)


def intercept_post_request(target_url):
    incoming_data = request.json
    response = requests.post(target_url, json=incoming_data, stream=True)

    def generate():
        for chunk in response.iter_content(chunk_size=1192):
            yield chunk

    return Response(generate(), content_type=response.headers['content-type'])


def intercept_get_request(target_url):
    r = requests.get(target_url)
    if r.status_code == HTTPStatus.OK:
        content_type = r.headers.get('content-type', mimetypes.guess_type(target_url)[0])
        content = r.content
        if "javascript" in content_type:
            content = replace_chatbase(r.text)
        return Response(content, content_type=content_type)
    else:
        return "Error fetching content", HTTPStatus.NOT_FOUND


@cache.memoize(timeout=3600)
@app.route(PROXY_URL_STRING, methods=['GET'])
def proxy():
    return intercept_request(request.args.get('url'))


@cache.memoize(timeout=3600)
@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_and_intercept(path):
    return intercept_request(path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
