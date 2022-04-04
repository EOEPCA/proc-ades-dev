import os
import shutil
import json


try:
    import zoo
except ImportError:
    print("Not running in zoo instance")

    class ZooStub(object):
        def __init__(self):
            self.SERVICE_SUCCEEDED = 3
            self.SERVICE_FAILED = 4

        def update_status(self, conf, progress):
            print(f"Status {progress}")

        def _(self, message):
            print(f"invoked _ with {message}")

    conf = {}
    conf["lenv"] = {"message": ""}
    zoo = ZooStub()
    pass


class UndeployService(object):
    def __init__(self, conf, inputs, outputs):

        self.conf = conf
        self.inputs = inputs
        self.outputs = outputs
        self.zooservices_folder = self.get_zoo_services_folder()
        self.service_identifier = self.get_application_package_identifier()


    def _get_conf_value(self, key, section="main"):

        if key in self.conf[section].keys():
            return self.conf[section][key]
        else:
            raise ValueError(f"{key} not set, check configuration")

    def get_zoo_services_folder(self):
        zooservices_folder = self._get_conf_value(
            key="CONTEXT_DOCUMENT_ROOT", section="renv"
        )
        return zooservices_folder


    def get_application_package_identifier(self):

        if "applicationPackageIdentifier" not in self.inputs.keys():
            raise ValueError("The inputs dot not include the applicationPackageIdentifier")

        applicationPackageIdentifier = self.inputs["applicationPackageIdentifier"]["value"]
        return applicationPackageIdentifier




    def remove_service(self):
        service_folder = os.path.join(self.zooservices_folder, self.service_identifier)
        if os.path.isdir(service_folder):
            shutil.rmtree(service_folder)

        service_configuration_file = f"{service_folder}.zcfg"
        if os.path.exists(service_configuration_file):
            os.remove(service_configuration_file)



def UndeployProcess(conf, inputs, outputs):

    undeploy_process = UndeployService(conf, inputs, outputs)

    undeploy_process.remove_service()

    response_json ={
        "message":f"Service {undeploy_process.service_identifier} successfully undeployed.",
        "service":undeploy_process.service_identifier,
        "status": "success"
    }

    outputs["undeployResult"]["value"]=json.dumps(response_json)

    return zoo.SERVICE_SUCCEEDED