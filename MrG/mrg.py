import json
import os
import sys
import time
import traceback
import yaml
import types
from nodes import NODE_CLASS_MAPPINGS as GLOBAL_NODE_CLASS_MAPPINGS
from nodes import NODE_DISPLAY_NAME_MAPPINGS as GLOBAL_NODE_DISPLAY_NAME_MAPPINGS
from server import PromptServer
from aiohttp import web
import websocket

from .mrgserver import *
from .database import *
from .api import *
from .prompt_api import *








NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
WEB_DIRECTORY = 'web'

create_tables()

def stalk_comfy(ws):
    try:
        while True:
            out = ws.recv()
            ws_queue_updated(1, out)
    except Exception as e:
        print("Socket error: ", e)
        traceback.print_exc()

ws = websocket.WebSocket()

def connect_to_server():
    while True:
        try:
            if ws.getstatus() != websocket.STATUS_NORMAL:
                ws.connect("ws://" + server_address + "/ws")
                print("Connected to server")
                stalk_comfy(ws)
        except:
            print("Could not connect to server")
        time.sleep(1)

threading.Thread(target=connect_to_server).start()
