import json
import server
from odata_query.sqlalchemy import apply_odata_query

from aiohttp import web
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text

from .mrg_db import *
from .mrg_helpers import *

# Helper function to serialize model objects
def serialize(model):
    return {c.name: getattr(model, c.name) for c in model.__table__.columns}

# General CRUD Handlers

async def create_record(request, model):
    session = SessionLocal()
    data = await request.json()
    record = model(**data)
    session.add(record)
    session.commit()
    session.refresh(record)
    session.close()
    return web.Response(text=json.dumps(serialize(record)), content_type='application/json')

async def read_records(request, model):
    session = SessionLocal()
    query = session.query(model)
    query_string = request.query_string
   
    if "$filter" in request.rel_url.query:
        filt = request.rel_url.query["$filter"]
        if filt:
            query = apply_odata_query(query, filt)



    # Execute the query and convert results to JSON
    results = query.all()
    records = [serialize(result) for result in results]
    session.close()
    return json_response(records)
    

async def update_record(request, model, record_id):
    session = SessionLocal()
    data = await request.json()
    record = session.query(model).get(record_id)
    if not record:
        return web.Response(status=404, text="Record not found")

    for key, value in data.items():
        setattr(record, key, value)
    
    session.commit()
    session.refresh(record)
    session.close()
    return web.Response(text=json.dumps(serialize(record)), content_type='application/json')

async def delete_record(request, model, record_id):
    session = SessionLocal()
    record = session.query(model).get(record_id)
    if not record:
        return web.Response(status=404, text="Record not found")

    session.delete(record)
    session.commit()
    session.close()
    return web.Response(status=204)

# Dynamic route handlers

async def create_record_handler(request):
    model_name = request.match_info['model']
    model = globals().get(model_name.capitalize())
    if not model:
        return web.Response(status=404, text="Model not found")
    return await create_record(request, model)

async def read_records_handler(request):
    model_name = request.match_info['model']
    model = globals().get(model_name.capitalize())
    if not model:
        return web.Response(status=404, text="Model not found")
    return await read_records(request, model)

async def update_record_handler(request):
    model_name = request.match_info['model']
    model = globals().get(model_name.capitalize())
    if not model:
        return web.Response(status=404, text="Model not found")
    record_id = int(request.match_info['id'])
    return await update_record(request, model, record_id)

async def delete_record_handler(request):
    model_name = request.match_info['model']
    model = globals().get(model_name.capitalize())
    if not model:
        return web.Response(status=404, text="Model not found")
    record_id = int(request.match_info['id'])
    return await delete_record(request, model, record_id)

# Setting up the aiohttp application

app = server.PromptServer.instance.app #web.Application()
app.router.add_post('/mrgdata/{model}', create_record_handler)
app.router.add_get('/mrgdata/{model}', read_records_handler)
app.router.add_put('/mrgdata/{model}/{id}', update_record_handler)
app.router.add_delete('/mrgdata/{model}/{id}', delete_record_handler)

#web.run_app(app)
