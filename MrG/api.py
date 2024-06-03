from tokenize import String
from .queue_processing import *
import server

import json
from aiohttp import web
from .database import *
from .helpers import *

from .bundle import *





@server.PromptServer.instance.routes.get('/mrg/bundle')
async def picker_texts_update(request):
    bundle_javascript_files("/ComfyUI/web/mrg/app/", "/bundle.js")
    return web.HTTPTemporaryRedirect('app/bundle.js')

# api api - get, update

@server.PromptServer.instance.routes.get('/mrg/api')
async def api_get(request):
    data = get_apis().dicts()
    return json_response(list(data))

@server.PromptServer.instance.routes.put('/mrg/api')
@server.PromptServer.instance.routes.post('/mrg/api')
async def api_update(request):
    json_data = await request.json()
    upsert_api(json_data)
    await send_socket_message_internal("apiUpdated", {}, None)
    return json_response({})

@server.PromptServer.instance.routes.delete('/mrg/api')
async def api_delete(request):
    data = await request.json()
    delete_api(data['uuid'])
    await send_socket_message_internal("apiUpdated", {}, None)
    return web.Response(status=200)

# jobs api - get, update

@server.PromptServer.instance.routes.get('/mrg/jobs')
async def jobs_get(request):
    data = get_jobs().dicts()
    return json_response(list(data))

@server.PromptServer.instance.routes.put('/mrg/jobs')
@server.PromptServer.instance.routes.post('/mrg/jobs')
async def jobs_update(request):
    json_data = await request.json()
    upsert_job(json_data)
    return json_response({})

@server.PromptServer.instance.routes.delete('/mrg/jobs')
async def jobs_delete(request):
    data = await request.json()
    delete_job(data['uuid'])
    return web.Response(status=200)


# settings api - get, update

@server.PromptServer.instance.routes.get('/mrg/settings')
async def settings_get(request):
    data = get_settings().dicts()
    return json_response(list(data))

@server.PromptServer.instance.routes.put('/mrg/settings')
@server.PromptServer.instance.routes.post('/mrg/settings')
async def picker_texts_update(request):    
    json_data = await request.json()
    upsert_setting(json_data)
    return json_response({})


# workflows api - get, update, delete

@server.PromptServer.instance.routes.get('/mrg/workflow')
async def workflow_get(request):
    if "uuid" in request.rel_url.query:
        uuid = request.rel_url.query["uuid"]
    data = get_workflow(uuid)
    data = model_to_dict(data)
    return json_response(data)

@server.PromptServer.instance.routes.get('/mrg/workflows')
async def workflows_get(request):
    data = get_workflows_full().dicts()
    return json_response(list(data))

@server.PromptServer.instance.routes.put('/mrg/workflows')
@server.PromptServer.instance.routes.post('/mrg/workflows')
async def workflows_update(request):    
    json_data = await request.json()
    upsert_workflow(json_data)
    return json_response({})

@server.PromptServer.instance.routes.delete('/mrg/workflows')
async def workflows_delete(request):   
    data = await request.json()
    delete_workflow(data['uuid'])
    return web.Response(status=200)



# workflow categories api - get, update, delete

@server.PromptServer.instance.routes.get('/mrg/categories')
async def categories_get(request):
    data = get_categories().dicts()
    return json_response(list(data))

@server.PromptServer.instance.routes.get('/mrg/categories_tree')
async def categories_get_tree(request):
    data = list(get_categories().dicts())
   
    for node in data:
        node["children"] = []
    data.sort(key=lambda x: x["order"])
    nodes = dict((e["uuid"], e) for e in data)
    
    for node in data:
        if node["parent_uuid"]:
            nodes[node["parent_uuid"]]["children"].append(nodes[node["uuid"]])
    for node in nodes.values():
        if len(node["children"])==0:
            node["leaf"] = True
    roots = [n for n in nodes.values() if not n["parent_uuid"]]
   
    root = Empty()
    root["uuid"] = "root"
    root["children"] = roots
    return json_response(root)

@server.PromptServer.instance.routes.put('/mrg/categories')
@server.PromptServer.instance.routes.post('/mrg/categories')
async def categories_update(request):    
    json_data = await request.json()
    remove_not_needed_properties(categories, json_data)
    response = upsert_category(json_data)
   
    return json_response({})

@server.PromptServer.instance.routes.delete('/mrg/categories')
async def categories_delete(request):   
    data = await request.post()
    delete_category(data['uuid'])
    return web.Response(status=200)





# selection_item api - get all, get specific, update, delete

@server.PromptServer.instance.routes.get('/mrg/selection_items_types')
async def selection_items_types(request):
    for item in ComfyTypeMappings:
        item.refresh_data()
        item['db_data'] =  list(get_selection_items(item['field'], item['cls']).dicts())
    return json_response(list(ComfyTypeMappings))

@server.PromptServer.instance.routes.get('/mrg/selection_item')
async def selection_item_get(request):
    if "uuid" in request.rel_url.query:
        uuid = request.rel_url.query["uuid"]
    data = get_selection_item(uuid)
    data = model_to_dict(data)
    return json_response(data)

@server.PromptServer.instance.routes.get('/mrg/selection_items')
async def selection_items_get(request):
    field = ""
    node = ""
    if "field" in request.rel_url.query:
        field = request.rel_url.query["field"]
    if "node" in request.rel_url.query:
        node = request.rel_url.query["node"]
    db_data = selection_item_get_internal(field, node)
    return json_response(db_data)

@server.PromptServer.instance.routes.put('/mrg/selection_items')
@server.PromptServer.instance.routes.post('/mrg/selection_items')
async def selection_items_update(request):  
    json_data = await request.json()
    db_data = upsert_selection_items(json_data)
    return json_response(db_data)

@server.PromptServer.instance.routes.delete('/mrg/selection_items')
async def selection_items_delete(request):   
    #TODO: also delete item
    data = await request.post()
    delete_selection_items(data['uuid'])
    return web.Response(status=200)


