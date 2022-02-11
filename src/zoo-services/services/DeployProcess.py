import os
import zoo
from cookiecutter.main import cookiecutter
import sys
from distutils.dir_util import copy_tree
import shutil
import json
import urllib.request
from pathlib import Path

def DeployProcess(conf, inputs, outputs):

    zooservices_folder = "/usr/lib/cgi-bin"
    tmpFolder= "/tmp"


    #print(json.dumps(inputs , indent=4, sort_keys=True), file=sys.stderr)
    #TODO check of Mimetype
    applicationPackageUrl = json.loads(inputs["applicationPackage"]["value"])["href"]
    processId=conf["lenv"]["usid"]

    # for the moment I am retrieving the workflow id from the filename
    # but it should be retrieve from the cwl content with the version
    applicationPackageName = Path(applicationPackageUrl).stem


    print(f"applicationPackageUrl: {applicationPackageUrl}", file=sys.stderr)
    print(f"processId: {processId}", file=sys.stderr)
    print(f"applicationPackageName: {applicationPackageName}", file=sys.stderr)
    
    # creating the folder where we will download the applicationPackage
    tmpFolderApplicationPackage1 = os.path.join(tmpFolder, f"{applicationPackageName}-{processId}")
    os.mkdir(tmpFolderApplicationPackage1)
    tmpFolderApplicationPackage2 = os.path.join(tmpFolderApplicationPackage1, applicationPackageName)
    os.mkdir(tmpFolderApplicationPackage2)

    # downloading the application package
    applicationPackageFile = os.path.join(tmpFolderApplicationPackage2,f"{applicationPackageName}.cwl")
    urllib.request.urlretrieve(applicationPackageUrl,applicationPackageFile)
    

    # retrieving service name
    serviceName = applicationPackageName
    print(f"Creating {serviceName}", file=sys.stderr)
    try:

        # Checking if zoo can write in the servicePath
        if not os.access(zooservices_folder, os.W_OK):
            errorMsg = f"cookicutter cannot write to /usr/lib/cgi-bin"
            print(errorMsg, file=sys.stderr)
            raise Exception(errorMsg)

        # Create project from local template
        print(f"calling cookicutter ", file=sys.stderr)
        path = cookiecutter('/usr/lib/cgi-bin/assets/cookiecutter-templates/serviceTemplate',
                            extra_context={'serviceName': serviceName, },
                            output_dir=tmpFolderApplicationPackage1,
                            no_input=True,
                            config_file="/usr/lib/cgi-bin/assets/cookiecutter_config.yaml",
                            overwrite_if_exists=True
                            )

        # Create project from the cookiecutter-pypackage.git repo template
        # cookiecutter('https://git.terradue.com/fbrito/test-runner-template.git')

        # copy service contents to /usr/lib/cgi-bin
        copy_tree(path, zooservices_folder)

        # removing tmp directory
        shutil.rmtree(path)
        shutil.rmtree(tmpFolderApplicationPackage1)

        print(f"cookicutter called", file=sys.stderr)
        outputs["deployResult"]["value"] = f"Service {serviceName} was successfully deployed in {zooservices_folder}"
        return zoo.SERVICE_SUCCEEDED
    except Exception as error:
        errorMsg = f"An error occured during the deploy of service {serviceName}: {error}"
        print(errorMsg, file=sys.stderr)
        raise error

        # if I return the SERVICE_FAILED the error will not be shown in the response
        # outputs["Result"]["value"]=errorMsg
        # return zoo.SERVICE_FAILED
