import zoo
from cookiecutter.main import cookiecutter
import sys

def DeployProcess(conf,inputs,outputs):
    serviceName = inputs["servicename"]["value"]
    print(f"Creating {serviceName}",file=sys.stderr)
    try:
        print(f"calling cookicutter ",file=sys.stderr)
        # Create project from local template
        path =  cookiecutter('/usr/lib/cgi-bin/assets/cookiecutter-templates/serviceTemplate',
                    extra_context={'serviceName': serviceName},
                    output_dir="/usr/lib/cgi-bin",
                    no_input=True)

        # Create project from the cookiecutter-pypackage.git repo template
        #cookiecutter('https://git.terradue.com/fbrito/test-runner-template.git')

        print(f"cookicutter called",file=sys.stderr)


        outputs["Result"]["value"]=f"Service {serviceName} was successfully deployed in {path}"
        return zoo.SERVICE_SUCCEEDED
    except:
        outputs["Result"]["value"]=f"An error occured during the deploy of service {serviceName}"            
        return zoo.SERVICE_FAILED
