import json
import os
import sys
import time
import traceback
import yaml
import types
import threading
import websocket

from nodes import NODE_CLASS_MAPPINGS as GLOBAL_NODE_CLASS_MAPPINGS
from nodes import NODE_DISPLAY_NAME_MAPPINGS as GLOBAL_NODE_DISPLAY_NAME_MAPPINGS
from server import PromptServer
from aiohttp import web


from . import mrg_server
from . import mrg_api 
from . import mrg_api_crud
from . import mrg_prompt_api
from . import mrg_queue_processing

#from .mrg_odata import *








NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
WEB_DIRECTORY = 'web'



def stalk_comfy(ws):
    try:
        while True:
            out = ws.recv()
            mrg_queue_processing.ws_queue_updated(1, out)
    except Exception as e:
        print("Socket error: ", e)
        traceback.print_exc()

ws = websocket.WebSocket()

def connect_to_server():
    while True:
        try:
            if ws.getstatus() != websocket.STATUS_NORMAL:
                ws.connect("ws://" + mrg_queue_processing.server_address + "/ws")
                print("Connected to server")
                stalk_comfy(ws)
        except:
            print("Could not connect to server")
        time.sleep(1)

threading.Thread(target=connect_to_server).start()
