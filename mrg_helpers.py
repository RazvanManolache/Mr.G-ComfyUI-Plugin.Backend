import folder_paths
import comfy
import os
import uuid
import nodes
import server
import asyncio
import json
import copy

from pathlib import PurePath, Path
from aiohttp import web
from comfy_extras import nodes_mask,nodes_post_processing,nodes_custom_sampler,nodes_model_downscale,nodes_images,nodes_model_advanced,nodes_compositing

from .mrg_database import *

class Empty(dict):
    pass   


async def send_socket_message_internal(message_type, msg, client_id):
    await server.PromptServer.instance.send(message_type, msg, client_id)

def send_socket_message(message_type, msg, client_id):
    asyncio.run(send_socket_message_internal(message_type, msg, client_id))

def to_json(data):
    return json.dumps(data, default=str)

def json_response(data):
    status = 200
    if isinstance(data, dict):
        if "error" in data.keys():
            status = 400
        if "status" in data.keys():
            status = data["status"]
    return web.json_response(data, content_type='application/json',status=status, dumps=to_json)

def remove_not_needed_properties(cls, dic):
    props = dir(cls)
    keys = list(dic.keys())
    for key in keys:
        if key not in props:
            del dic[key]

def selection_item_get_internal(field_type, node_type):    
    db_data = []
    mapping  = get_selectiondata_by_type(field_type, node_type)
    if mapping != None:
        db_data = list(get_selection_items(field_type, mapping["cls"]).dicts())
        if mapping["type"] !=2 :
            should_refresh_dbdata = False
            for entry in mapping["data"]:
                found = False
                for row in db_data:
                    if row["comfy_name"] == entry:
                        found = True
                            
                        
                
                if not found:
                    should_refresh_dbdata = True
                    if mapping["type"] == 0 :
                        path = PurePath(entry)
                        #TODO: try to also get images from these subfolders
                        selection_items.insert(uuid=uuid.uuid4(), 
                                              name=path.name,
                                              path= path.parents[0],
                                              alias=path.name,
                                              comfy_name=entry, 
                                              text=entry, 
                                              field_type = field_type,
                                              node_type = mapping["cls"] ).execute()                    
                    else:
                        selection_items.insert(uuid=uuid.uuid4(), 
                                              name=entry, 
                                              alias=entry,
                                              comfy_name=entry, 
                                              text=entry, 
                                              field_type = field_type,
                                              node_type = mapping["cls"] ).execute()
            if should_refresh_dbdata:
                db_data = list(get_selection_items(field_type, mapping["cls"]).dicts())
            db_data = list(filter(lambda row: row["comfy_name"] in mapping["data"], db_data))
        else:
            db_data = list(get_selection_items(field_type, "*").dicts())
    return db_data

class ComfyTypeMapping(dict):
    def __init__(self, field, cls , type, alias):
        dict.__init__(self, field=field, cls=cls, type=type, alias=alias, data=[])
    def refresh_data(self):
        if self["type"]==0:
            self["data"] = folder_paths.get_filename_list(self["alias"])
        if self["type"]==1:
            self["data"] = eval(self["alias"])
        


        
ComfyTypeMappings = [
    ComfyTypeMapping("MRG_STRING","", 2, "STRING"),
    ComfyTypeMapping("MRG_INT","", 2, "INT"),
    ComfyTypeMapping("MRG_FLOAT","", 2, "FLOAT"),
    ComfyTypeMapping("MRG_PRESET","", 2, "PRESET"),


    ComfyTypeMapping("upscale_method","LatentUpscaleBy", 1, "nodes.LatentUpscaleBy.upscale_methods"),
    ComfyTypeMapping("image","", 1, "nodes.LoadImage.INPUT_TYPES()['required']['image'][0]"),
    ComfyTypeMapping("image","LoadImageMask", 1, "nodes.LoadImageMask.INPUT_TYPES()['required']['image'][0]"),
    ComfyTypeMapping("channel","LoadImageMask", 1, "nodes.LoadImageMask._color_channels"),
    ComfyTypeMapping("upscale_method","ImageScale", 1, "nodes.ImageScale.upscale_methods"),
    ComfyTypeMapping("upscale_method","ImageScaleBy", 1, "nodes.ImageScaleBy.upscale_methods"),
    ComfyTypeMapping("set_cond_area","ConditioningSetMask", 1, "nodes.ConditioningSetMask.INPUT_TYPES()['required']['set_cond_area'][0]"),
    ComfyTypeMapping("add_noise","KSamplerAdvanced", 1, "nodes.KSamplerAdvanced.INPUT_TYPES()['required']['add_noise'][0]"),
    ComfyTypeMapping("return_with_leftover_noise","KSamplerAdvanced", 1, "nodes.KSamplerAdvanced.INPUT_TYPES()['required']['return_with_leftover_noise'][0]"),
    ComfyTypeMapping("rotation","LatentRotate", 1, "nodes.LatentRotate.INPUT_TYPES()['required']['rotation'][0]"),
    ComfyTypeMapping("flip_method","LatentFlip", 1, "nodes.LatentFlip.INPUT_TYPES()['required']['flip_method'][0]"),
    ComfyTypeMapping("model_path","DiffusersLoader", 1, "nodes.DiffusersLoader.INPUT_TYPES()['required']['model_path'][0]"),
    ComfyTypeMapping("latent","LoadLatent", 1, "nodes.LoadLatent.INPUT_TYPES()['required']['latent'][0]"),
    ComfyTypeMapping("mode","PorterDuffImageComposite", 1, "nodes_compositing.PorterDuffImageComposite.INPUT_TYPES()['required']['mode'][0]"),
   
    
    ComfyTypeMapping("channel","ImageToMask", 1, "nodes_mask.ImageToMask.INPUT_TYPES()['required']['channel'][0]"),
    ComfyTypeMapping("upscale_method","PatchModelAddDownscale", 1, "nodes_model_downscale.PatchModelAddDownscale.upscale_methods"),
    ComfyTypeMapping("method","SaveAnimatedWEBP", 1, "nodes_images.SaveAnimatedWEBP.methods"),
    ComfyTypeMapping("upscale_method","ImageScaleToTotalPixels", 1, "nodes_post_processing.ImageScaleToTotalPixels.upscale_methods"),
    ComfyTypeMapping("blend_mode","ImageBlend", 1, "nodes_post_processing.Blend.INPUT_TYPES()['required']['blend_mode'][0]"),
    ComfyTypeMapping("dither","ImageQuantize", 1, "nodes_post_processing.Quantize.INPUT_TYPES()['required']['dither'][0]"),
    ComfyTypeMapping("solver_type","SamplerDPMPP_2M_SDE", 1, "nodes_custom_sampler.SamplerDPMPP_2M_SDE.INPUT_TYPES()['required']['solver_type'][0]"),
    ComfyTypeMapping("noise_device","SamplerDPMPP_2M_SDE", 1, "nodes_custom_sampler.SamplerDPMPP_2M_SDE.INPUT_TYPES()['required']['noise_device'][0]"),
    ComfyTypeMapping("noise_device","SamplerDPMPP_SDE", 1, "nodes_custom_sampler.SamplerDPMPP_SDE.INPUT_TYPES()['required']['noise_device'][0]"),
    
    ComfyTypeMapping("sampling","ModelSamplingContinuousEDM", 1, "nodes_model_advanced.ModelSamplingContinuousEDM.INPUT_TYPES()['required']['sampling'][0]"),
    ComfyTypeMapping("downscale_method","PatchModelAddDownscale", 1, "nodes_model_downscale.PatchModelAddDownscale.INPUT_TYPES()['required']['downscale_method'][0]"),
    ComfyTypeMapping("operation","MaskComposite", 1, "nodes_mask.MaskComposite.INPUT_TYPES()['required']['operation'][0]"),


    ComfyTypeMapping("sampling","ModelSamplingDiscrete", 1, "nodes_model_advanced.ModelSamplingDiscrete.INPUT_TYPES()['required']['sampling'][0]"),

   

    ComfyTypeMapping("upscale_method","LatentUpscale", 1, "nodes.LatentUpscale.upscale_methods"),
    ComfyTypeMapping("crop","LatentUpscale", 1, "nodes.LatentUpscale.crop_methods"),

    ComfyTypeMapping("crop","ImageScale", 1, "nodes.ImageScale.upscale_methods"),
    ComfyTypeMapping("crop","ImageScale", 1, "nodes.ImageScale.crop_methods"),
    
    


    ComfyTypeMapping("hypernetwork_name","", 0, "hypernetworks"),
    ComfyTypeMapping("model_name","", 0, "upscale_models"),
    ComfyTypeMapping("ckpt_name","", 0, "checkpoints"),
    ComfyTypeMapping("config_name","", 0, "configs"),
    ComfyTypeMapping("lora_name","", 0, "loras"),
    ComfyTypeMapping("vae_name","", 0, "vae"),
    ComfyTypeMapping("control_net_name","", 0, "controlnet"),
    ComfyTypeMapping("unet_name","", 0, "unet"),
    ComfyTypeMapping("clip_name","CLIPVisionLoader", 0, "clip_vision"),
    ComfyTypeMapping("clip_name","", 0, "clip"),
    ComfyTypeMapping("clip_name1","", 0, "clip"),
    ComfyTypeMapping("clip_name2","", 0, "clip"),
    ComfyTypeMapping("style_model_name","", 0, "style_models"),
    ComfyTypeMapping("gligen_name","", 0, "gligen"),
    ComfyTypeMapping("embeddings","", 0, "embeddings"),
    ComfyTypeMapping("previewer","", 0, "vae_approx"),

    ComfyTypeMapping("sampler_name","KSampler", 1, "comfy.samplers.KSampler.SAMPLERS"),
    ComfyTypeMapping("sampler_name","KSamplerAdvanced", 1, "comfy.samplers.KSampler.SAMPLERS"),
    ComfyTypeMapping("sampler_name","", 1, "comfy.samplers.SAMPLER_NAMES"),
    ComfyTypeMapping("scheduler","KSampler", 1, "comfy.samplers.KSampler.SCHEDULERS"),
    ComfyTypeMapping("scheduler","KSamplerAdvanced", 1, "comfy.samplers.KSampler.SCHEDULERS"),
    ComfyTypeMapping("scheduler","", 1, "comfy.samplers.KSampler.SCHEDULERS"),
]        


def get_selectiondata_by_type(field, cls):
    
    filter_field =  list(filter(lambda x: x['field'] == field, ComfyTypeMappings))

    if(len(filter_field)==0):
        return None

    filter_field_cls =  list(filter(lambda x: x['cls'] == cls, filter_field))
    if(len(filter_field_cls)==0):
        filter_field_cls =  list(filter(lambda x: x["cls"] == "", filter_field))

    if(len(filter_field_cls)==0):
        raise Exception(field + " has no known mapping")

    result = filter_field_cls[0]

    result.refresh_data()

    return result