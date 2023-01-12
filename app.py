from email import message
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,
)

import os
import sqlite3
from flask import g
import random
from flask_bootstrap import Bootstrap
import requests
import json
import types
import cld3

app = Flask(__name__)
bootstrap = Bootstrap(app)
line_bot_api = LineBotApi(os.environ['YOUR_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['YOUR_CHANNEL_SECRET'])

# noby api
ENDPOINT_noby = "https://www.cotogoto.ai/webapi/noby.json"
ENDPOINT_cotoha = "https://api.ce-cotoha.com/api/dev/nlp/v1/sentiment"
COTOHA_publish_url = "https://api.ce-cotoha.com/v1/oauth/accesstokens"
API_KEY_noby = os.environ['noby_key']
access_token = ""

# flask 動作確認
@app.route("/")
def test():
    return "<h1>Tests</h1>"

# cotoha api access token 取得 （1日1回）
#@app.route("/token")
def get_token():
    headers = {'Content-Type': 'application/json'}
    params = {'grantType': 'client_credentials', 'clientId': os.environ['clientId'], 'clientSecret': os.environ['clientSecret']}
    r = requests.post(COTOHA_publish_url, headers=headers, json=params)
    data = r.json()
    global access_token 
    access_token= data['access_token']
    return 'OK'

# LINEbot必要処理
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

# message reply
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    con = sqlite3.connect('tables.db')

    if ("使い方" in event.message.text):
        message = "私の名前はレオン！ 使いかたについて説明するね!"

    else:
        message = is_matched_full_text(event.message.text, con)
        if message == "":
            message = create_reply(event.message.text, con)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))
    con.close()

    return 'OK'

def is_matched_full_text(message, con):
    cur = con.cursor()
    reply_message = cur.execute('''SELECT REPLY_WORD FROM REPLIES WHERE TARGET_WORD=? ''', (message, )).fetchone()
    if reply_message is None:
        return ""
    else:
        return reply_message[0]

def create_reply(message, con):

    get_token()

    while True:
        # noby api で返信作成
        params_noby = {'text': message, 'app_key': API_KEY_noby}
        r = requests.get(ENDPOINT_noby, params=params_noby)
        data = r.json()
        response_noby = data["text"]

        # cotoha api でネガティブ判定 ネガティブならもう一度 noby api で作り直し
        params_cotoha = {'sentence': response_noby}
        headers = {'Content-Type': 'application/json;charset=UTF-8', 'Authorization':'Bearer '+access_token}
        r = requests.post(ENDPOINT_cotoha, headers=headers, json=params_cotoha)
        data = r.json()
        response_cotoha = data["result"]["sentiment"]

        if response_cotoha != "Negative":
            break

    return response_noby

#プッシュメッセージ  urlの末尾（messageの部分）を送る
@app.route("/send/<message>")
def push_manual_message(message):
    line_bot_api.broadcast([TextSendMessage(text=message)])

    return 'OK'

#プッシュメッセージ  messageデータベースからランダムに一つメッセージを選択して送る
@app.route("/send")
def push_message():
    con = sqlite3.connect('tables.db')
    cur = con.cursor()
    messages = cur.execute('''SELECT * FROM MESSAGES''').fetchall()
    line_bot_api.broadcast([TextSendMessage(text=random.choice(messages)[0])])
    con.close()

    return 'OK'

# def insert_to_replys_db(con, target_word, reply_word):
#     '''
#     '''
#     cur = con.cursor()
#     sql = '''INSERT INTO REPLIES (TARGET_WORD, REPLY_WORD) values (?, ?)'''
#     data = [target_word, reply_word]
#     cur.execute(sql, data)
#     con.commit()

# def check_user(con, user_id):
#     cur = con.cursor()

#     diary_mode_flags = cur.execute('''SELECT DIALY_MODE_FLAG FROM USERS WHERE USERID=? ''', (user_id,)).fetchone()

#     if diary_mode_flags == None:
#         cur.execute('''INSERT INTO USERS(USERID, DIALY_MODE_FLAG) VALUES(?, ?)''', (user_id, 0))
#         con.commit()
#         diary_mode_flag = 0
#     else :
#         diary_mode_flag = diary_mode_flags[0]
#     return diary_mode_flag

# #adminサイト
# @app.route("/admin")
# def form():
#     con = sqlite3.connect('tables.db')
#     cur = con.cursor()
#     messages = cur.execute(
#         '''SELECT MESSAGEID, MESSAGE FROM MESSAGES''').fetchall()
#     replies = cur.execute(
#         '''SELECT REPLYID, TARGET_WORD, REPLY_WORD FROM REPLIES''').fetchall()
#     con.close()

#     return render_template('form.html', messages=messages, replies=replies)

# #adminサイト  格言追加処理
# @app.route('/register', methods = ['POST'])
# def register():
#     if request.method == 'POST':
#         result = request.form
#         con = sqlite3.connect('tables.db')
#         cur = con.cursor()
#         messages = cur.execute('''INSERT INTO MESSAGES(MESSAGE) VALUES(?)''', (result.getlist('register')[0],))
#         con.commit()
#         con.close()
#         return form()

# #adminサイト  格言削除処理
# @app.route('/delete', methods = ['POST'])
# def delete_message():
#     if request.method == 'POST':
#         result = request.form
#         con = sqlite3.connect('tables.db')
#         cur = con.cursor()
#         messages = cur.execute(
#             '''DELETE FROM MESSAGES WHERE MESSAGEID = ?''', (result.getlist('message_id')[0],))
#         con.commit()
#         con.close()
#         return form()

# #adminサイト  特定のキーワードに対して特定のキーワードを返信する機能   追加処理
# @app.route('/keyword_add', methods = ['POST'])
# def add_keyword():
#     if request.method == 'POST':
#         result = request.form
#         con = sqlite3.connect('tables.db')
#         cur = con.cursor()
#         cur.execute('''INSERT INTO REPLIES(TARGET_WORD, REPLY_WORD) VALUES(?, ?)''', ((
#             result.getlist('user')[0]), (result.getlist('bot')[0])))
#         con.commit()
#         con.close()
#         return form()

# #adminサイト  特定のキーワードに対して特定のキーワードを返信する機能   削除処理
# @app.route('/keyword_del', methods = ['POST'])
# def delete_keyword():
#     if request.method == 'POST':
#         result = request.form
#         con = sqlite3.connect('tables.db')
#         cur = con.cursor()
#         cur.execute('''DELETE FROM REPLIES WHERE REPLYID = ? ''', (result.getlist('reply_id')[0],))
#         con.commit()
#         con.close()
#         return form()

if __name__ == "__main__":
    app.run()


# if diary_mode_flag == 1:
#     received_text = transralte_lang(received_text, "JA", "EN")

#     # request = requests.get("https://aws.random.cat/meow")
#     request = requests.get("https://dog.ceo/api/breeds/image/random")
#     request = request.json()

#     image_url = request['message']

#     diary_mode_flag = 0
#     line_bot_api.push_message(user_id, ImageSendMessage(original_content_url=image_url, preview_image_url=image_url))

#     message = "But that doesn't matter, look at my friends!"

#     cur = con.cursor()
#     # reset flag
#     cur.execute('''UPDATE USERS SET DIALY_MODE_FLAG = ? WHERE USERID = ?''', (0, user_id,))
#     con.commit()
