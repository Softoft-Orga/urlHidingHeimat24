from http import HTTPStatus

from flask import Flask, Response, request
from flask_cors import CORS

from src.config import URL_PARAMETER, PROXY_URL_STRING
from src.request_interception import CONTENT_TYPE, build_chatbot_iframe_url, fetch_and_rewrite, \
    RequestInterception

app = Flask(__name__)
CORS(app, resources={
    r"*": {"origins": ["http://localhost:*", "http://127.0.0.1:*", "https://softoft.de/*", "https://*.softoft.de/*"]}})
request_interception = RequestInterception()


@app.route('/chatbot/<chatbase_bot_id>')
def home(chatbase_bot_id):
    rewritten_html = fetch_and_rewrite(build_chatbot_iframe_url(chatbase_bot_id))
    if rewritten_html is not None:
        return Response(rewritten_html, content_type=CONTENT_TYPE)
    else:
        return "Error fetching content", HTTPStatus.NOT_FOUND


@app.route(PROXY_URL_STRING, methods=['GET'])
def proxy():
    return request_interception.intercept_request(request.args.get(URL_PARAMETER))


@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_and_intercept(path):
    return request_interception.intercept_request(path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
