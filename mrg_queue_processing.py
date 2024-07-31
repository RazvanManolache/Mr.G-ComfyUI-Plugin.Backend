import array
import random
import asyncio
import datetime
import base64

import server
import execution
import json
import copy
import math

import pylab as pl

from doctest import debug
from fileinput import filename
from tokenize import String
from asyncio.windows_events import NULL
from calendar import c
from aiohttp import web
from execution import *

from .mrg_database import *
from .mrg_helpers import *


from types import SimpleNamespace

server_address = "127.0.0.1:8188"
mrg_client_id = str(uuid.uuid4())

def get_obj_dict(obj):
    return obj.__dict__


def make_json(obj):
    return json.dumps(obj, default=get_obj_dict,separators=(',', ':'))

def queded_run_result_finished(uuid):
    result = get_batch_step_by_id(uuid)
    result.status = "finished"
    result.end_time = datetime.datetime.now();    
    update_batch_step(result)
    check_batch_requests_finished_uuid(result["batch_request_uuid"])
    
def check_comfy_queue():
    #somehow check that comfy is still doing stuff and if so, return
    return False

def get_prompt_queue(server_id):
    return server.PromptServer.instance.prompt_queue

def get_prompt_queue_history(server_id):
    return get_prompt_queue(server_id).get_history()

def get_prompt_queue_queue(server_id):
    return get_prompt_queue(server_id).queue

def get_prompt_queue_currently_running(server_id):
    return get_prompt_queue(server_id).currently_running

def delete_history_item(server_id, uuid):
    get_prompt_queue(server_id).delete_history_item(uuid)

    
def prompt_queue_put(server_id, number, prompt_id, prompt, extra_data, outputs_to_execute):
    get_prompt_queue(server_id).put((number, prompt_id, prompt, extra_data, outputs_to_execute))

def process_socket_api_request(sid, data):
     try:
        data = json.loads(data)
        if data["type"] == "getActions":
            return {"type": "actionDefinitions", "result": {"actions": get_api_actions_def_clean()}}
        elif data["type"] == "getAction":
            if("api" in data):
                return {"type": "actionDefinition", "result":get_api_action_def_clean(data["api"])}
        elif data["type"] == "getStatus":
            ob = { "query": [], "result":[]} 
            if "uuids" in data and type(data["uuids"]) is list:
                ob["query"] = data["uuids"]
                ob["result"] = list(get_batch_request_status_for_uuid_list(data["uuids"]))
            return {"type": "requestStatuses", "result": ob}
        elif data["type"] == "getResult":
            outputs = get_all_outputs_for_run(data["uuid"]);
            output_results = []
            for output in outputs:
                
                output_data = json.loads(output["value"].replace("\'", "\""))
                output_type = output["output_type"]
                directory = folder_paths.get_directory_by_type(output_data["type"])
                subfolder = output_data["subfolder"]
                filename = output_data["filename"]
                path = os.path.join(directory, subfolder, filename)
                
                contents = None
                #read the file
                #check if file exists
                if os.path.exists(path):
                    with open(path, 'rb') as file:
                        contents = base64.b64encode(file.read()).decode("utf-8")
                output_result = {"name": filename, "type":output_type, "contents":contents}
                output_results.append(output_result)
            return {"type": "resultPushed", "result": { "outputs":output_results, "batch_request_uuid":data["uuid"]}}
            pass
        elif data["type"] == "executeApi":
            if("requestId" not in data):
                return {"type": "executeApiError", "result": "Api request must have requestId parameter"}
            if("api" not in data):                       
                return {"type": "executeApiError", "result": "Api request must have api parameter"}
            
            api_def = get_api_action_def(data["api"])
            params = data["params"] if "params" in data else {}
            result = process_api_request(sid, api_def, params)
            if "error" in result:                
                return {"type": "executeApiError", "result": { "requestId": data["requestId"], "error": result["error"] }}
                
            return {"type": "executeApiQueued", "result": { "requestId": data["requestId"], "result": result }}
            #await self.execute(data["node"], data["prompt_id"], data["inputs"], data["outputs"])
        elif data["type"] == "executeWorkflow":
            pass
            #await self.execute(data["node"], data["prompt_id"], data["inputs"], data["outputs"])
        else:            
            return {"type": "error", "result": "Unknown request"}
     except Exception as e:        
        return {"type": "error", "result": "Unknown request"}
        print("Error handling socket request", e)
        traceback.print_exc()

def validate_api_request(api_ob):
    #check if all parameters are present
    for parameter in api_ob["parameters"]:
        if "value" not in parameter.keys():
            if not parameter["optional"]:
                return {"error": "Parameter "+parameter["name"] + " is required."}
            parameter["value"] = parameter["default_value"]
    
    #convert values to types
    for parameter in api_ob["parameters"]:
        if parameter["field_type"] == "INT":
            try:
                parameter["value"] = int(parameter["value"])
            except:
                return {"error": "Invalid value ("+parameter["value"]+") for parameter '"+parameter["name"]+ "'. It should be a int."}
        if parameter["field_type"] == "FLOAT":
            try:
                parameter["value"] = float(parameter["value"])
            except:
                return {"error": "Invalid value ("+parameter["value"]+") for parameter '"+parameter["name"]+ "'. It should be a float."}
        if parameter["field_type"] == "BOOLEAN":
            if parameter["value"] == "true":
                parameter["value"] = True
            else:
                parameter["value"] = False
    #validate collections
    for parameter in api_ob["parameters"]:
        if "collection" in parameter.keys():
            collection = parameter["collection"]
            if parameter["field_type"] == "SELECT":
                if parameter["value"] not in [x["v"] for x in collection["c"]]:
                    return {"error": "Invalid value for parameter "+parameter["name"]}
            if parameter["field_type"] == "INT":
                if "c" in collection.keys() and len(collection["c"])>0 and parameter["value"] not in [x["v"] for x in collection["c"]]:
                    return {"error": "Invalid value for parameter "+parameter["name"]}
                if "i" in collection.keys():
                    interval = collection["i"]
                    if "n" in interval.keys() and interval["n"] > parameter["value"]:
                        return {"error": "Invalid value for parameter "+parameter["name"]+ ". The value is smaller than minimum value of " + str(interval["n"])}
                    if "x" in interval.keys() and interval["x"] < parameter["value"]:
                        return {"error": "Invalid value for parameter "+parameter["name"]+ ". The value is greater than maximum value of " + str(interval["x"])}
                        
            if collection["c"] and parameter["field_type"] == "FLOAT":
                #check if it is float
                if "c" in collection.keys() and len(collection["c"])>0 and parameter["value"] not in [x["v"] for x in collection["c"]]:
                    return {"error": "Invalid value for parameter "+parameter["name"]}
                if "i" in collection.keys():
                    interval = collection["i"]
                    if "n" in interval.keys() and interval["n"] > parameter["value"]:
                        return {"error": "Invalid value for parameter "+parameter["name"]+ ". The value is smaller than minimum value of " + str(interval["n"])}
                    if "x" in interval.keys() and interval["x"] < parameter["value"]:
                        return {"error": "Invalid value for parameter "+parameter["name"]+ ". The value is greater than maximum value of " + str(interval["x"])}
    return None

def process_job_request(client_id, job_ob):
   
    validate = validate_api_request(job_ob)
    if validate:
        return validate
    
    #execute the workflows
    for workflow in job_ob["workflows"]:
       
        uuid = workflow["uuid"]
        origUuid = workflow["workflowUuid"]
        
        value_preset = {}
           
        preset_data = workflow["presetData"]
        if preset_data:
            #parse as json
            preset_data = json.loads(preset_data)
            

        try:
            work = get_workflow(workflow["workflowUuid"])
        except:
            return {"error": "Workflow not found"}

        workflow["queue"] = enqueue_prompt_by_type(client_id, work, secondary_uuid= uuid,job_uuid=job_ob["uuid"],run_mode=workflow["runMode"], preset=preset_data, override_values=value_preset, start_pos=int(job_ob["runs"]))
    errors = []
    for workflow in job_ob["workflows"]:
        if "error" in workflow["queue"].keys():
            errors.append(workflow["queue"]["error"])
    if len(errors)>0:
        return {"error": errors}
    for workflow in job_ob["workflows"]:
        workflow["run"] = insert_batch_request(workflow["queue"])
    update_job_runs(job_ob["uuid"], int(job_ob["runs"]+1))
    check_batch_requests()
    
    response = {}
    response["success"] = "OK"
    response["batch_request_uuids"] = [str(x["queue"]["uuid"]) for x in job_ob["workflows"]]
    
    return response

def get_api_actions_def_clean():
    data = get_apis().dicts()    
    data = [x for x in data if x["enabled"]]
    apis = get_definition_for_api(data)
    clean_api_definitions(apis)
    return apis

def get_api_action_def(ident):
    if not ident:
        return {}
    data = get_apis().dicts()    
    data = [x for x in data if x["enabled"]]
    data = [x for x in data if x["endpoint"]== ident or x["uuid"]== ident]
    if(len(data)!=1):
        return {}
    apis = get_definition_for_api(data)
    if(len(apis)!=1):
        return {}
    return apis[0]

def get_api_action_def_clean(ident):
    return clean_api_definitions([get_api_action_def(ident)])[0]

def process_api_request(client_id, api_ob, params):
    for parameter in api_ob["parameters"]:
        if parameter["name"] in params.keys():
            parameter["value"] = params[parameter["name"]]
    validate = validate_api_request(api_ob)
    if validate:
        return validate
    
    #execute the workflows
    for workflow in api_ob["workflows"]:
       
        uuid = workflow["uuid"]
        origUuid = workflow["workflowUuid"]
        
        value_preset = {}
        for parameter in api_ob["parameters"]:
            fields = [x for x in parameter["fields"] if x["workflowUniqueUuid"]==uuid]
            if len(fields):
                field = fields[0]
                node_id = field["nodeId"]
                str_node_id = str(node_id)
                if str_node_id not in value_preset.keys():
                    value_preset[str_node_id] = {}
                value_preset[str_node_id][field["fieldName"]] = {}
                value_preset[str_node_id][field["fieldName"]]["value"] = parameter["value"]
                #value_preset[str_node_id][field["fieldName"]]["sequence"] = "fixed"
            
        preset_data = workflow["presetData"]
        if preset_data:
            #parse as json
            preset_data = json.loads(preset_data)
            

        try:
            work = get_workflow(workflow["workflowUuid"])
        except:
            return {"error": "Workflow not found"}

        workflow["queue"] = enqueue_prompt_by_type(client_id, work, secondary_uuid= uuid,api_uuid=api_ob["uuid"],run_mode=workflow["runMode"], preset=preset_data, override_values=value_preset, start_pos=int(api_ob["runs"]))
    errors = []
    for workflow in api_ob["workflows"]:
        if "error" in workflow["queue"].keys():
            errors.append(workflow["queue"]["error"])
    if len(errors)>0:
        return {"error": errors}
    for workflow in api_ob["workflows"]:
        workflow["run"] = insert_batch_request(workflow["queue"])
    update_api_runs(api_ob["uuid"], int(api_ob["runs"]+1))
    check_batch_requests()
    
    response = {}
    response["success"] = "OK"
    response["batch_request_uuids"] = [str(x["queue"]["uuid"]) for x in api_ob["workflows"]]
    
    return response



def clean_api_definitions(apis):
    for api in apis:
        if "parameters" in api.keys() and api["parameters"]:
            for parameter in api["parameters"]:
                if parameter["fields"]:
                    del parameter["fields"]
    return apis

def get_definition_for_api(data):
    apis = []
    #for each of the entries, read the workflows column parse as json and get the uuids of the workflows
    for entry in data:
        workflows = json.loads(entry["workflows"])
        workflows = [x for x in workflows if x["enabled"]]
        if(len(workflows)==0):
            continue
        api_desc = {}
        api_desc["uuid"] = entry["uuid"]
        api_desc["name"] = entry["name"]
        api_desc["endpoint"] = entry["endpoint"]
        api_desc["description"] = entry["description"]
        api_desc["runs"] = entry["runs"]
        apis.append(api_desc)
        parameters = json.loads(entry["parameters"])
        parameters = [x for x in parameters if x["enabled"]]
        actual_parameters = []
        api_desc["parameters"] = actual_parameters
        api_desc["workflows"] = workflows
        for workflow in workflows:
            workflow_parameters = [x for x in parameters if x["workflowUniqueUuid"] == workflow["uuid"]]
            for parameter in workflow_parameters:
                parameter["workflowUuid"] = workflow["workflowUuid"]
                parameter["field"] = get_field_by_workflow_node_field(parameter["workflowUuid"], parameter["nodeId"], parameter["fieldName"])
                if(parameter["field"] == None):
                    continue
                
                parameter["collection"] = calculate_collection(parameter["field"])
                if(parameter["alias"] not in [x["name"] for x in actual_parameters]):
                    par = {}
                    par["optional"] = parameter["optional"]
                    par["name"] = parameter["alias"]
                    if parameter["field"]["fieldType"]=="SELECT" and parameter["field"]["fieldName"]=="image":
                        par["field_type"] = "IMAGE"
                    else:
                        par["field_type"] = parameter["field"]["fieldType"]
                        par["collection"] = parameter["collection"]
                    if not par["optional"]:
                        par["default_value"] = parameter["defaultValue"]
                    par["fields"] = []
                    par["fields"].append(parameter)
                    actual_parameters.append(par)
                else:
                    for par in actual_parameters:
                        if par["name"] == parameter["alias"] and par["field_type"] == parameter["field"]["fieldType"]:
                            #TODO: merge collections
                            if not par["optional"] and "default_value" not in par.keys():
                                 par["default_value"] = parameter["defaultValue"]
                            par["optional"] =  par["optional"] and parameter["optional"]
                            par["fields"].append(parameter)
        #set workflows as distinct list of all workflows from actual_parameters
        
    return apis

first_check_queue = True
def ws_queue_updated(server, message):
    # technically it's not hard to support multiple servers, but it's not needed for now
    server_id = 1;
    # print(message) 
    if isinstance(message, str):
        message = json.loads(message)
    batch_steps = get_all_batch_steps_by_statuses_other_than(["finished", "failed", "invalid"])
    history = get_prompt_queue_history(server_id)
    queue = get_prompt_queue_queue(server_id)
    currently_running = get_prompt_queue_currently_running(server_id)
    #prompt_queue.delete_history_item(uuid)
    #prompt_queue.wipe_history()    
    for step in batch_steps:
        found = False
        for key in history:
            if key == step.uuid:
                history_item = history[key]
                if step.status != 'finished':
                    step.end_date = datetime.datetime.now()
                    step.status = 'finished'
                    # add outputs to item
                    update_batch_step(step)
                    order = 1
                    for node_id in history_item["outputs"].keys():
                         node_output = history_item["outputs"][node_id] 
                         for output_type in node_output.keys():
                             output = node_output[output_type]
                             for output_item in output:
                                 outp = {}
                                 batch_request = get_batch_request_by_step_id(step.uuid)
                                 if not batch_request:
                                     continue
                                 selection_items = get_selection_items_from_step(batch_request, step)
                                 outp["batch_step_uuid"] = step.uuid
                                 outp["uuid"] = str(uuid.uuid4())
                                 outp["value"] = make_json(output_item)
                                 outp["output_type"] = output_type
                                 outp["node_id"] = node_id
                                 outp["order"] = order
                                 order += 1
                                 outp = insert_output(outp)
                                 if selection_items:
                                     for selection_item in selection_items:
                                         outp_sel = {}
                                         outp_sel["output_uuid"] = outp.uuid
                                         outp_sel["selection_item_uuid"] = selection_item.uuid
                                         insert_output_link(outp_sel)
                                 
                         
                    delete_history_item(server_id, key)
                found = True
                break
        for queued in queue:
            if queued[1] == step.uuid:
                if step.status != 'queued':
                    step.status = 'queued'
                    update_batch_step(step)
                found = True
                break
        for running in currently_running.values():
            if running[1] == step.uuid:
                if step.status != 'running':
                    step.start_date = datetime.datetime.now()
                    step.status = 'running'
                    update_batch_step(step)
                found = True
                break
        if not found:
            if step.retry>2:
                    step.status = "failed"
                    step.error = "Too many failed attempts"
                    update_batch_step(step)
                    continue
            step.retry += 1
            step.status = "queued"
            updated_step = update_batch_step(step)
            run_step(updated_step)
            break
            
    if len(get_prompt_queue_currently_running(server_id))==0 and len(get_prompt_queue_queue(server_id))<=0:
        check_batch_requests()
        

def get_selection_items_from_batch_request(run):
    nodes = json.loads(run.nodes_values)
    selection_items = []
    for node in nodes:
        fields = node["fieldValues"]
        for field_name in fields.keys():
            field = fields[field_name]
            if not field["linkField"]:
                selection_item = {}
                selection_item["nodeId"] = node["id"]
                selection_item["fieldName"] = field["fieldName"]
                selection_item["fieldType"] = field["fieldType"]
                selection_item["nodeType"] = node["className"]
                if "filteredSelectedSets" in field.keys():
                    selection_item["filteredSelectedSets"] = field["filteredSelectedSets"]
                selection_items.append(selection_item)
    return selection_items
            

def get_selection_items_from_step(batch_request, step):
    run_sel_items = get_selection_items_from_batch_request(batch_request)
    
    step_sel_items = []
    
    #get the values
    nodes_values = json.loads(step.run_value)["prompt"]
    for node_key in nodes_values:
        node_value = nodes_values[node_key]
        node_run_sel_items = [x for x in run_sel_items if x["nodeId"] == node_key]
        for run_sel_item in node_run_sel_items:
            for field_key in node_value["inputs"]:
                if field_key == run_sel_item["fieldName"]:
                    field_value = node_value["inputs"][field_key]
                    run_sel_item["value"] = field_value
                
               
    #get the selection items via value
    for run_sel_item in run_sel_items:
        if "value" in run_sel_item:
            sel_item = get_selection_item_by_node_field_value(run_sel_item["nodeType"], run_sel_item["fieldType"], run_sel_item["value"])
            if sel_item:
                run_sel_item["uuid"] = sel_item["uuid"]
                step_sel_items.append(run_sel_item)
            
    return step_sel_items
    

def check_batch_requests_finished(batch_request):    
    if batch_request.total == batch_request.current:
        runs = get_batch_steps_by_statuses_other_than(batch_request.uuid, ["finished","failed","invalid"])
        if not runs:
            batch_request.status = "finished"
            batch_request.end_time = datetime.datetime.now();
            update_batch_request(batch_request)
            #server.PromptServer.instance.send("executionFinished", batch_request.uuid, batch_request.client_id)

            send_socket_message("executionFinished",{"batch_request_uuid": batch_request.uuid}, batch_request.client_id)
            return True
    return False


def check_batch_requests_finished_uuid(uuid):
    batch_request = get_batch_request_by_id(uuid)
    check_batch_requests_finished(batch_request)

def check_batch_requests():      
    batch_requests = get_batch_requests_by_statuses(["queued", "running"])
    queued_something = False
    added = False
    for batch_request in batch_requests:
        if check_batch_requests_finished(batch_request):
            continue
        if added:
            if batch_request.status!="queued":
                batch_request.status = "queued"
                update_batch_request(batch_request)
            continue
        step = batch_request.current+1
        # if this happens it basically means we're waiting for some failed steps to retry
        if step > batch_request.total and batch_request.total>0:            
            continue
        # have to execute the next result
        added = execute_step_of_batch_request(batch_request, step)
        if batch_request.status!="running":
            batch_request.status = "running"
            update_batch_request(batch_request)
        queued_something = True

def execute_step_of_batch_request(batch_request, step):
    try: 
         contents = create_prompt_for_step(batch_request, step, False)
         #this is to be able to show it also in ui
         extra_data = {}
         extra_data["client_id"] = contents["client_id"]
         enqueue_step(batch_request.uuid, batch_request.order, contents, extra_data, step, 1)
         batch_request.current = step
         update_batch_request(batch_request)
         return True
    except:
        return False

def enqueue_step(batch_request_uuid, priority, comfy_content, extra_data, curr_step, server_id):
    step = {}
    step_uuid = str(uuid.uuid4())
    step["uuid"] = step_uuid
    step["batch_request_uuid"] = batch_request_uuid
    step["status"] = "queued"
    step["server"] = server_id
    step["step"] = curr_step
    step["run_value"] = make_json(comfy_content)
    inserted_step = insert_batch_step(step)
    run_step(inserted_step)
    
    return True

def run_step_uuid(step_uuid):
    step = get_batch_step_by_id(step_uuid)
    run_step(step)

def run_step(step):
    comfy_content = json.loads(step.run_value)
    extra_data = {}
    extra_data["client_id"] = comfy_content["client_id"]
    run = get_batch_request_by_id(step.batch_request_uuid)
    priority = run.order
    valid = execution.validate_prompt(comfy_content["prompt"])
    if valid[0]:
        outputs_to_execute = valid[2]
        prompt_queue_put(1, priority, step.uuid, comfy_content["prompt"], extra_data, outputs_to_execute)
    else:
        error = {"error": valid[1], "node_errors": valid[3]}
        step["error"] = make_json(error);
        step["status"] = "invalid"
        update_batch_step(step)
    
    

def enqueue_prompt_by_type(client_id, workflow, api_uuid=None, job_uuid=None, run_mode=None, preset=None, override_values=None, secondary_uuid=None, start_pos=-1):
    # check if we need to return the values after the steps changes or keep the current ones
    if not isinstance(workflow, dict):
        workflow = model_to_dict(workflow)
        

    settings_obj = json.loads(workflow["settings"])
    
    contents_obj = workflow["contents"]
    sequence_fields_config = settings_obj["sequenceFields"]
    run_settings = settings_obj["runSettings"]
    
    if not run_mode:
        run_mode = settings_obj["selectedRunMode"]
        
    
    
    curr_run_settings = run_settings[run_mode]
    
    

    run_mode = curr_run_settings["runMode"]
    return_values_after_steps = run_mode in ["qs", "q", "lq"]
    
   
    nodes = json.loads(workflow["nodes_values"])
    #apply preset 
    if preset:
        for node_preset in preset:
            for node in nodes:
                if node["className"] == node_preset["nodeType"]:
                    for field_name, field_value in node_preset["fieldValues"].items():
                        if field_name in node["fieldValues"].keys():
                            for field_setting in field_value:
                                node["fieldValues"][field_name][field_setting] = field_value[field_setting]
                    break
    #make the sequence fields list
    sequence_fields = create_new_sequence_field(sequence_fields_config, nodes)

    #make the root prompt object, from which we will derive the secondary ones
    root_prompt = make_root_prompt(client_id, nodes, sequence_fields, override_values, start_pos)
    #validate the root prompt
    root_valid = execution.validate_prompt(root_prompt["prompt"])
    if not root_valid[0]:
        print("invalid prompt:", root_valid[1])
        return {"error": root_valid[1], "error_type":"comfy_validation", "node_errors": root_valid[3]}

    order = get_batch_requests_max_order()
    if not order:
        order = 0
    total_cnt = 1
    order = order +1
    numberOfRuns = curr_run_settings["numberOfRuns"]
    if not numberOfRuns:
        numberOfRuns = 1
    numberOfSteps = curr_run_settings["numberOfSteps"]
    if not numberOfSteps:
        numberOfSteps = 1
    
    if run_mode == "q":
        if curr_run_settings["infinite"]:
            total_cnt = -1
            curr_run_settings["numberOfRuns"]
        else:
            total_cnt = numberOfRuns
            del curr_run_settings["infinite"]
    elif run_mode == "lq":
        total_cnt = numberOfRuns
    elif run_mode == "qs":
        total_cnt = numberOfRuns * numberOfSteps
    elif run_mode == "qa":
        total_cnt = numberOfRuns
        if curr_run_settings["infinite"]:
            total_cnt = -1
        else:
            for sequence_field in sequence_fields:
                if not sequence_field["transparentSequence"]:
                    length = sequence_field["col"]["#"]
                    print(sequence_field["fieldName"],sequence_field["sequence"],sequence_field["value"], sequence_field["sequencePosition"], length )
                    if length != sequence_field["sequenceTotalCnt"]:
                        return {"error": "sequence field collection length does not match the total count"}
                    
                    # if curr_run_settings["startFromCurrent"]:
                    #     if sequence_field["sequence"] == "increment":
                    #         total_cnt *= length - sequence_field["sequencePosition"]
                    #     elif sequence_field["sequence"] == "decrement":
                    #         if sequence_field["sequencePosition"]==-1:
                    #             total_cnt *= length+1
                    #         else:
                    #             total_cnt *= sequence_field["sequencePosition"]+1
                    # else:
                    if True:
                           total_cnt *= sequence_field["col"]["#"]
        
    create_date =  datetime.datetime.now()
    start_date = None
    end_date = None
    status = "queued"
    if total_cnt == 0:
        return {"error": "total count is 0", "error_type":"count_zero"}
        
    name = curr_run_settings["nameRun"]
    del curr_run_settings["nameRun"]
    tags = curr_run_settings["tagsRun"]
    del curr_run_settings["tagsRun"]
    del curr_run_settings["askForNameEachRun"]

    
    curr_run_settings["sequenceFields"] = sequence_fields_config
    
    prompt_uuid = workflow["uuid"]
    
        
    # find all sequence_fields that are not transparent and return the product of all their total counts
    # for sequence_field in sequence_fields:
    #     if not sequence_field.transparentSequence:
    #         total_cnt *= sum([x["cnt"] for x in calculate_collection(sequence_field)])
    print("order",order)
    # some cleanup before saving, visual info is not useful
    for node in nodes:
        cleanup_node(node)
   
    new_uuid = uuid.uuid4()
    return {"uuid": new_uuid,
            "client_id": client_id,
            "workflow_uuid": prompt_uuid,
            "api_uuid": api_uuid,
            "job_uuid": job_uuid,
            "secondary_uuid":secondary_uuid,
            "name": name,
            "tags": tags,
            "status": "queued",
            "run_settings": make_json(curr_run_settings),
            "order": order,
            "total": total_cnt, 
            "run_type": run_mode,
            "current": 0, 
            "create_date": create_date,
            "update_date": create_date,
            "start_date": start_date,
            "end_date": end_date,
            "contents": contents_obj,
             "nodes_values": make_json(nodes),
            "run_values": make_json(root_prompt),
    }
   



     
def create_prompt_for_step(batch_request, step, include_pos):
    contents = json.loads(batch_request.run_values) 
   
    total = batch_request.total
    run_settings = json.loads(batch_request.run_settings)
    run_mode = run_settings["runMode"]
    number_of_runs = run_settings["numberOfRuns"]
    infinite = False
    if "infinite" in run_settings.keys():
        infinite = run_settings["infinite"]
    do_runs_in_sequence = run_settings["doRunsInSequence"]
    nodes = json.loads(batch_request.nodes_values)
    root_prompt = json.loads(batch_request.run_values)
     
    sequence_fields = run_settings["sequenceFields"]
    sequence_fields.sort(key=lambda x: x["order"],reverse = True)
    node_values = []
    non_transparent_sequence_fields = [x for x in sequence_fields if not x["transparentSequence"] and x["hasSequence"]]
     
    transparent_sequence_fields = [x for x in sequence_fields if x["transparentSequence"] and x["hasSequence"]]
    for field in transparent_sequence_fields:
        modify_comfy_node(contents, nodes, field["nodeId"], field["fieldName"], step-1, include_pos)
         
    remaining = step-1
    if not infinite:
        if not do_runs_in_sequence:
             # this makes them all run the ones with same non transparent parameters run one after the other
            remaining = (remaining - (remaining%number_of_runs))/number_of_runs
    if run_mode in ["qa", "qs", "lq"]:
        for field in non_transparent_sequence_fields:
            node = [x for x in nodes if x["id"]==field["nodeId"]][0]
            orig_field = node["fieldValues"][field["fieldName"]]
            total = orig_field["col"]["#"]
            transp_step = remaining%total
            remaining = (remaining-transp_step)/total
            if run_mode in ["qs", "lq"]:
                if transp_step + field["sequencePosition"] >= total:
                    remaining += 1
            modify_comfy_node(contents, nodes, field["nodeId"], field["fieldName"], transp_step, include_pos)
    return contents

def get_values_and_pos_from_prompt(prompt):
    nodes = {}
    for key, value in prompt["prompt"].items():
        node = {}
        nodes[key] = node
        inputs = value["inputs"]
        for key2, value2 in inputs.items():
            if "pos" in value.keys() and key2 in value["pos"].keys():
                node[key2] = {"value":value2, "pos":value["pos"][key2]}
    return nodes

def modify_comfy_node(contents, nodes, nodeId, fieldName, step, include_pos):
    node = [x for x in nodes if x["id"]==nodeId][0]
    field = node["fieldValues"][fieldName]
    value = get_value_from_sequence_fields(field, step)
    comfy_node = contents["prompt"][str(node["id"])]
    comfy_node["inputs"][field["fieldName"]] = value["v"]
    if include_pos:
        if "pos" not in comfy_node.keys():
            comfy_node["pos"] = {}
        comfy_node["pos"][field["fieldName"]] = int(value["p"])

def execute_step_of_batch_request_uuid(uuid, step):
    batch_request = get_batch_request_by_id(uuid)
    return execute_step_of_batch_request(batch_request, step)


            



            
def cleanup_node(node):
    del node["xclass"]
    del node["nodeHidden"]
    del node["selectedNode"]
    del node["order"]
    for key, value in node["fieldValues"].items():
        cleanup_field(value)

def cleanup_field(field):
    del field["label"]
    del field["fieldSelected"]
    del field["hidden"]            
    if "node" in field.keys():
        del field["node"]
        keys = set(field.keys())
        for key in keys:
            if key.startswith("hide"):
                del field[key]


def make_root_prompt(client_id, nodes,sequence_fields, override_values, start_pos):
    root_prompt = {}
    root_prompt["client_id"] =client_id
    nodes_array = {}
    root_prompt["prompt"] = nodes_array
    for node in nodes:
        node_prompt = {}
        node_id = str(node["id"]);
        if override_values:
            if node_id in override_values.keys():
                for field_name, field in node["fieldValues"].items():
                    if field_name in override_values[node_id].keys():
                        field["value"] = override_values[node_id][field_name]["value"]
                        #field["sequence"] = override_values[node_id][field_name]["sequence"]
        nodes_array[str(node["id"])] = node_prompt
        node_prompt["class_type"] = node["className"]        
        inputs = {}
        node_prompt["inputs"] = inputs
        for field_name, field in node["fieldValues"].items():
            if field["linkField"]:
                if "fieldKeys" in field.keys() and "slot" in field["fieldKeys"].keys():
                    fieldKeys = field["fieldKeys"]
                    inp = [str(fieldKeys["id"]), fieldKeys["slot"]]
                    inputs[field_name] = inp;
            else:
                #find if the field is in the sequence_fields list
                found = False
                for sequence_field in sequence_fields:
                    if sequence_field["fieldName"] == field_name and node["id"]==sequence_field["node_id"]:
                        found = sequence_field
                        break
                if not found:
                    inputs[field_name] = field["value"]
                else:
                    # if start_from_current:
                    #      field["start_from_current"] = True
                    sequence_value = get_value_from_sequence_fields(field, start_pos)
                    inputs[field_name] = sequence_value['v']
                    found["sequencePosition"] = sequence_value['p']
                field["value"] = inputs[field_name]
                
    return root_prompt

def calculate_collection(field):
    collection = []
    # start_from_current = False
    # if "start_from_current" in field.keys():
    #     start_from_current = field["start_from_current"]
    
    #try to get the collection from the field
    if "filteredSelectedSets" in field.keys():
        collection = field["filteredSelectedSets"]
   
    interval_def = None
    # if it's select field and it has negate (why did i ever implement this feature?) I must negate the list
    if field["fieldType"] == "SELECT":
        collection = [{"#": x["count"], "v": x["comfy_name"]} for x in collection]
        if "negateList" in field.keys() and field["negateList"]:
            main_list = get_selectiondata_by_type(field["fieldName"], field["nodeType"])
            if main_list:
                main_list = main_list["data"]
                collection = [x["v"] for x in collection]
                collection = list(set(main_list) - set(collection))
                collection = [{"#": 1, "v": x} for x in collection]
        if len(collection)==0:
            main_list = get_selectiondata_by_type(field["fieldName"], field["nodeType"])
            if main_list:
                main_list = main_list["data"]
                collection = set(main_list)
                collection = [{"#": 1, "v": x} for x in collection]
            
    
    #if it's an int field I have to split the values
    elif field["fieldType"] == "INT" or field["fieldType"] == "FLOAT":
        if field["optionSelected"] == "Select":
            text = field["valuesComboText"]
            if text:                
                collection = [x.strip() for x in text.split(",") if x.strip()]
        elif field["optionSelected"] == "Interval" or (field["optionSelected"] == "Simple" and field["optionMode"] == "Advanced"):
            minValue = field["minValue"]
            maxValue = field["maxValue"]
            stepValue = field["stepValue"]
            if "minValueInterval" in field.keys():
                minValue = field["minValueInterval"]
            if "maxValueInterval" in field.keys():
                maxValue = field["maxValueInterval"]
            if "stepValueInterval" in field.keys():
                stepValue = field["stepValueInterval"]
            interval_def = {"n": minValue, "x": maxValue, "s": stepValue}
        else:
            minValue = field["minValue"]
            maxValue = field["maxValue"]
            stepValue = field["stepValue"]
            interval_def = {"n": minValue, "x": maxValue, "s": stepValue}
        if field["fieldType"] == "INT":
            collection = [int(x) for x in collection]
        if field["fieldType"] == "FLOAT":
            collection = [float(x) for x in collection]
        collection = [{"#": 1, "v": x} for x in collection]    
    
    elif field["fieldType"] == "STRING":
        collection = [{"#": x["count"], "v": x["text"]} for x in collection]
    
    elif field["fieldType"] == "BOOLEAN":
        collection = [{"#": 1, "v": False}, {"#": 1, "v": True}]
    
   

    #if value is not present in collection then we add it to the beginning
    has_custom = None 
    if not interval_def:
        if field["fieldType"] == "INT":
            if int(field["value"]) not in [int(x["v"]) for x in collection]:
                has_custom = int(field["value"])
        elif field["fieldType"] == "FLOAT":
            if float(field["value"]) not in [float(x["v"]) for x in collection]:
                has_custom = float(field["value"])
        elif field["fieldType"] == "BOOLEAN":
            if bool(field["value"]) not in [bool(x["v"]) for x in collection]:
                has_custom = bool(field["value"])
        else:
            if str(field["value"]) not in [str(x["v"]) for x in collection]:
                has_custom = str(field["value"])
    else:
        if field["fieldType"] == "INT":
            if (int(field["value"])-interval_def["n"]) % interval_def["s"]!=0:
                has_custom = int(field["value"])
        elif field["fieldType"] == "FLOAT":
            if (float(field["value"])-interval_def["n"]) % interval_def["s"]!=0:
                has_custom = float(field["value"])

    total = sum([x["#"] for x in collection])
    result = {"c":collection,"#": total}
    if interval_def:
        result["i"] = interval_def
        result["#"] = math.floor((interval_def["x"] - interval_def["n"])/interval_def["s"]+1)
    if has_custom is not None:
        result["?"] = has_custom
        result["#"] +=1
    return result

def calculate_collection_for_workflow_field(workflow_uuid, node_id, field_name):
    field = get_field_by_workflow_node_field(workflow_uuid, node_id, field_name)
    return calculate_collection(field)
    
def get_field_by_workflow_node_field(workflow_uuid, node_id, field_name):
    node = get_node_by_workflow_node(workflow_uuid, node_id)
    if not node:
        return None
    return node["fieldValues"][field_name]

def get_node_by_workflow_node(workflow_uuid, node_id):
    workflow = get_workflow(workflow_uuid)
    if(workflow.nodes_values):
        contents = json.loads(workflow.nodes_values)
        return [x for x in contents if str(x["id"])==node_id][0]
    return None
    
    
def get_value_from_sequence_fields(field, step):
    collection = None
    if "col" not in field.keys():
        # this should only happen once, at init
        if step!=-1:
            print("Collection initialization when step is not -1")
        collection = calculate_collection(field)
        field["col"] = collection
    else:
        collection = field["col"]
    if step==-1:
        step = 0
    start_pos = field["sequencePosition"]
    sequence = field["sequence"]
    return get_value_from_collection(collection, sequence, start_pos, step)



def get_value_from_collection(collection, sequence, start_pos, step):
    total_collection_count = collection["#"]
    if "?" in collection.keys():
        start_pos+=1
    

    curr_pos = start_pos % total_collection_count 
    step = step % total_collection_count
    if sequence == "randomize":        
        if step!=0:
                curr_pos = random.randint(0, total_collection_count-1)
    if sequence == "increment":
        curr_pos = (curr_pos + step) % total_collection_count
    if sequence == "decrement":
        curr_pos = (total_collection_count + curr_pos - step) % total_collection_count
     
        
    if curr_pos == 0 and "?" in collection.keys():
        return {'p': -1, 'v': collection["?"], 'c':collection, 't':1}
    
    if "?" in collection.keys():
        curr_pos -= 1
    pos = curr_pos
    if "i" in collection.keys():
        interval_def = collection["i"]
        value = (interval_def["n"] + interval_def["s"] * curr_pos)
        return {'p': curr_pos, 'v': value, 'c':collection, 't':total_collection_count}
    else:
        for item in collection["c"]:
            pos -= item["#"]
            if pos < 0:
                return {'p': curr_pos, 'v': item["v"], 'c':collection, 't':total_collection_count}
        
def create_new_sequence_field(sequence_fields_config, nodes):
    # order by sequence_fields_config by order property
    ordered_sequence_fields_config = [x for x in sequence_fields_config if x["hasSequence"]]
    ordered_sequence_fields_config.sort(key=lambda x: x["order"])
    sequence_fields = []
    nontransparent_fields = []
    transparent_fields = []
    for node in nodes:
        for field_name, field in node["fieldValues"].items():
            #the fields may still have a sequence attribute, but we will not use it if they are not in correct view mode
            check_sequence = False
            if field["fieldType"]=='SELECT' or field["fieldType"]=='STRING':
                if field["optionMode"]=='Advanced' or field["optionSelected"]=='Select':
                    check_sequence = True           
            elif field["fieldType"]=='FLOAT' or field["fieldType"]=='INT':
                if field["optionMode"]!='Basic' or field["optionSelected"]!='Simple':
                    check_sequence = True
            elif field["fieldType"]=='BOOLEAN':
                if field["optionMode"]!='Basic' or field["optionSelected"]!='Simple':
                    check_sequence = True
            elif not field["linkField"]:
                #useful to catch any new field types that are added
                print(field)
            if check_sequence and field["sequence"]:
                field["node_id"] = node["id"]
                field["node"] = node
                if(field["sequence"]=="randomize" or (field["sequence"]!="fixed" and field["transparentSequence"])):
                    transparent_fields.append(field)
                elif field["sequence"]!="fixed" and not field["transparentSequence"]:
                    nontransparent_fields.append(field)
    
    #make new sequence fields list based on the sequence_fields_config order and the fields that are not in the sequence_fields_config
    to_remove = []
    #put first the fields that are in the sequence_fields_config and are not transparent
    for sequence_field in ordered_sequence_fields_config:
        for field in nontransparent_fields:
            if field["node_id"] == sequence_field["nodeId"] and field["fieldName"]==sequence_field["fieldName"]:
                sequence_fields.append(field)
                field["transparentSequence"] = False
                if field not in to_remove:
                    to_remove.append(field)
                break
            
    for field in to_remove:
        nontransparent_fields.remove(field)
    # add the rest of the nontransparent fields
    for field in nontransparent_fields:
        field["transparentSequence"], False
        sequence_fields.append(field)
    
    #put the transparent fields in the sequence_fields list
    to_remove = []
    for sequence_field in ordered_sequence_fields_config:
        for field in transparent_fields:
            if field["node_id"] == sequence_field["nodeId"] and field["fieldName"]==sequence_field["fieldName"]:
                field["transparentSequence"] = True
                sequence_fields.append(field)                
                if field not in to_remove:
                    to_remove.append(field)
                break
            
    for field in to_remove:
        transparent_fields.remove(field)
    
    # add the rest of the nontransparent fields
    for field in transparent_fields:
        field["transparentSequence"] = True
        sequence_fields.append(field)
    return sequence_fields