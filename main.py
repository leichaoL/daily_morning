import math
import os
import random
import time
from datetime import date, datetime

import requests
from notion_client import Client
from wechatpy import WeChatClient
from wechatpy.client.api import WeChatMessage, WeChatTemplate

today = datetime.now()
today_str = date.today().strftime("%Y/%m/%d")

start_date = os.environ['START_DATE']
city = os.environ['CITY']
birthday = os.environ['BIRTHDAY']

app_id = os.environ["APP_ID"]
app_secret = os.environ["APP_SECRET"]

user_id1 = os.environ["USER_ID1"]
user_id2 = os.environ["USER_ID2"]
template_id = os.environ["TEMPLATE_ID"]

notion_secret = os.environ["NOTION_SECRET"]


def get_weather():
    url = "http://autodev.openspeech.cn/csp/api/v2.1/weather?openId=aiuicus&clientType=android&sign=android&city=" + city
    res = requests.get(url).json()
    if datetime.now().hour > 4:
        wea = res['data']['list'][1]
        weather = wea['weather']
        low = wea['low']
        high = wea['high']
    else:
        wea = res['data']['list'][0]
        weather = wea['weather']
        low = wea['low']
        high = wea['high']
    return weather, math.floor(low), math.floor(high)

def get_count():
    delta = today - datetime.strptime(start_date, "%Y-%m-%d") 
    return delta.days + 1

def get_birthday():
    next = datetime.strptime(str(date.today().year) + "-" + birthday, "%Y-%m-%d")
    if next < datetime.now():
        next = next.replace(year=next.year + 1)
    return (next - today).days

def get_words():
    words = requests.get("https://api.shadiao.pro/chp")
    if words.status_code != 200:
        return get_words()
    return words.json()['data']['text']

def get_random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)

def get_notion_id():
    results = notion.search(query=today_str).get("results")
    if len(results) > 0:
        result = results[0]
        page_id = result["id"]
    return page_id

def get_notion_status():
    pages = notion.search(query=today_str).get("results")
    if len(pages) > 0:
        page = pages[0]
        page_status = page["properties"]["Published"]["checkbox"]
    else:
        page_status = "False"
    return page_status

def get_notion_text(page_id):
    blocks = notion.blocks.children.list(block_id = page_id)["results"]
    text = ""
    for block in blocks:
        type = block["type"]
        if len(block[type]["rich_text"]) == 0:
            text = text + "\n"
        else:
            text = text + "\n" + block[type]["rich_text"][0]["plain_text"]
    return text

def update():
    old_status = get_notion_status()
    while (datetime.now().hour >= 12) & (datetime.now().hour < 18):
        new_status = get_notion_status()
        if (new_status != old_status) & (new_status == True):
            old_status = new_status
            sendMsg()
        elif (new_status != old_status) & (new_status == False):
            old_status = new_status
        time.sleep(5)

def sendMsg():
    client = WeChatClient(app_id, app_secret)
    wm = WeChatMessage(client)
    wea, low, high = get_weather()
    page_id = get_notion_id()
    text = get_notion_text(page_id)
    data = {"city":{"value":city},"weather":{"value":wea},"low":{"value":low},"high":{"value":high},"love_days":{"value":get_count()},"birthday_left":{"value":get_birthday()}, "text":{"value":text}}
    res1 = wm.send_template(user_id1, template_id, data)
    res2 = wm.send_template(user_id2, template_id, data)
    return res1, res2


notion = Client(auth=notion_secret)
update()
