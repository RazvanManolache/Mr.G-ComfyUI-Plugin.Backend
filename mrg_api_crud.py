import server
import json

from tokenize import String
from aiohttp import web

from .mrg_database import *
from .mrg_helpers import *
from .mrg_queue_processing import *
from .mrg_bundle import *

# package_repositories api - get, update, delete

@server.PromptServer.instance.routes.get('/mrg/package_repositories')
async def package_repositories_get(request):
    data = get_package_repositories().dicts()
    return json_response(list(data))

@server.PromptServer.instance.routes.put('/mrg/package_repositories')
@server.PromptServer.instance.routes.post('/mrg/package_repositories')
async def package_repositories_update(request):
    json_data = await request.json()    
    upsert_package_repository(json_data)
    return json_response({})

@server.PromptServer.instance.routes.delete('/mrg/package_repositories')
async def package_repositories_delete(request):
    data = await request.json()
    package = get_package_repository(data['uuid'])
    if package is None:
        return web.Response(status=404)
    if package.system:
        return web.Response(status=400, text="Cannot delete system package repository")
    
        

    delete_package_repository(data['uuid'])
    return web.Response(status=200)

# packages - get, update, delete

@server.PromptServer.instance.routes.get('/mrg/installed_packages')
async def installed_packages(request):
    data = get_packages().dicts()
    return json_response(list(data))

@server.PromptServer.instance.routes.put('/mrg/install_package')
async def install_package(request):
    json_data = await request.json()
    package_uuid = json_data['uuid']
    return json_response({})


@server.PromptServer.instance.routes.delete('/mrg/uninstall_package')
async def uninstall_package(request):
    data = await request.json()
    delete_package(data['uuid'])
    return web.Response(status=200)

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

# output_links api - get, update, delete

@server.PromptServer.instance.routes.get('/mrg/output_links_by_output')
async def output_links_by_output(request):
    data = await request.json()
    data = get_output_links_by_output(data['output_uuid']).dicts()
    return json_response(list(data))

@server.PromptServer.instance.routes.get('/mrg/output_links_by_selection_item')
async def output_links_by_selection_item(request):
    data = await request.json()
    page = 1
    pagesize = 25
    if "page" in data:
        page = data["page"]
    if "pagesize" in data:
        pagesize = data["pagesize"]
    data = get_output_links_by_selection_item(data['selection_item_uuid'], page, pagesize).dicts()
    return json_response(list(data))

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
