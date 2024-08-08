import datetime
import server
import execution
import json
import copy
import aiohttp
import mimetypes
import asyncio
import random

from types import SimpleNamespace
from app.user_manager import UserManager
import pylab as pl
from re import L
from tokenize import String
from doctest import debug
from pickle import NONE
from execution import *


from . import mrg_helpers
from . import mrg_queue_processing
from . import mrg_database





@server.PromptServer.instance.routes.get('/mrg/apis_client')
async def get_api_actions(request):    
    return mrg_helpers.json_response(mrg_queue_processing.get_api_actions_def_clean())


@server.PromptServer.instance.routes.get("/mrgapi/{ident}")
async def handle_api_definition_request(request):
    ident = request.match_info['ident']
    return mrg_helpers.json_response(mrg_queue_processing.get_api_action_def(ident))

@server.PromptServer.instance.routes.post("/mrgapi/{ident}")
async def handle_api_request(request):
    ident = request.match_info['ident']
    client_id = None
    if "ClientId" in request.headers.keys():
        client_id = request.headers["ClientId"]

    if client_id is None:
        return mrg_helpers.json_response({"error":"Please provide client_id header."})

    if not ident:
        return mrg_helpers.json_response({})
    data = mrg_database.get_apis().dicts()    
    data = [x for x in data if x["enabled"]]
    data = [x for x in data if x["endpoint"]== ident or x["uuid"]== ident]
    if(len(data)!=1):
        return mrg_helpers.json_response({})
    apis = mrg_queue_processing.get_definition_for_api(data)
    if(len(apis)!=1):
        return mrg_helpers.json_response({})
    params = await request.json()
        
    return mrg_helpers.json_response(mrg_queue_processing.process_api_request(client_id, apis[0], params))

@server.PromptServer.instance.routes.post('/mrg_prompt')
async def mrg_prompt(request):
    json_data = await request.json()
    client_id = json_data["client_id"]
    prompt = json_data["prompt"]
    result = mrg_queue_processing.enqueue_prompt_by_type(client_id, prompt)
    if "error" in result:
        return mrg_helpers.json_response(result)
    
    batch_request = mrg_database.insert_batch_request(result)
    mrg_queue_processing.check_batch_requests()
    new_prompt = mrg_queue_processing.create_prompt_for_step(batch_request, result["total"]+1, True)
    response = {}
    response["success"] = "OK"
    response["batch_request_uuid"] = str(result["uuid"])
    response["prompt"] = new_prompt
    response["changes"] = mrg_queue_processing.get_values_and_pos_from_prompt(new_prompt)    
    return mrg_helpers.json_response(response)


        
