import os
import sys
import asyncio
import traceback
from server import *

import uuid
import urllib
import json

from io import BytesIO
import aiohttp 
from aiohttp import web

import comfy.model_management
from .helpers import *

from .prompt_api import *
# want to handle more cases for websockets, don't want to work too hard to get it
async def mrg_handle_socket_request(sid, data):
    self = server.PromptServer.instance        
    result = process_socket_api_request(sid, data)
    if result is not None:
        await self.send(result["type"], result["result"], sid)
   
@server.PromptServer.instance.routes.get("/test")
async def test(request):
    return web.Response(text="Hello")

@server.PromptServer.instance.routes.get("/mrg_ws")
async def mrg_websocket_handler(request):
            self = server.PromptServer.instance
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            sid = request.rel_url.query.get('clientId', '')
            if sid:
                # Reusing existing session, remove old
                self.sockets.pop(sid, None)
            else:
                sid = uuid.uuid4().hex

            self.sockets[sid] = ws

            try:
                # Send initial state to the new client
                await self.send("status", { "status": self.get_queue_info(), 'sid': sid }, sid)
                # On reconnect if we are the currently executing client send the current node
                if self.client_id == sid and self.last_node_id is not None:
                    await self.send("executing", { "node": self.last_node_id }, sid)
                    
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.ERROR:
                        print('ws connection closed with exception %s' % ws.exception())
                    else:
                        await mrg_handle_socket_request(sid, msg.data)
            finally:
                self.sockets.pop(sid, None)
            return ws
