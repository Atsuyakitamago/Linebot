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
import sys


ENDPOINT_noby = "https://www.cotogoto.ai/webapi/noby.json"
ENDPOINT_cotoha = "https://api.ce-cotoha.com/api/dev/nlp/v1/sentiment"
COTOHA_publish_url = "https://api.ce-cotoha.com/v1/oauth/accesstokens"
API_KEY_noby = os.environ['noby_key']
access_token = ""

def get_token():
    headers = {'Content-Type': 'application/json'}
    params = {'grantType': 'client_credentials', 'clientId': os.environ['clientId'], 'clientSecret': os.environ['clientSecret']}
    r = requests.post(COTOHA_publish_url, headers=headers, json=params)
    data = r.json()
    #print(data)
    global access_token 
    access_token= data['access_token']

    return 'OK'

# print(type(os.environ['clientId']))
# print(type(os.environ['clientSecret']))
#sys.exit()
get_token()
#sys.exit()

message = "こんにちは"

# noby api で返信作成
params_noby = {'text': message, 'app_key': API_KEY_noby}
r = requests.get(ENDPOINT_noby, params=params_noby)
# print(r.text)
# sys.exit()
data = r.json()
response_noby = data["text"]

# print(response_noby)
# sys.exit()

# cotoha api でネガティブ判定 ネガティブならもう一度 noby api で作り直し
params_cotoha = {'sentence': response_noby}
#print('Bearer '+access_token)
#sys.exit()
headers = {'Content-Type': 'application/json;charset=UTF-8', 'Authorization':'Bearer '+access_token}
r = requests.post(ENDPOINT_cotoha, headers=headers, json=params_cotoha)
data = r.json()
# print(type(r.text))
# sys.exit()

response_cotoha = data["result"]["sentiment"]

print(response_cotoha)


# curl -X POST -H "Content-Type:application/json;charset=UTF-8" -H "Authorization:Bearer aVBPojFcU52rE0ZgOvXqumm4wnfv" -d '{"sentence":"人生の春を謳歌しています"}' "https://api.ce-cotoha.com/api/dev/nlp/v1/sentiment"