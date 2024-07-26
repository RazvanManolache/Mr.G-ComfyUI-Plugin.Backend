import server
import json

from tokenize import String
from aiohttp import web

from .mrg_database import *
from .mrg_helpers import *
from .mrg_queue_processing import *
from .mrg_bundle import *





@server.PromptServer.instance.routes.get('/mrg/bundle')
async def picker_texts_update(request):
    bundle_javascript_files("/ComfyUI/web/mrg/app/", "/bundle.js")
    return web.HTTPTemporaryRedirect('app/bundle.js')

@server.PromptServer.instance.routes.get('/mrg/categories_tree')
async def categories_get_tree(request):
    data = list(get_categories())
   
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


