import os
import urllib.request
from http import HTTPStatus

import requests
from bs4 import BeautifulSoup
from flask import request, Response

from src.config import FULL_LOCALHOST_URL
from src.content_type import ContentType, ContentTypeFinder
from src.tag_replacers import HTTP_PROTOCOL, HTML_PARSER, TAG_REPLACER_LIST, replace_chatbase

CHATBASE_ROOT_URL = "https://www.chatbase.co/"
CHATBASE_ROOT_URL_NO_TRAILING_SLASH = "https://www.chatbase.co"
CHATBASE_IFRAME_URL = CHATBASE_ROOT_URL + "chatbot-iframe/"
CONTENT_TYPE = "text/html; charset=utf-8"
HTTP_POST = "POST"
HTTP_GET = "GET"
STATIC_FOLDER = "static"
JS_FILE_EXTENSION = ".js"


def build_chatbot_iframe_url(chatbase_bot_id: str) -> str:
    return CHATBASE_IFRAME_URL + chatbase_bot_id


def convert_to_chatbase_url(url: str) -> str:
    if HTTP_PROTOCOL in url:
        return url
    if url.startswith('/'):
        return CHATBASE_ROOT_URL_NO_TRAILING_SLASH + url
    else:
        return CHATBASE_ROOT_URL + url


def remove_power_by(soup):
    target_form = soup.find("form")
    powered_by = target_form.find('p', {"class": "text-center"}) if target_form else None
    if powered_by:
        powered_by.decompose()


def fetch_and_rewrite(url) -> str:
    response = requests.get(url)
    if response.ok:
        soup = BeautifulSoup(response.text, HTML_PARSER)
        remove_power_by(soup)
        for tag_replacer in TAG_REPLACER_LIST:
            tag_replacer.replace(soup)
        return str(soup)


class RequestInterception:
    def __init__(self):
        self.request_method_interception = {
            HTTP_POST: self._intercept_post_request,
            HTTP_GET: self._intercept_get_request
        }

    def intercept_request(self, url: str):
        if self._cache_url(url):
            print("URL from cache: " + url)
            return self._load_js_file_from_cache(url)
        print("URL from chatbase: " + url)
        chatbase_url = convert_to_chatbase_url(url)

        if request.method not in self.request_method_interception:
            raise Exception("Unsupported method")
        return self.request_method_interception[request.method](chatbase_url)

    def _convert_url_to_static_file_name(self, url):
        return url.replace("/", "_")

    def _cache_url(self, url):
        return any([url.endswith(extension) for extension in [".js", ".css", ".png", ".jpg", ".jpeg", ".gif"]])

    def _load_js_file_from_cache(self, url):
        url_formatted = self._convert_url_to_static_file_name(url)
        full_url = CHATBASE_ROOT_URL + url
        local_path = os.path.join(STATIC_FOLDER, url_formatted)
        if os.path.exists(local_path):
            return self._get_static_file(url_formatted)
        urllib.request.urlretrieve(full_url, local_path)
        return self._get_static_file(url_formatted)

    def _get_static_file(self, file_name):
        return self._intercept_get_request(f"{FULL_LOCALHOST_URL}/{STATIC_FOLDER}/" + file_name,
                                           cache_age=60 * 60 * 24 * 365)

    def _intercept_post_request(self, target_url):
        incoming_data = request.json
        response = requests.post(target_url, json=incoming_data, stream=True)

        def generate():
            for chunk in response.iter_content(chunk_size=1192):
                yield chunk

        return Response(generate(), content_type=response.headers["content-type"])

    def _intercept_get_request(self, target_url, cache_age=0):
        response = requests.get(target_url)
        if response.ok:
            content_type: ContentType = ContentTypeFinder.find_type_for(response)
            content = response.content
            if content_type.is_javascript():
                content = replace_chatbase(response.text)
            intercepted_response = Response(content, content_type=content_type.mime_type)
            intercepted_response.headers["Cache-Control"] = f"public, max-age={cache_age}"
            return intercepted_response
        else:
            return "Error fetching content", HTTPStatus.NOT_FOUND
