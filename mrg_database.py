import datetime
from re import T
from peewee import *
from playhouse.shortcuts import model_to_dict



dbName = ".\db\mrg.db"

database = SqliteDatabase(dbName, pragmas={
    'journal_mode': 'wal',
    'cache_size': 10000,  # 10000 pages, or ~40MB
    'foreign_keys': 1,  # Enforce foreign-key constraints
})

class BaseModel(Model): # js model
    uuid = TextField(primary_key=True)
    class Meta:
        database = database
        
def get_queue_info():
    count = queue_runs.select(fn.SUM(queue_runs.total - queue_runs.current)).where(queue_runs.status.not_in(("completed","cancelled"))).scalar()
    return count

def get_queue_running():
    return queue_runs.select().where(queue_runs.status == "running").count()


    
    

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
    field = TextField()
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
    

# queue_runs - queue
 
class queue_runs(NamedObject): 
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

def get_queue_runs_paged(page, per_page, order_column, order_dir, filt):
    #include outputs, workflow name, api name and job name
    page_results = queue_runs.select().join(queue_steps).join(outputs).join(workflows).join(api).join(jobs).order_by(order_column).paginate(page, per_page)
    if filt is not None:
        page_results = page_results.where(filt)
    page_results = page_results.dicts().execute()
    total = queue_runs.select().count()
    pages = total // per_page
    return {"items":page_results, "total":total, "pages":pages}
    
    

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

def get_queue_run_by_step_id(uuid):
    return queue_runs.select().where(queue_runs.uuid == uuid).execute()[0]

# queue_steps - queue results

class queue_steps(BaseModel):
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

class outputs(BaseModel):
    queue_step_uuid = ForeignKeyField(queue_steps, null=True,on_delete='SET NULL', backref='queue_step')
    value = TextField(null=False)
    order = IntegerField(null=False)
    node_id = IntegerField(null=False)
    output_type = TextField(null=False)
    create_date = DateTimeField(null=False)
    update_date = DateTimeField(null=False)
    rating = SmallIntegerField(default=0)

def get_all_outputs_for_run(queued_run_uuid):
    return outputs.select().join(queue_steps).where(queue_steps.queued_run_uuid == queued_run_uuid).order_by(outputs.order).dicts().execute()

def get_output(uuid):
    return outputs.get_by_id(uuid)

def get_outputs():
    return outputs.select()


def get_outputs_paginated(page, per_page, orderby, order_name, order_dir):
    page_results = outputs.select().paginate(page, per_page)
    #include step info
    page_results = page_results.join(queue_steps).join(queue_runs).join(workflows).join(api).join(jobs)
    
    # select only the fields we need, everything from outputs and only the name from the other tables

    page_results = page_results.select(outputs, queue_runs.uuid.alias("queue_run_uuid"), 
                                       workflows.uuid.alias("workflow_uuid"), workflows.name.alias("workflow_name"), 
                                       api.uuid.alias("api_uuid"), api.name.alias("api_name"),
                                       jobs.uuid.alias("job_uuid"), jobs.name.alias("job_name")
                                  )
    
    if orderby is not None:
        page_results = page_results.order_by(orderby)
    
    page_results = page_results.dicts().execute()
    total = outputs.select().count()
    pages = total // per_page
    return {"items":page_results, "total":total, "pages":pages}

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

def update_output_rating(uuid, rating):
    outputs.update(rating=rating).where(outputs.uuid == uuid).execute()
    
def delete_output(uuid):
    outputs.delete_by_id(uuid)

def insert_output(output):
    now = datetime.datetime.now()
    output["create_date"] = now
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
        database.create_tables([selection_items, settings, categories,workflows, queue_runs, queue_steps, outputs, api, jobs, package_repositories, packages ])
        
create_tables()

def create_default_data():
    upsert_package_repository({"uuid":"f42cd12c-4c7a-451b-a1f4-ad2d2a6fe28f","name":"Mr.G official packages","url":"https://github.com/RazvanManolache/Mr.G-AI-Packages-List","system":True})

    upsert_category({"uuid":"00000000-0001-0000-0000-000000000000","name":"Favourites","icon":"x-fa fa-star","system":True,"order":-9999})
    upsert_category({"uuid":"00000000-0003-0000-0000-000000000000","name":"No category","icon":"x-fa fa-question","system":True,"order":-9997})
    upsert_category({"uuid":"00000000-0002-0000-0000-000000000000","name":"All","icon":"x-fa fa-globe","system":True,"order":-9998})

        

