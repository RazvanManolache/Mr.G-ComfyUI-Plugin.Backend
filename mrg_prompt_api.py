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


from .mrg_helpers import *
from .mrg_queue_processing import *





@server.PromptServer.instance.routes.get('/mrg/apis_client')
async def get_api_actions(request):    
    return json_response(get_api_actions_def_clean())


@server.PromptServer.instance.routes.get("/mrgapi/{ident}")
async def handle_api_definition_request(request):
    ident = request.match_info['ident']
    return json_response(get_api_action_def(ident))

@server.PromptServer.instance.routes.post("/mrgapi/{ident}")
async def handle_api_request(request):
    ident = request.match_info['ident']
    client_id = None
    if "ClientId" in request.headers.keys():
        client_id = request.headers["ClientId"]

    if client_id is None:
        return json_response({"error":"Please provide client_id header."})

    if not ident:
        return json_response({})
    data = get_apis().dicts()    
    data = [x for x in data if x["enabled"]]
    data = [x for x in data if x["endpoint"]== ident or x["uuid"]== ident]
    if(len(data)!=1):
        return json_response({})
    apis = get_definition_for_api(data)
    if(len(apis)!=1):
        return json_response({})
    params = await request.json()
        
    return json_response(process_api_request(client_id, apis[0], params))

@server.PromptServer.instance.routes.post('/mrg_prompt')
async def mrg_prompt(request):
    json_data = await request.json()
    client_id = json_data["client_id"]
    prompt = json_data["prompt"]
    result = enqueue_prompt_by_type(client_id, prompt)
    if "error" in result:
        return json_response(result)
    
    queued_run = insert_queue_run(result)
    check_queue_runs()
    new_prompt = create_prompt_for_step(queued_run, result["total"]+1, True)
    response = {}
    response["success"] = "OK"
    response["run_uuid"] = str(result["uuid"])
    response["prompt"] = new_prompt
    response["changes"] = get_values_and_pos_from_prompt(new_prompt)    
    return json_response(response)


        
