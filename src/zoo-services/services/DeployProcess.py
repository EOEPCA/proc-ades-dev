import os
import subprocess
import zoo
from cookiecutter.main import cookiecutter
import sys
from distutils.dir_util import copy_tree
import shutil
import json
import urllib.request
from pathlib import Path
import sys
from deploy_util import Process
import yaml

def create_service_tmp_folder(application_package_url, process_id, destination_folder):
    # creating the folder where we will download the applicationPackage
    tmp_folder_application_package = os.path.join(
        destination_folder,
        f"DeployProcess-{process_id}"
    )
    os.makedirs(tmp_folder_application_package)
    return tmp_folder_application_package

def download_application_package(application_package_url, destination_folder):
    # retrieving package name from filename
    application_package_name = Path(application_package_url).stem

    # downloading the application package
    application_package_file = os.path.join(
        destination_folder, f"{application_package_name}.cwl"
    )
    urllib.request.urlretrieve(application_package_url, application_package_file)
    return application_package_file

def refactor_with_service_name(application_package_file, service_tmp_folder, service_name):
    # retrieving filname
    application_package_name = Path(application_package_file).stem

    # renaming application package name with service name
    new_application_package_file = application_package_file.replace(f"{application_package_name}.cwl",f"{service_name}/{service_name}.cwl")
    os.rename(application_package_file,new_application_package_file)


    
    return new_application_package_file


def get_service_config_from_application_package(application_package_file):
    with open(application_package_file, "r") as stream:
        try:
            cwl = yaml.safe_load(stream)
            stream.close()
        except yaml.YAMLError as e:
            print("ERROR")
    
    service_zcfg = Process.create_from_cwl(cwl)
    return service_zcfg

def write_service_config(service_zcfg, destination_folder):
    # retrieving package name from filename
    application_package_name = service_zcfg.identifier
    zcfg_file = os.path.join(destination_folder, f"{application_package_name}.zcfg")
    print(zcfg_file,file=sys.stderr)

    with open(zcfg_file, 'w') as f:
        service_zcfg.write_zcfg(f)

    return zcfg_file

def check_write_permissions(zooservices_folder):
    # Checking if zoo can write in the servicePath
    if not os.access(zooservices_folder, os.W_OK):
        errorMsg = f"Cannot write to {zooservices_folder}. Please check folder"
        print(errorMsg, file=sys.stderr)
        raise Exception(errorMsg)

def generate_service_provider_from_template(deploy_template, destination_folder, cookiecutter_templates_folder, inputs=dict()):
    
    # checking if the template location is remote or local
    if deploy_template.endswith(".git"):
        template_name=Path(deploy_template).stem
        template_folder= os.path.join(cookiecutter_templates_folder,template_name)
        
        # checking if template had already been cloned
        if os.path.isdir(template_folder):
            shutil.rmtree(template_folder)

        os.system(f"git clone {deploy_template} {template_folder}" )
    else:
        template_folder=deploy_template

    # Create project from template
    path = cookiecutter(template_folder,
        extra_context={
            "workflow_id": inputs["workflow_id"],
        },
        output_dir=destination_folder,
        no_input=True,
        config_file="/tmp/cookiecutter_config.yaml",
        overwrite_if_exists=True,
        )    
    return path

def DeployProcess(conf, inputs, outputs):

    zooservices_folder = conf["renv"]["CONTEXT_DOCUMENT_ROOT"]
    tmp_folder = conf["main"]["tmpPath"]
    cookiecutter_templates_folder= "/tmp/cookiecutter-templates"
    application_package_url = json.loads(inputs["applicationPackage"]["value"])["href"]
    deploy_template = inputs["deployTemplate"]["value"]
    process_id = conf["lenv"]["usid"]

    # check if zooservices_folder is accessible
    check_write_permissions(zooservices_folder)

    # create a temporary folder where to save the application package, the zcfg and the service provider
    service_tmp_folder = create_service_tmp_folder(application_package_url, process_id, tmp_folder)

    # downloading application package to tmp folder
    application_package_file = download_application_package(application_package_url, service_tmp_folder)

    # parse cwl and generate service configuration object
    service_configuration = get_service_config_from_application_package(application_package_file)


    # retrieving service name
    service_name = service_configuration.identifier
    service_configuration.service_provider=f"{service_name}.service"
    service_configuration.service_type="Python"

    # write service configuration to file
    service_configuration_file = write_service_config(service_configuration, service_tmp_folder)

    # preparing inputs for the cookiecutter template
    cookicutter_inputs = dict()
    cookicutter_inputs["workflow_id"]=service_name

    # generate the service provider using a cookiecutter template
    service_path = generate_service_provider_from_template(deploy_template, service_tmp_folder, cookiecutter_templates_folder,cookicutter_inputs)   

    # 
    application_package_file = refactor_with_service_name(application_package_file, service_tmp_folder, service_name)

    # copy service contents to /usr/lib/cgi-bin
    copy_tree(service_tmp_folder, zooservices_folder)

    # removing service_tmp_folder
    shutil.rmtree(service_tmp_folder)
        

    return zoo.SERVICE_SUCCEEDED

