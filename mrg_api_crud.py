import server
import json

from tokenize import String
from aiohttp import web

from . import mrg_database
from . import mrg_helpers 
from . import mrg_queue_processing 
from . import mrg_bundle

# package_repositories api - get, update, delete

@server.PromptServer.instance.routes.get('/mrg/package_repositories')
async def package_repositories_get(request):
    data = mrg_database.get_package_repositories().dicts()
    return mrg_helpers.json_response(list(data))

@server.PromptServer.instance.routes.put('/mrg/package_repositories')
@server.PromptServer.instance.routes.post('/mrg/package_repositories')
async def package_repositories_update(request):
    json_data = await request.json()    
    mrg_database.upsert_package_repository(json_data)
    return mrg_helpers.json_response({})

@server.PromptServer.instance.routes.delete('/mrg/package_repositories')
async def package_repositories_delete(request):
    data = await request.json()
    package = mrg_database.get_package_repository(data['uuid'])
    if package is None:
        return web.Response(status=404)
    if package.system:
        return web.Response(status=400, text="Cannot delete system package repository")
    
        

    mrg_database.delete_package_repository(data['uuid'])
    return web.Response(status=200)



# api api - get, update

@server.PromptServer.instance.routes.get('/mrg/api')
async def api_get(request):
    data = mrg_database.get_apis().dicts()
    return mrg_helpers.json_response(list(data))

@server.PromptServer.instance.routes.put('/mrg/api')
@server.PromptServer.instance.routes.post('/mrg/api')
async def api_update(request):
    json_data = await request.json()
    mrg_database.upsert_api(json_data)
    await mrg_helpers.send_socket_message_internal("apiUpdated", {}, None)
    return mrg_helpers.json_response({})

@server.PromptServer.instance.routes.delete('/mrg/api')
async def api_delete(request):
    data = await request.json()
    mrg_database.delete_api(data['uuid'])
    await mrg_helpers.send_socket_message_internal("apiUpdated", {}, None)
    return web.Response(status=200)

# jobs api - get, update

@server.PromptServer.instance.routes.get('/mrg/jobs')
async def jobs_get(request):
    data = mrg_database.get_jobs().dicts()
    return mrg_helpers.json_response(list(data))

@server.PromptServer.instance.routes.put('/mrg/jobs')
@server.PromptServer.instance.routes.post('/mrg/jobs')
async def jobs_update(request):
    json_data = await request.json()
    mrg_database.upsert_job(json_data)
    return mrg_helpers.json_response({})

@server.PromptServer.instance.routes.delete('/mrg/jobs')
async def jobs_delete(request):
    data = await request.json()
    mrg_database.delete_job(data['uuid'])
    return web.Response(status=200)


# settings api - get, update

@server.PromptServer.instance.routes.get('/mrg/settings')
async def settings_get(request):
    data = mrg_database.get_settings().dicts()
    return mrg_helpers.json_response(list(data))

@server.PromptServer.instance.routes.put('/mrg/settings')
@server.PromptServer.instance.routes.post('/mrg/settings')
async def picker_texts_update(request):    
    json_data = await request.json()
    mrg_database.upsert_setting(json_data)
    return mrg_helpers.json_response({})

# output_links api - get, update, delete

@server.PromptServer.instance.routes.get('/mrg/output_links_by_output')
async def output_links_by_output(request):
    data = await request.json()
    data = mrg_database.get_output_links_by_output(data['output_uuid']).dicts()
    return mrg_helpers.json_response(list(data))

@server.PromptServer.instance.routes.get('/mrg/output_links_by_selection_item')
async def output_links_by_selection_item(request):
    data = await request.json()
    page = 1
    pagesize = 25
    if "page" in data:
        page = data["page"]
    if "pagesize" in data:
        pagesize = data["pagesize"]
    data = mrg_database.get_output_links_by_selection_item(data['selection_item_uuid'], page, pagesize).dicts()
    return mrg_helpers.json_response(list(data))

# workflows api - get, update, delete

@server.PromptServer.instance.routes.get('/mrg/workflow')
async def workflow_get(request):
    if "uuid" in request.rel_url.query:
        uuid = request.rel_url.query["uuid"]
    data = mrg_database.get_workflow(uuid)
    data = mrg_database.model_to_dict(data)
    return mrg_helpers.json_response(data)

@server.PromptServer.instance.routes.get('/mrg/workflows')
async def workflows_get(request):
    data = mrg_database.get_workflows_full().dicts()
    return mrg_helpers.json_response(list(data))

@server.PromptServer.instance.routes.put('/mrg/workflows')
@server.PromptServer.instance.routes.post('/mrg/workflows')
async def workflows_update(request):    
    json_data = await request.json()
    mrg_database.upsert_workflow(json_data)
    return mrg_helpers.json_response({})

@server.PromptServer.instance.routes.delete('/mrg/workflows')
async def workflows_delete(request):   
    data = await request.json()
    mrg_database.delete_workflow(data['uuid'])
    return web.Response(status=200)

# workflow categories api - get, update, delete

@server.PromptServer.instance.routes.get('/mrg/categories')
async def categories_get(request):
    data = mrg_database.get_categories().dicts()
    return mrg_helpers.json_response(list(data))

@server.PromptServer.instance.routes.put('/mrg/categories')
@server.PromptServer.instance.routes.post('/mrg/categories')
async def categories_update(request):    
    json_data = await request.json()
    mrg_helpers.remove_not_needed_properties(mrg_database.categories, json_data)
    response = mrg_database.upsert_category(json_data)
   
    return mrg_helpers.json_response({})

@server.PromptServer.instance.routes.delete('/mrg/categories')
async def categories_delete(request):   
    data = await request.post()
    mrg_database.delete_category(data['uuid'])
    return web.Response(status=200)
