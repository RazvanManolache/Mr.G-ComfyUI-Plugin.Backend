import datetime
import logging


from re import T
from peewee import *


from playhouse.shortcuts import model_to_dict, dict_to_model



dbName = ".\db\mrg.db"

database = SqliteDatabase(dbName, pragmas={
    'journal_mode': 'wal',
    'cache_size': 10000,  # 10000 pages, or ~40MB
    'foreign_keys': 1,  # Enforce foreign-key constraints
})
logger = logging.getLogger('peewee')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)



class BaseModel(Model): # js model
    uuid = TextField(primary_key=True)
    class Meta:
        database = database
        
def get_request_info():
    count = batch_requests.select(fn.SUM(batch_requests.total - batch_requests.current)).where(batch_requests.status.not_in(("completed","cancelled"))).scalar()
    return count

def get_batch_requestning():
    return batch_requests.select().where(batch_requests.status == "running").count()


    
    

def copy_values(src, dest):
    is_src_dict = isinstance(src, dict)
    is_dst_dict = isinstance(dest, dict)
    
    attrs = src
    if not is_src_dict:
        # make empty dict
        attrs = {} 
        a = dir(src)
        for key in a:
            if key[0] != "_":
                attrs[key] = getattr(src,key)

    for key in attrs.keys():
        # do not update uuid, create_date, update_date
        if key == "uuid" or key == "create_date" or key == "update_date":
            continue
        if is_dst_dict:
            dest[key] = attrs[key]
        else:
            setattr(dest, key,attrs[key])
    
    
    
class NamedObject(BaseModel): # js model
    name = TextField()
    description = TextField(null=True)   
    create_date = DateTimeField(null=False)
    update_date = DateTimeField(null=False)
    tags = TextField(null=True)

class package_repositories(NamedObject): # js model
    url = TextField()
    system = BooleanField(default=False)

def get_package_repository(uuid):
    return package_repositories.get_by_id(uuid)

def get_package_repositories():
    return package_repositories.select()

def upsert_package_repository(pkg_repo):
    pkg_repo["update_date"] = datetime.datetime.now()
    existing_row = None
    try:
        existing_row = package_repositories.get_by_id(pkg_repo["uuid"])
    except:
        pass
    if existing_row == None:
        pkg_repo["create_date"] = pkg_repo["update_date"]
        
        package_repositories.insert(pkg_repo).execute()
        return get_package_repository(pkg_repo["uuid"])
    else:
        if existing_row.system == True:
            return None
        copy_values(pkg_repo, existing_row)
        existing_row.save()
        return model_to_dict(existing_row)
    


def delete_package_repository(uuid):
    if package_repositories.get_by_id(uuid).system == True:
        return
    package_repositories.delete_by_id(uuid)
    

#package - installed packages

class packages(NamedObject): #js model
    name = TextField()
    description = TextField(null=True)
    version = TextField(null=True)
    repository = TextField(null=True)
    branch = TextField(null=True)
    commit = TextField(null=True)
    parameters = TextField(null=True)
    settings = TextField(null=True)
    package_repository_uuid = ForeignKeyField(package_repositories, null=True,on_delete='SET NULL', backref='package_repository')
    
    
def get_package(uuid):
    return packages.get_by_id(uuid)

def get_packages():
    return packages.select()

def upsert_package(pkg):
    existing_row = None
    pkg["update_date"] = datetime.datetime.now()
    try:
        existing_row = packages.get_by_id(pkg["uuid"])
    except:
        pass
    if existing_row == None:
        pkg["create_date"] = pkg["update_date"]
        packages.insert(pkg).execute()
        return get_package(pkg["uuid"])
    else:
        copy_values(pkg, existing_row)
        existing_row.save()
        return model_to_dict(existing_row)

def delete_package(uuid, remove_associated = False):
    #delete jobs, apis and workflows
    if remove_associated:
        jobs.delete().where(jobs.package_uuid == uuid).execute()
        api.delete().where(api.package_uuid == uuid).execute()
        workflows.delete().where(workflows.package_uuid == uuid).execute()    
    packages.delete_by_id(uuid)
    


#selection_items - data for all combos

class selection_items(NamedObject): #js model
    alias = TextField()
    comfy_name = TextField(null=True)
    comments = TextField(null=True)
    times_used = IntegerField(default=0)
    rating = SmallIntegerField(default=0)
    text = TextField()
    hidden = BooleanField(default=False)
    favorite = BooleanField(default=False)
    field = TextField(null=True)
    field_type = TextField()
    node_type = TextField()
    path = TextField(null=True)
    image = TextField(null=True)
    thumbnail = TextField(null=True)
    


def get_selection_item(uuid):
    return selection_items.get_by_id(uuid)
    
def get_selection_items(field_type, node_type):
    if(node_type=='*'):
        return selection_items.select().where(selection_items.field_type == field_type)
    return selection_items.select().where(selection_items.field_type == field_type, selection_items.node_type == node_type)


def get_selection_item_by_node_field_value(node_type, field_type, value): 
    result = selection_items.select().where(selection_items.node_type == node_type, selection_items.field_type == field_type, selection_items.comfy_name == value).execute()
    if len(result) == 1:
        return result[0]
    result = selection_items.select().where(selection_items.field_type == field_type, selection_items.comfy_name == value or selection_items.text == value).execute()
    if len(result) == 1:
        return result[0]
    return None
    
def upsert_selection_items(sel_item):
    existing_row = None
    sel_item["update_date"] = datetime.datetime.now()
    try:
        existing_row = selection_items.get_by_id(sel_item["uuid"])
    except: 
        pass
    if existing_row == None:
        sel_item["create_date"] = sel_item["update_date"]
        selection_items.insert(sel_item).execute()
        return sel_item
    else:
        copy_values(sel_item, existing_row)
        existing_row.save()
        return model_to_dict(existing_row)
    
    #selection_item.insert(sel_item).on_conflict(conflict_target=(sel_item["uuid"],),update=sel_item).execute()

def delete_selection_items(uuid):
    selection_items.delete_by_id(uuid)
    




# categories - categories for workflows

class categories(NamedObject): #js model
    icon = TextField()
    system = BooleanField(default=False)
    order = IntegerField(default=1)
    parent_uuid = ForeignKeyField('self',null=True,on_delete='CASCADE', backref='categories')

def get_categories():
    return categories.select().order_by(categories.order).dicts().execute()

def get_category(uuid):
    try:
        return categories.get_by_id(uuid)
    except:
        pass
    return None

def upsert_category(category):
    existing_row = None
    category["update_date"] = datetime.datetime.now()
    try:
        existing_row = categories.get_by_id(category["uuid"])
    except:
        pass
    if existing_row == None:
        category["create_date"] = category["update_date"]
        categories.insert(category).execute()
        return category
    else:
        copy_values(category, existing_row)
        existing_row.save()
        return model_to_dict(existing_row)
    #categories.insert(category).on_conflict(conflict_target=(categories.uuid,),update=category).execute()
    #return get_category(category["uuid"])

def delete_category(uuid):
    cat =  categories.get_by_id(uuid)
    if(cat is None):
        return
    if(cat.system == True):
        return
    categories.delete_by_id(uuid)

    

# workflows - all saved workflows

class NamedPackageObject(NamedObject): #js model
    package_uuid = ForeignKeyField(packages, null=True,on_delete='SET NULL', backref='package')
    category_uuid = ForeignKeyField(categories, null=True,on_delete='SET NULL', backref='category')    

    
class workflows(NamedPackageObject): #js model
    
    rating = SmallIntegerField(default=0)
    order = IntegerField(default=1)
    favourite = BooleanField(default=False)  
    

    hidden = BooleanField(default=False)
    system = BooleanField(default=False)
    times_used = IntegerField(default=0)

    contents = TextField(null=True)
    nodes_values = TextField(null=True)
    settings = TextField(null=True)
    run_values =  TextField(null=True)

    

def get_workflows_short():
    return workflows.select()

def get_workflows_full():
    return workflows.select()

def get_workflow(uuid):
    return workflows.select().where(workflows.uuid == uuid).execute()[0]

def delete_workflow(uuid):
    workflows.delete_by_id(uuid)

def upsert_workflow(workflow):
    existing_row = None
    workflow["update_date"] = datetime.datetime.now()
    try:
        existing_row = workflows.get_by_id(workflow["uuid"])
    except:
        pass
    if existing_row == None:
        workflow["create_date"] = workflow["update_date"]
        workflows.insert(workflow).execute()
        return workflow
    else:
        copy_values(workflow, existing_row)
        existing_row.save()
        return model_to_dict(existing_row)
    


class workflow_extenders(NamedPackageObject): #js model
    workflows = TextField(null=True)    
    enabled = BooleanField(default=True)
    runs = IntegerField(default=0)
    
class api(workflow_extenders): #js model
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

    

def upsert_api(api_ob):
    existing_row = None
    api_ob["update_date"] = datetime.datetime.now()
    try:
        existing_row = api.get_by_id(api_ob["uuid"])
    except:
        pass
    if existing_row == None:
        api_ob["create_date"] = api_ob["update_date"]
                
        api.insert(api_ob).execute()
        return api
    else:
        for key in api_ob.keys():
            setattr(existing_row,key,api_ob[key])
        existing_row.save()
        return model_to_dict(existing_row)

class jobs(workflow_extenders): #js model
    cron = TextField(null=False) #cron string

def update_job_runs(uuid, runs):
    jobs.update(runs=runs).where(jobs.uuid == uuid).execute()

def get_job(uuid):
    return jobs.get_by_id(uuid)

def get_jobs():
    return jobs.select()

def delete_job(uuid):
    jobs.delete_by_id(uuid)
    
def upsert_job(job):
    job["update_date"] = datetime.datetime.now()
    existing_row = None
    try:
        existing_row = jobs.get_by_id(job["uuid"])
    except:
        pass
    if existing_row == None:
        job["create_date"] = job["update_date"]
        jobs.insert(job).execute()
        return job
    else:
        for key in job.keys():
            setattr(existing_row,key,job[key])
        existing_row.save()
        return model_to_dict(existing_row)
    

# batch_requests - queue
 
class batch_requests(NamedObject): 
    workflow_uuid = ForeignKeyField(workflows, null=True,on_delete='SET NULL', backref='workflow') #saved
    api_uuid = ForeignKeyField(api, null=True,on_delete='SET NULL', backref='api') #saved
    job_uuid = ForeignKeyField(jobs, null=True,on_delete='SET NULL', backref='job') #saved
    secondary_uuid = TextField(null=True) #saved
    client_id = TextField(null=True) #saved
    run_settings = TextField(null=False) #saved
    total = IntegerField(null=False) #saved
    contents = TextField(null=True) #saved
    run_type = TextField(null = False) #saved
    current = IntegerField(null=False) #saved on creation
    order = BigIntegerField(null=False) #saved on creation
    status = TextField(null=True) #saved on creation      
    start_date = DateTimeField(null=True) #saved on creation 
    end_date = DateTimeField(null=True) #saved on creation 
    nodes_values = TextField(null=True) #wip
    run_values =  TextField(null=True) #saved
    current_values = TextField(null=True) #need to update

def get_batch_requests_paginated(page, per_page, orderby, order_dir, filt):
    #include outputs, workflow name, api name and job name
    page_results = (batch_requests.select()
                    .join(batch_steps, JOIN.LEFT_OUTER, on=batch_steps.batch_request_uuid == batch_requests.uuid)
                    .join(outputs, JOIN.LEFT_OUTER, on=outputs.batch_step_uuid == batch_steps.uuid)
                    .join_from(batch_requests, workflows, JOIN.LEFT_OUTER, on=batch_requests.workflow_uuid== workflows.uuid)
                    .join_from(batch_requests, api, JOIN.LEFT_OUTER, on=batch_requests.api_uuid == api.uuid)
                    .join_from(batch_requests, jobs, JOIN.LEFT_OUTER, on=batch_requests.job_uuid == jobs.uuid))
    
    page_results= page_results.group_by(batch_requests, workflows.name, api.name, jobs.name)
   
    if orderby:
        page_results = page_results.order_by(orderby)
        
    page_results = page_results.paginate(page, per_page)

    
    # # select only the fields we need, everything from outputs and only the name from the other tables

    page_results = page_results.select(batch_requests, 
                                       fn.COUNT(batch_steps.uuid).alias("steps_count"),
                                       fn.COUNT(outputs.uuid).alias("outputs_count"),
                                       workflows.name.alias("workflow_name"), 
                                       api.name.alias("api_name"),
                                       jobs.name.alias("job_name"))
                                  

    if filt:
        page_results = page_results.where(filt)
    page_results = list(page_results.dicts().execute())
    total = batch_requests.select().count()
    pages = total / per_page
    return {"data":page_results, "total":total, "pages":pages, "success": True}
    
    

def get_batch_request_status_for_uuid_list(uuids):
    return batch_requests.select(batch_requests.uuid, batch_requests.status).where(batch_requests.uuid.in_(uuids)).dicts().execute()

def get_batch_requests_max_order():
    return batch_requests.select(fn.MAX(batch_requests.order)).scalar()

def get_batch_requests_min_order():
    return batch_requests.select(fn.MIN(batch_requests.order)).scalar()

def get_batch_requests_by_status(status):
    return batch_requests.select().where(batch_requests.status == status).order_by(batch_requests.order)

def get_batch_requests_by_statuses(statuses):
    return batch_requests.select().where(batch_requests.status.in_(statuses)).order_by(batch_requests.order)

def pause_batch_request(uuid):
    #only if it is queued or running
    batch_request = batch_requests.get_by_id(uuid)
    if batch_request.status in ["queued", "running"]:
        batch_requests.update(status="paused").where(batch_requests.uuid == uuid).execute()
    
def cancel_batch_request(uuid):
    #only if it is queued or running or paused
    batch_request = batch_requests.get_by_id(uuid)
    if batch_request.status in ["queued", "running", "paused"]:
        batch_requests.update(status="cancelled").where(batch_requests.uuid == uuid).execute()
    
def resume_batch_request(uuid):
    #only if total is greater than current
    batch_request = batch_requests.get_by_id(uuid)
    if batch_request.total > batch_request.current:        
        batch_requests.update(status="queued").where(batch_requests.uuid == uuid).execute()
       
def get_batch_request_by_id(uuid):
    return batch_requests.get_by_id(uuid)

def get_batch_requests():
    return batch_requests.select()


def get_batch_request(uuid):
    return batch_requests.select().where(batch_requests.uuid == uuid).execute()

def delete_batch_request(uuid):
    batch_requests.delete_by_id(uuid)

def insert_batch_request(batch_request):
    batch_requests.insert(batch_request).execute()
    return get_batch_request(batch_request["uuid"])[0]

def update_batch_request(batch_request):
    batch_request.update_date = datetime.datetime.now()
    batch_request.save()
    return get_batch_request(batch_request.uuid)[0]

def get_batch_request_by_step_id(uuid):
    result = batch_requests.select().join(batch_steps).where(batch_steps.uuid == uuid).execute()
    if len(result) == 1:
        return result[0]
    return None

# batch_steps - queue results

class batch_steps(BaseModel):
    batch_request_uuid = ForeignKeyField(batch_requests, null=True,on_delete='SET NULL', backref='batch_request')
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
    
def get_batch_step_by_id(uuid):
    return batch_steps.get_by_id(uuid)

def get_completed_batch_steps(batch_request_uuid):
    return batch_steps.select().where(batch_steps.batch_request_uuid == batch_request_uuid, batch_steps.status == "completed").order_by(batch_steps.step)

def get_completed_batch_steps_count(batch_request_uuid):
    return get_completed_batch_steps(batch_request_uuid).count()    
    
def get_batch_steps_max_order(batch_request_uuid):
    return batch_steps.select(fn.MAX(batch_steps.step)).where(batch_steps.batch_request_uuid == batch_request_uuid).scalar()

def get_batch_steps_min_order(batch_request_uuid):
    return batch_steps.select(fn.MIN(batch_steps.step)).where(batch_steps.batch_request_uuid == batch_request_uuid).scalar()

def get_batch_steps(batch_request_uuid):
    return batch_steps.select().where(batch_steps.batch_request_uuid == batch_request_uuid).order_by(batch_steps.step).dicts()

def get_batch_steps_by_status_other_than(batch_request_uuid, status):
    return batch_steps.select().where(batch_steps.batch_request_uuid == batch_request_uuid, batch_steps.status != status).order_by(batch_steps.step).dicts()

def get_batch_steps_by_status(batch_request_uuid, status):
    return batch_steps.select().where(batch_steps.batch_request_uuid == batch_request_uuid, batch_steps.status == status).order_by(batch_steps.step).dicts()

def get_batch_steps_by_statuses_other_than(batch_request_uuid:str, statuses):
    return batch_steps.select().where(batch_steps.batch_request_uuid == batch_request_uuid, batch_steps.status.not_in(statuses)).order_by(batch_steps.step).dicts()

def get_batch_steps_by_statuses(batch_request_uuid, statuses):
    return batch_steps.select().where(batch_steps.batch_request_uuid == batch_request_uuid, batch_steps.status.in_(statuses)).order_by(batch_steps.step)

def get_all_batch_steps_by_statuses(statuses):
    return batch_steps.select().where(batch_steps.status.in_(statuses)).order_by(batch_steps.step)

def get_all_batch_steps_by_statuses_other_than(statuses):
    return batch_steps.select().where(batch_steps.status.not_in(statuses)).order_by(batch_steps.step)
    
def get_batch_steps_count(batch_request_uuid):
    return batch_steps.select().where(batch_steps.batch_request_uuid == batch_request_uuid).count()

def get_batch_steps_short():
    return batch_steps.select()

def get_batch_steps_full():
    return batch_steps.select()

def get_batch_step(uuid):
    return batch_steps.select().where(batch_steps.uuid == uuid).execute()[0]

def delete_batch_step(uuid):
    batch_steps.delete_by_id(uuid)
    
def insert_batch_step(batch_step):
    now = datetime.datetime.now()
    batch_step["create_date"] = now
    batch_step["update_date"] = now
    batch_steps.insert(batch_step).execute()
    return get_batch_step(batch_step["uuid"])

def update_batch_step(batch_step):
    batch_step.update_date = datetime.datetime.now()
    batch_step.save()
    return get_batch_step(batch_step.uuid)

# output - output from the run

class outputs(BaseModel):
    batch_step_uuid = ForeignKeyField(batch_steps, null=True,on_delete='SET NULL', backref='batch_step')
    value = TextField(null=False)
    order = IntegerField(null=False)
    node_id = IntegerField(null=False)
    output_type = TextField(null=False)
    create_date = DateTimeField(null=False)
    update_date = DateTimeField(null=False)
    rating = SmallIntegerField(default=0)

def get_all_outputs_for_run(batch_request_uuid):
    return outputs.select().join(batch_steps).where(batch_steps.batch_request_uuid == batch_request_uuid).order_by(outputs.order).dicts().execute()

def get_output(uuid):
    return outputs.get_by_id(uuid)



def get_outputs_paginated(page, per_page, orderby, order_dir, filt):
    page_results = outputs.select().paginate(page, per_page)
    #include step info
    page_results = (page_results.join(batch_steps, on=outputs.batch_step_uuid == batch_steps.uuid)
                                .join(batch_requests, on= batch_steps.batch_request_uuid == batch_requests.uuid)
                                .join_from(batch_requests, workflows, JOIN.LEFT_OUTER, on=batch_requests.workflow_uuid== workflows.uuid)
                                .join_from(batch_requests, api, JOIN.LEFT_OUTER, on=batch_requests.api_uuid == api.uuid)
                                .join_from(batch_requests, jobs, JOIN.LEFT_OUTER, on=batch_requests.job_uuid == jobs.uuid))
    

    
    # select only the fields we need, everything from outputs and only the name from the other tables

    page_results = page_results.select(outputs, batch_requests.uuid.alias("batch_request_uuid"), 
                                       workflows.uuid.alias("workflow_uuid"), workflows.name.alias("workflow_name"), 
                                       api.uuid.alias("api_uuid"), api.name.alias("api_name"),
                                       jobs.uuid.alias("job_uuid"), jobs.name.alias("job_name"), batch_requests.tags.alias("tags"))
                                  
    
    if orderby is not None:
        page_results = page_results.order_by(orderby)
    
    page_results = list(page_results.dicts().execute())
    total = outputs.select().count()
    pages = total // per_page
    return {"data":page_results, "total":total, "pages":pages, "success": True}

def get_outputs_by_batch_step(batch_step_uuid):
    return outputs.select().where(outputs.batch_step_uuid == batch_step_uuid).order_by(outputs.order)

def get_outputs_by_batch_step_and_node_id(batch_step_uuid, node_id):
    return outputs.select().where(outputs.batch_step_uuid == batch_step_uuid, outputs.node_id == node_id).order_by(outputs.order)

def get_outputs_by_batch_step_and_node_id_and_output_type(batch_step_uuid, node_id, output_type):
    return outputs.select().where(outputs.batch_step_uuid == batch_step_uuid, outputs.node_id == node_id, outputs.output_type == output_type).order_by(outputs.order)

def get_outputs_by_batch_step_and_output_type(batch_step_uuid, output_type):
    return outputs.select().where(outputs.batch_step_uuid == batch_step_uuid, outputs.output_type == output_type).order_by(outputs.order)

def get_outputs_by_node_run_uuid(node_run_uuid):
    return outputs.select().join(batch_steps).where(batch_steps.batch_request_uuid == node_run_uuid).order_by(outputs.order)

def update_output(uuid, json_data):
    
    rating = json_data.get("rating", None)
    if rating is not None:    
        outputs.update(rating=rating).where(outputs.uuid == uuid).execute()
    
    
def delete_output(uuid):
    outputs.delete_by_id(uuid)

def insert_output(output):
    now = datetime.datetime.now()
    output["create_date"] = now
    output["update_date"] = now
    outputs.insert(output).execute()
    return get_output(output["uuid"])

# output_link - output links to selection items
class output_links(BaseModel):
    output_uuid = ForeignKeyField(outputs, null=True,on_delete='CASCADE', backref='output')
    selection_item_uuid = ForeignKeyField(selection_items, null=True,on_delete='CASCADE', backref='selection_item')
    
def get_output_link(uuid):
    return output_links.get_by_id(uuid)

def get_output_links_by_output(output_uuid):
    return output_links.select().where(output_links.output_uuid == output_uuid)

def get_selection_item_by_output(output_uuid):
    return output_links.select().join(selection_items).where(output_links.output_uuid == output_uuid).dicts().execute()

def get_outputs_by_selection_item(selection_item_uuid, page, pagesize):
    return outputs.select().join(output_links).where(output_links.selection_item_uuid == selection_item_uuid).paginate(page, pagesize)
    

def get_output_links_by_selection_item(selection_item_uuid):
    return output_links.select().where(output_links.selection_item_uuid == selection_item_uuid)

def insert_output_link(output_link):
    output_links.insert(output_link).execute()
    return get_output_link(output_link["uuid"])

def delete_output_link(uuid):
    output_links.delete_by_id(uuid)
    

# settings - settings for UI and backend

class settings(NamedObject):
    setting_type = TextField()
    value = TextField(null=True)
    value_type = TextField(null=True)
    value_type_options = TextField(null=True)

def get_settings():
    return settings.select()

def upsert_setting(setting):
    existing_row = None
    setting["update_date"] = datetime.datetime.now()
    try:
        existing_row = settings.get_by_id(setting["uuid"])
    except:
        pass
    if existing_row == None:
        setting["create_date"] = setting["update_date"]
        settings.insert(setting).execute()
        return setting
    else:
        for key in setting.keys():
            setattr(existing_row,key,setting[key])
        existing_row.save()
        return model_to_dict(existing_row)


# create tables

def create_tables():
    with database:
        database.create_tables([selection_items, settings, categories,workflows, batch_requests, batch_steps, outputs, api, jobs, package_repositories, packages ])
        
create_tables()

def create_default_data():
    upsert_package_repository({"uuid":"f42cd12c-4c7a-451b-a1f4-ad2d2a6fe28f","name":"Mr.G official packages","url":"https://github.com/RazvanManolache/Mr.G-AI-Packages-List","system":True})

    upsert_category({"uuid":"00000000-0001-0000-0000-000000000000","name":"Favourites","icon":"x-fa fa-star","system":True,"order":-9999})
    upsert_category({"uuid":"00000000-0003-0000-0000-000000000000","name":"No category","icon":"x-fa fa-question","system":True,"order":-9997})
    upsert_category({"uuid":"00000000-0002-0000-0000-000000000000","name":"All","icon":"x-fa fa-globe","system":True,"order":-9998})

create_default_data()

