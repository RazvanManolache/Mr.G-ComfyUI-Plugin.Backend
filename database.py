import datetime
from re import T
from peewee import *
from playhouse.shortcuts import model_to_dict



dbName = "mrg.db"

database = SqliteDatabase(dbName, pragmas={
    'journal_mode': 'wal',
    'cache_size': 10000,  # 10000 pages, or ~40MB
    'foreign_keys': 1,  # Enforce foreign-key constraints
})

class BaseModel(Model):
    class Meta:
        database = database


class BaseModelWithUUID(BaseModel):
    uuid = TextField(primary_key=True)

#selection_item - data for all combos

class selection_item(BaseModelWithUUID):
    name = TextField()
    alias = TextField()
    comfy_name = TextField(null=True)
    description = TextField(null=True)
    comments = TextField(null=True)
    tags = TextField(null=True)
    times_used = IntegerField(default=0)
    rating = SmallIntegerField(default=0)
    text = TextField()
    hidden = BooleanField(default=False)
    favorite = BooleanField(default=False)
    field = TextField()
    field_type = TextField()
    node_type = TextField()
    path = TextField(null=True)
    image = TextField(null=True)
    thumbnail = TextField(null=True)
    


def get_selection_item(uuid):
    return selection_item.get_by_id(uuid)
    
def get_selection_items(field_type, node_type):
    if(node_type=='*'):
        return selection_item.select().where(selection_item.field_type == field_type)
    return selection_item.select().where(selection_item.field_type == field_type, selection_item.node_type == node_type)


def upsert_selection_items(sel_item):
    existing_row = None
    try:
        existing_row = selection_item.get_by_id(sel_item["uuid"])
    except: 
        pass
    if existing_row == None:
        selection_item.insert(sel_item).execute()
        return sel_item
    else:
        for key in sel_item.keys():
            setattr(existing_row,key,sel_item[key])
        existing_row.save()
        return model_to_dict(existing_row)
    
    #selection_item.insert(sel_item).on_conflict(conflict_target=(sel_item["uuid"],),update=sel_item).execute()

def delete_selection_items(uuid):
    selection_item.delete_by_id(uuid)
    




# categories - categories for workflows

class categories(BaseModelWithUUID):
    name = TextField()
    icon = TextField()
    description = TextField(null=True)
    system = BooleanField(default=False)
    order = IntegerField(default=1)
    parent_uuid = ForeignKeyField('self',null=True,on_delete='CASCADE', backref='categories')

def get_categories():
    return categories.select()

def get_category(uuid):
    try:
        return categories.get_by_id(uuid)
    except:
        pass
    return None

def upsert_category(category):
    cat = get_category(category["uuid"])
    if cat is not None:    
        if(cat.system == True):
            return
    categories.insert(category).on_conflict(conflict_target=(categories.uuid,),update=category).execute()
    return get_category(category["uuid"])

def delete_category(uuid):
    cat =  categories.get_by_id(uuid)
    if(cat is None):
        return
    if(cat.system == True):
        return
    categories.delete_by_id(uuid)

    

# workflows - all saved workflows

class workflows(BaseModelWithUUID):
    name = TextField()
    description = TextField(null=True)

    tags = TextField(null=True)    
    rating = SmallIntegerField(default=0)
    order = IntegerField(default=1)
    favourite = BooleanField(default=False)
    
    category_uuid = ForeignKeyField(categories, null=True,on_delete='SET NULL', backref='category')

    hidden = BooleanField(default=False)
    system = BooleanField(default=False)
    times_used = IntegerField(default=0)

    contents = TextField(null=True)
    nodes_values = TextField(null=True)
    settings = TextField(null=True)
    run_values =  TextField(null=True)

    create_date = DateTimeField(null=False)
    update_date = DateTimeField(null=False)
    

def get_workflows_short():
    return workflows.select()

def get_workflows_full():
    return workflows.select()

def get_workflow(uuid):
    return workflows.select().where(workflows.uuid == uuid).execute()[0]

def delete_workflow(uuid):
    workflows.delete_by_id(uuid)

def upsert_workflow(workflow):
    #try to insert, if it fails, update
    
    existing_row = None
    try:
        existing_row = workflows.get_by_id(workflow["uuid"])
    except:
        pass
    if existing_row == None:
        workflows.insert(workflow).execute()
        return get_workflow(workflow["uuid"])
    else:
        for key in workflow.keys():
            setattr(existing_row,key,workflow[key])
        existing_row.save()
        return model_to_dict(existing_row)

    # workflows.insert(workflow).on_conflict(conflict_target=(workflows.uuid,),update=workflow).execute()
    # return get_workflow(workflow["uuid"])


class workflow_extenders(BaseModelWithUUID):
    name = TextField()
    description = TextField(null=True)
    workflows = TextField(null=True)    
    create_date = DateTimeField(null=False)
    update_date = DateTimeField(null=False)
    enabled = BooleanField(default=True)
    tags = TextField(null=True)
    runs = IntegerField(default=0)
    
class api(workflow_extenders):
    endpoint = TextField(null=False)
    parameters = TextField(null=True)

def update_api_runs(uuid, runs):
    api.update(runs=runs).where(api.uuid == uuid).execute()
        

def get_api(uuid):
    return api.get_by_id(uuid)

def get_apis():
    return api.select()

def get_apis_by_workflow(workflow_uuid):
    return api.select().where(api.workflow_uuid == workflow_uuid)

def get_apis_by_preset(preset_uuid):
    return api.select().where(api.preset_uuid == preset_uuid)

def delete_api(uuid):
    api.delete_by_id(uuid)
    
def insert_api(api):
    now = datetime.datetime.now()
    api["create_date"] = now
    api["update_date"] = now
    api.insert(api).execute()
    return get_api(api["uuid"])

    
def update_api(api_ob):
    api_ob.update_date = datetime.datetime.now()

    api_ob.save()
    return get_api(api.uuid)

def upsert_api(api_ob):
    existing_row = None
    try:
        existing_row = api.get_by_id(api_ob["uuid"])
    except:
        pass
    if existing_row == None:
        api_ob["create_date"] = datetime.datetime.now()
        api_ob["update_date"] = datetime.datetime.now()        
        api.insert(api_ob).execute()
        return api
    else:
        for key in api_ob.keys():
            setattr(existing_row,key,api_ob[key])
        api_ob["update_date"] = datetime.datetime.now()
        existing_row.save()
        return model_to_dict(existing_row)

class jobs (workflow_extenders):
    cron = TextField(null=False)

def update_job_runs(uuid, runs):
    jobs.update(runs=runs).where(jobs.uuid == uuid).execute()

def get_job(uuid):
    return jobs.get_by_id(uuid)

def get_jobs():
    return jobs.select()

def delete_job(uuid):
    jobs.delete_by_id(uuid)
    
def insert_job(job):
    jobs.insert(job).execute()
    return get_job(job["uuid"])

def update_job(job):    
    job.save()
    return get_job(job.uuid)

def upsert_job(job):
    existing_row = None
    try:
        existing_row = jobs.get_by_id(job["uuid"])
    except:
        pass
    if existing_row == None:
        jobs.insert(job).execute()
        return job
    else:
        for key in job.keys():
            setattr(existing_row,key,job[key])
        existing_row.save()
        return model_to_dict(existing_row)
    

# queue_runs - queue

class queue_runs(BaseModelWithUUID):
    workflow_uuid = ForeignKeyField(workflows, null=True,on_delete='SET NULL', backref='workflow') #saved
    api_uuid = ForeignKeyField(api, null=True,on_delete='SET NULL', backref='api') #saved
    job_uuid = ForeignKeyField(jobs, null=True,on_delete='SET NULL', backref='job') #saved
    secondary_uuid = TextField(null=True) #saved
    client_id = TextField(null=True) #saved
    name = TextField(null=True) #saved
    tags = TextField(null=True) #saved
    run_settings = TextField(null=False) #saved
    total = IntegerField(null=False) #saved
    contents = TextField(null=True) #saved
    create_date = DateTimeField(null=False) #saved
    run_type = TextField(null = False) #saved
    current = IntegerField(null=False) #saved on creation
    order = BigIntegerField(null=False) #saved on creation
    status = TextField(null=True) #saved on creation      
    start_date = DateTimeField(null=True) #saved on creation 
    update_date = DateTimeField(null=False) #saved on creation 
    end_date = DateTimeField(null=True) #saved on creation 
    nodes_values = TextField(null=True) #wip
    run_values =  TextField(null=True) #saved
    current_values = TextField(null=True) #need to update

def get_queue_run_status_for_uuid_list(uuids):
    return queue_runs.select(queue_runs.uuid, queue_runs.status).where(queue_runs.uuid.in_(uuids)).dicts().execute()

def get_queue_runs_max_order():
    return queue_runs.select(fn.MAX(queue_runs.order)).scalar()

def get_queue_runs_min_order():
    return queue_runs.select(fn.MIN(queue_runs.order)).scalar()

def get_queue_runs_by_status(status):
    return queue_runs.select().where(queue_runs.status == status).order_by(queue_runs.order)

def get_queue_runs_by_statuses(statuses):
    return queue_runs.select().where(queue_runs.status.in_(statuses)).order_by(queue_runs.order)

def pause_queued_run(uuid):
    #only if it is queued or running
    run = queue_runs.get_by_id(uuid)
    if run.status in ["queued", "running"]:
        queue_runs.update(status="paused").where(queue_runs.uuid == uuid).execute()
    
def cancel_queued_run(uuid):
    #only if it is queued or running or paused
    run = queue_runs.get_by_id(uuid)
    if run.status in ["queued", "running", "paused"]:
        queue_runs.update(status="cancelled").where(queue_runs.uuid == uuid).execute()
    
def resume_queued_run(uuid):
    #only if total is greater than current
    run = queue_runs.get_by_id(uuid)
    if run.total > run.current:        
        queue_runs.update(status="queued").where(queue_runs.uuid == uuid).execute()
       
def get_queued_run_by_id(uuid):
    return queue_runs.get_by_id(uuid)

def get_queue_runs():
    return queue_runs.select()


def get_queue_run(uuid):
    return queue_runs.select().where(queue_runs.uuid == uuid).execute()

def delete_queue_run(uuid):
    queue_runs.delete_by_id(uuid)

def insert_queue_run(queued_run):
    queue_runs.insert(queued_run).execute()
    return get_queue_run(queued_run["uuid"])[0]

def update_queue_run(queued_run):
    queued_run.update_date = datetime.datetime.now()
    queued_run.save()
    return get_queue_run(queued_run.uuid)[0]

# queue_steps - queue results

class queue_steps(BaseModelWithUUID):
    queued_run_uuid = ForeignKeyField(queue_runs, null=True,on_delete='SET NULL', backref='queued_run')
    run_value = TextField()
    status = TextField(null=False) # queued, running, paused, cancelled, completed
    step = IntegerField(null=False)
    server = IntegerField(null=False)
    retry = IntegerField(null=False, default=0)
    error =  TextField(null=True)
    create_date = DateTimeField(null=False) 
    start_date = DateTimeField(null=True) 
    update_date = DateTimeField(null=False)
    end_date = DateTimeField(null=True) 
    
def get_queue_step_by_id(uuid):
    return queue_steps.get_by_id(uuid)

def get_completed_queue_steps(queued_run_uuid):
    return queue_steps.select().where(queue_steps.queued_run_uuid == queued_run_uuid, queue_steps.status == "completed").order_by(queue_steps.step)

def get_completed_queue_steps_count(queued_run_uuid):
    return get_completed_queue_steps(queued_run_uuid).count()    
    
def get_queue_steps_max_order(queued_run_uuid):
    return queue_steps.select(fn.MAX(queue_steps.step)).where(queue_steps.queued_run_uuid == queued_run_uuid).scalar()

def get_queue_steps_min_order(queued_run_uuid):
    return queue_steps.select(fn.MIN(queue_steps.step)).where(queue_steps.queued_run_uuid == queued_run_uuid).scalar()

def get_queue_steps(queued_run_uuid):
    return queue_steps.select().where(queue_steps.queued_run_uuid == queued_run_uuid).order_by(queue_steps.step).dicts()

def get_queue_steps_by_status_other_than(queued_run_uuid, status):
    return queue_steps.select().where(queue_steps.queued_run_uuid == queued_run_uuid, queue_steps.status != status).order_by(queue_steps.step).dicts()

def get_queue_steps_by_status(queued_run_uuid, status):
    return queue_steps.select().where(queue_steps.queued_run_uuid == queued_run_uuid, queue_steps.status == status).order_by(queue_steps.step).dicts()

def get_queue_steps_by_statuses_other_than(queued_run_uuid:str, statuses):
    return queue_steps.select().where(queue_steps.queued_run_uuid == queued_run_uuid, queue_steps.status.not_in(statuses)).order_by(queue_steps.step).dicts()

def get_queue_steps_by_statuses(queued_run_uuid, statuses):
    return queue_steps.select().where(queue_steps.queued_run_uuid == queued_run_uuid, queue_steps.status.in_(statuses)).order_by(queue_steps.step)

def get_all_queue_steps_by_statuses(statuses):
    return queue_steps.select().where(queue_steps.status.in_(statuses)).order_by(queue_steps.step)

def get_all_queue_steps_by_statuses_other_than(statuses):
    return queue_steps.select().where(queue_steps.status.not_in(statuses)).order_by(queue_steps.step)
    
def get_queue_steps_count(queued_run_uuid):
    return queue_steps.select().where(queue_steps.queued_run_uuid == queued_run_uuid).count()

def get_queue_steps_short():
    return queue_steps.select()

def get_queue_steps_full():
    return queue_steps.select()

def get_queue_step(uuid):
    return queue_steps.select().where(queue_steps.uuid == uuid).execute()[0]

def delete_queue_step(uuid):
    queue_steps.delete_by_id(uuid)
    
def insert_queue_step(queue_step):
    now = datetime.datetime.now()
    queue_step["create_date"] = now
    queue_step["update_date"] = now
    queue_steps.insert(queue_step).execute()
    return get_queue_step(queue_step["uuid"])

def update_queue_step(queue_step):
    queue_step.update_date = datetime.datetime.now()
    queue_step.save()
    return get_queue_step(queue_step.uuid)

# output - output from the run

class outputs(BaseModelWithUUID):
    queue_step_uuid = ForeignKeyField(queue_steps, null=True,on_delete='SET NULL', backref='queue_step')
    value = TextField(null=False)
    order = IntegerField(null=False)
    node_id = IntegerField(null=False)
    output_type = TextField(null=False)
    create_date = DateTimeField(null=False)
    rating = SmallIntegerField(default=0)

def get_all_outputs_for_run(queued_run_uuid):
    return outputs.select().join(queue_steps).where(queue_steps.queued_run_uuid == queued_run_uuid).order_by(outputs.order).dicts().execute()

def get_output(uuid):
    return outputs.get_by_id(uuid)

def get_outputs():
    return outputs.select()

def get_outputs_by_queue_step(queue_step_uuid):
    return outputs.select().where(outputs.queue_step_uuid == queue_step_uuid).order_by(outputs.order)

def get_outputs_by_queue_step_and_node_id(queue_step_uuid, node_id):
    return outputs.select().where(outputs.queue_step_uuid == queue_step_uuid, outputs.node_id == node_id).order_by(outputs.order)

def get_outputs_by_queue_step_and_node_id_and_output_type(queue_step_uuid, node_id, output_type):
    return outputs.select().where(outputs.queue_step_uuid == queue_step_uuid, outputs.node_id == node_id, outputs.output_type == output_type).order_by(outputs.order)

def get_outputs_by_queue_step_and_output_type(queue_step_uuid, output_type):
    return outputs.select().where(outputs.queue_step_uuid == queue_step_uuid, outputs.output_type == output_type).order_by(outputs.order)

def get_outputs_by_node_run_uuid(node_run_uuid):
    return outputs.select().join(queue_steps).where(queue_steps.queued_run_uuid == node_run_uuid).order_by(outputs.order)


def insert_output(output):
    now = datetime.datetime.now()
    output["create_date"] = now
    outputs.insert(output).execute()
    return get_output(output["uuid"])

# settings - settings for UI and backend

class settings(BaseModelWithUUID):
    name = TextField()
    setting_type = TextField()
    description = TextField(null=True)
    value = TextField(null=True)
    value_type = TextField(null=True)
    value_type_options = TextField(null=True)

def get_settings():
    return settings.select()

def upsert_setting(setting):
    settings.insert(setting).on_conflict(conflict_target=(settings.uuid,),update=setting).execute()


# create tables

def create_tables():
    with database:
        database.create_tables([selection_item, settings, categories,workflows, queue_runs, queue_steps, outputs, api, jobs ])

        

