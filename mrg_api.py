from requests.sessions import merge_hooks
import server
import json

from tokenize import String
from aiohttp import web

from . import mrg_database
from . import mrg_helpers
from . import mrg_queue_processing
from . import mrg_bundle 
from . import mrg_packages





@server.PromptServer.instance.routes.get('/mrg/bundle')
async def picker_texts_update(request):
    mrg_bundle.bundle_javascript_files("/ComfyUI/web/mrg/app/", "bundle.js")
    return web.HTTPTemporaryRedirect('app/bundle.js')

@server.PromptServer.instance.routes.get('/mrg/categories_tree')
async def categories_get_tree(request):
    data = list(mrg_database.get_categories())
   
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
   
    root = mrg_helpers.Empty()
    root["uuid"] = "root"
    root["children"] = roots
    return mrg_helpers.json_response(root)



# packages - get, update, delete

@server.PromptServer.instance.routes.get('/mrg/available_packages')
async def available_packages(request):
    packages = mrg_packages.get_available_packages_from_repositories()
    return mrg_helpers.json_response(list([mrg_database.model_to_dict(package) for package in packages]))

@server.PromptServer.instance.routes.post('/mrg/available_packages')
async def install_package(request):
    json_data = await request.json()
    package_uuid = json_data['uuid']
    return mrg_helpers.json_response({})

@server.PromptServer.instance.routes.get('/mrg/installed_packages')
async def installed_packages(request):
    data = mrg_database.get_packages().dicts()
    return mrg_helpers.json_response(list(data))

@server.PromptServer.instance.routes.delete('/mrg/uninstall_package')
async def uninstall_package(request):
    data = await request.json()
    mrg_database.delete_package(data['uuid'])
    return web.Response(status=200)


# selection_item api - get all, get specific, update, delete

@server.PromptServer.instance.routes.get('/mrg/selection_items_types')
async def selection_items_types(request):
    for item in mrg_helpers.ComfyTypeMappings:
        item.refresh_data()
        item['db_data'] =  list(mrg_helpers.selection_item_get_internal(item['field'], item['cls']))
    return mrg_helpers.json_response(list(mrg_helpers.ComfyTypeMappings))

@server.PromptServer.instance.routes.get('/mrg/selection_item')
async def selection_item_get(request):
    if "uuid" in request.rel_url.query:
        uuid = request.rel_url.query["uuid"]
    data = mrg_database.get_selection_item(uuid)
    data = mrg_database.model_to_dict(data)
    return mrg_helpers.json_response(data)

@server.PromptServer.instance.routes.get('/mrg/selection_items')
async def selection_items_get(request):
    field = ""
    node = ""
    if "field" in request.rel_url.query:
        field = request.rel_url.query["field"]
    if "node" in request.rel_url.query:
        node = request.rel_url.query["node"]
    db_data = mrg_helpers.selection_item_get_internal(field, node)
    return mrg_helpers.json_response(db_data)

@server.PromptServer.instance.routes.put('/mrg/selection_items')
@server.PromptServer.instance.routes.post('/mrg/selection_items')
async def selection_items_update(request):  
    json_data = await request.json()
    db_data = mrg_database.upsert_selection_items(json_data)
    return mrg_helpers.json_response(db_data)

@server.PromptServer.instance.routes.delete('/mrg/selection_items')
async def selection_items_delete(request):   
    #TODO: also delete item
    data = await request.post()
    mrg_database.delete_selection_items(data['uuid'])
    return web.Response(status=200)


# output - get, edit, delete
@server.PromptServer.instance.routes.get('/mrg/output')
async def output_get(request): 
    if "uuid" in request.rel_url.query:
        uuid = request.rel_url.query["uuid"]
    data = mrg_database.get_output(uuid)
    data = mrg_database.model_to_dict(data)
    return mrg_helpers.json_response(data)

@server.PromptServer.instance.routes.post('/mrg/output_download')
async def output_download(request):
    data = await request.json()
    output = mrg_database.get_output(data['uuid'])
    #TODO: work on download
    return web.FileResponse(output['path'])

#example request
#http://127.0.0.1:8188/mrg/outputs?_dc=1722268183209&page=1&start=0&limit=25
@server.PromptServer.instance.routes.get('/mrg/outputs')
async def outputs_get(request):
    page = 1
    limit = 25
    start = 0
    filt = ""
    if "page" in request.rel_url.query:
        page = int(request.rel_url.query["page"])
    if "limit" in request.rel_url.query:
        limit = int(request.rel_url.query["limit"])
    if "start" in request.rel_url.query:
        start = int(request.rel_url.query["start"])
    if "filter" in request.rel_url.query:
        filt = request.rel_url.query["filter"]
    orderby = ""
    order_dir = "ASC"
    
    data = mrg_database.get_outputs_paginated(page, limit, orderby, order_dir, filt)
    return mrg_helpers.json_response(data)

# put http://127.0.0.1:8188/mrg/outputs/2f81cc46-fb33-4815-8c48-e83c9130b2e8?_dc=1726219613667
@server.PromptServer.instance.routes.put('/mrg/outputs/{uuid}')
async def output_update(request):
    uuid = request.match_info['uuid']
    json_data = await request.json()
    db_data = mrg_database.update_output(uuid, json_data)
    return mrg_helpers.json_response(db_data)

@server.PromptServer.instance.routes.get('/mrg/batch_requests')
async def batch_requests_get(request):
    page = 1
    limit = 25
    start = 0
    filt = ""
    if "page" in request.rel_url.query:
        page = int(request.rel_url.query["page"])
    if "limit" in request.rel_url.query:
        limit = int(request.rel_url.query["limit"])
    if "start" in request.rel_url.query:
        start = int(request.rel_url.query["start"])
    if "filter" in request.rel_url.query:
        filt = request.rel_url.query["filter"]
    orderby = ""
    order_dir = "ASC"
    
    data = mrg_database.get_batch_requests_paginated(page, limit, orderby, order_dir, filt)
    return mrg_helpers.json_response(data)
    
    


