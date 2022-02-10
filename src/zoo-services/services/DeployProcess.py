from msilib.schema import Error
import os
import zoo
from cookiecutter.main import cookiecutter
import sys
from distutils.dir_util import copy_tree
import shutil

def DeployProcess(conf,inputs,outputs):

    serviceName = inputs["servicename"]["value"]
    print(f"Creating {serviceName}",file=sys.stderr)
    try:

        # cookicutter_output_dir= "/usr/lib/cgi-bin"
        cookicutter_output_dir= "/tmp"
        zooservices_folder="/usr/lib/cgi-bin"

        print(f"calling cookicutter ",file=sys.stderr)
        # Create project from local template
        if not os.access(zooservices_folder, os.W_OK):
             errorMsg = f"cookicutter cannot write to /usr/lib/cgi-bin"
             print(errorMsg,file=sys.stderr)
             raise Exception(errorMsg)

        path =  cookiecutter('/usr/lib/cgi-bin/assets/cookiecutter-templates/serviceTemplate',
                    extra_context={'serviceName': serviceName, },
                    output_dir=cookicutter_output_dir,
                    no_input=True,
                    config_file="/usr/lib/cgi-bin/assets/cookiecutter_config.yaml",
                    overwrite_if_exists=True
                    )

        # Create project from the cookiecutter-pypackage.git repo template
        #cookiecutter('https://git.terradue.com/fbrito/test-runner-template.git')

        # copy service contents to /usr/lib/cgi-bin
        copy_tree(path, zooservices_folder)

        # removing directory
        shutil.rmtree(path)


        print(f"cookicutter called",file=sys.stderr)
        outputs["Result"]["value"]=f"Service {serviceName} was successfully deployed in {path}"
        return zoo.SERVICE_SUCCEEDED
    except Exception as error:
        errorMsg = f"An error occured during the deploy of service {serviceName}: {error}"
        print(errorMsg,file=sys.stderr)
        raise error
        
        # if I return the SERVICE_FAILED the error will not be shown in the response
        #outputs["Result"]["value"]=errorMsg
        #return zoo.SERVICE_FAILED
