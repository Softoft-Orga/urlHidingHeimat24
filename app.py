import mimetypes
from http import HTTPStatus
from typing import List

import requests
from bs4 import BeautifulSoup
from flask import Flask, Response, request

CHATBASE_ROOT_URL = "https://www.chatbase.co/"
CHATBASE_URL = CHATBASE_ROOT_URL + "chatbot-iframe/Z7FWEuyvj1NI_k1GtlE0v"

app = Flask(__name__)

CHATBASE_REPLACEMENT = "heimat24-chat"
REAL_CHATBASE = "chatbase"
PROXY_URL_STRING = "/heimat24-chat"
HTML_PARSER = "html.parser"
SRC_HTML_ATTRIBUTE = "src"
HREF_HTML_ATTRIBUTE = "href"
SRCSET_HTML_ATTRIBUTE = "srcset"

SCRIPT_HTML_TAG = "script"
LINK_HTML_TAG = "link"
IMG_HTML_TAG = "img"

HTTP_PROTOCOL = "http"



class ReplaceStrategy:
    def __init__(self, html_tag_attribute):  # Fixed typo here
        self.html_tag_attribute = html_tag_attribute

    def replace(self, tag):
        raise NotImplementedError


class SrcReplaceStrategy(ReplaceStrategy):
    def __init__(self):  # Fixed typo here
        super().__init__(SRC_HTML_ATTRIBUTE)

    def replace(self, tag):
        tag[self.html_tag_attribute] = build_proxy_url(tag[self.html_tag_attribute])


class SrcSetReplaceStrategy(ReplaceStrategy):
    def __init__(self):  # Fixed typo here
        super().__init__(SRCSET_HTML_ATTRIBUTE)

    def replace(self, tag):
        tag[self.html_tag_attribute] = ""


class HrefReplaceStrategy(ReplaceStrategy):
    def __init__(self):  # Fixed typo here
        super().__init__(HREF_HTML_ATTRIBUTE)

    def replace(self, tag):
        tag[self.html_tag_attribute] = build_proxy_url(tag[self.html_tag_attribute])


class TagReplacer:
    def __init__(self, tag, replace_strategies: List[ReplaceStrategy]):
        self.tag = tag
        self.replace_strategies = replace_strategies  # Type hinting not needed here

    def replace(self, soup):
        for replace_strategy in self.replace_strategies:
            for tag in soup.find_all(self.tag, {replace_strategy.html_tag_attribute: True}):
                replace_strategy.replace(tag)


TAG_REPLACER_LIST = [
    TagReplacer(SCRIPT_HTML_TAG, [SrcReplaceStrategy()]),
    TagReplacer(LINK_HTML_TAG, [HrefReplaceStrategy()]),
    TagReplacer(IMG_HTML_TAG, [SrcReplaceStrategy(), SrcSetReplaceStrategy()])
]


def replace_chatbase(text):
    return text.replace(REAL_CHATBASE, CHATBASE_REPLACEMENT)


def undo_replacement(text):
    return text.replace(CHATBASE_REPLACEMENT, REAL_CHATBASE)


def build_proxy_url(url):
    return f"{PROXY_URL_STRING}?url=" + replace_chatbase(url)


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


@app.route('/')
def home():
    rewritten_html = fetch_and_rewrite(CHATBASE_URL)
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
        if 'javascript' in content_type:
            js_content = replace_chatbase(r.text)
            return Response(js_content, content_type=content_type)
        else:
            return Response(r.content, content_type=content_type)
    else:
        return "Error fetching content", HTTPStatus.NOT_FOUND


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
