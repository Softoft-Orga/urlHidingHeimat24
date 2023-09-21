from http import HTTPStatus

import requests
from bs4 import BeautifulSoup
from flask import request, Response

from src.content_type import ContentType, ContentTypeFinder
from src.tag_replacers import HTTP_PROTOCOL, HTML_PARSER, TAG_REPLACER_LIST, replace_chatbase

CHATBASE_ROOT_URL = "https://www.chatbase.co/"
CHATBASE_ROOT_URL_NO_TRAILING_SLASH = "https://www.chatbase.co"
CHATBASE_IFRAME_URL = CHATBASE_ROOT_URL + "chatbot-iframe/"
CONTENT_TYPE = "text/html; charset=utf-8"
HTTP_POST = "POST"
HTTP_GET = "GET"


def build_chatbot_iframe_url(chatbase_bot_id: str) -> str:
    return CHATBASE_IFRAME_URL + chatbase_bot_id


def change_url(url: str) -> str:
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
    @classmethod
    def intercept_request(cls, url):
        url = change_url(url)
        if request.method == HTTP_POST:
            return cls._intercept_post_request(url)
        elif request.method == HTTP_GET:
            return cls._intercept_get_request(url)
        raise Exception("Unsupported method")

    @staticmethod
    def _intercept_post_request(target_url):
        incoming_data = request.json
        response = requests.post(target_url, json=incoming_data, stream=True)

        def generate():
            for chunk in response.iter_content(chunk_size=1192):
                yield chunk

        return Response(generate(), content_type=response.headers["content-type"])

    @staticmethod
    def _intercept_get_request(target_url):
        response = requests.get(target_url)
        if response.ok:
            content_type: ContentType = ContentTypeFinder.find_type_for(response)
            content = response.content
            if content_type.is_javascript():
                content = replace_chatbase(response.text)
            return Response(content, content_type=content_type.mime_type)
        else:
            return "Error fetching content", HTTPStatus.NOT_FOUND
