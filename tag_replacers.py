from dataclasses import dataclass
from typing import List

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


def replace_chatbase(text):
    return text.replace(REAL_CHATBASE, CHATBASE_REPLACEMENT)


def undo_replacement(text):
    return text.replace(CHATBASE_REPLACEMENT, REAL_CHATBASE)


def build_proxy_url(url):
    return f"{PROXY_URL_STRING}?url=" + replace_chatbase(url)


@dataclass
class ReplaceStrategy:
    html_tag_attribute: str | None = None

    def replace(self, tag):
        raise NotImplementedError


@dataclass
class SrcReplaceStrategy(ReplaceStrategy):
    def __post_init__(self):
        self.html_tag_attribute = SRC_HTML_ATTRIBUTE

    def replace(self, tag):
        tag[self.html_tag_attribute] = build_proxy_url(tag[self.html_tag_attribute])


@dataclass
class SrcSetReplaceStrategy(ReplaceStrategy):
    def __post_init__(self):
        self.html_tag_attribute = SRCSET_HTML_ATTRIBUTE

    def replace(self, tag):
        tag[self.html_tag_attribute] = ""


@dataclass
class HrefReplaceStrategy(ReplaceStrategy):
    def __post_init__(self):
        self.html_tag_attribute = HREF_HTML_ATTRIBUTE

    def replace(self, tag):
        tag[self.html_tag_attribute] = build_proxy_url(tag[self.html_tag_attribute])


@dataclass
class TagReplacer:
    tag: str
    replace_strategies: List[ReplaceStrategy]

    def replace(self, soup):
        for replace_strategy in self.replace_strategies:
            for tag in soup.find_all(self.tag, {replace_strategy.html_tag_attribute: True}):
                replace_strategy.replace(tag)


TAG_REPLACER_LIST = [
    TagReplacer(SCRIPT_HTML_TAG, [SrcReplaceStrategy()]),
    TagReplacer(LINK_HTML_TAG, [HrefReplaceStrategy()]),
    TagReplacer(IMG_HTML_TAG, [SrcReplaceStrategy(), SrcSetReplaceStrategy()])
]
