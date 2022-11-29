import os
import shutil
import json
import sys

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
        self.service_identifier = self.get_process_identifier()


    def _get_conf_value(self, key, section="main"):

        if key in self.conf[section].keys():
            return self.conf[section][key]
        else:
            raise ValueError(f"{key} not set, check configuration")

    def get_zoo_services_folder(self):
        # checking for namespace
        if "zooServicesNamespace" in self.conf and \
                "namespace" in self.conf["zooServicesNamespace"] and \
                "servicesNamespace" in self.conf and \
                "path" in self.conf["servicesNamespace"]:
            zooservices_folder = os.path.join(self.conf["servicesNamespace"]["path"],
                                              self.conf["zooServicesNamespace"]["namespace"])
        else:
            zooservices_folder = self._get_conf_value(
                key="CONTEXT_DOCUMENT_ROOT", section="renv"
            )
        return zooservices_folder


    def get_process_identifier(self):
        process_identifier = self.conf["lenv"]["deployedServiceId"]
        return process_identifier




    def remove_service(self):
        import psycopg2
        import psycopg2.extensions
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
        conn = psycopg2.connect("host=%s port=%s dbname=%s user=%s password=%s" % (self.conf["metadb"]["host"], self.conf["metadb"]["port"], self.conf["metadb"]["dbname"], self.conf["metadb"]["user"], self.conf["metadb"]["password"]))
        cur = conn.cursor()
        cur.execute("DELETE FROM collectiondb.ows_process WHERE identifier='%s'" % (self.get_process_identifier()))
        conn.commit()
        conn.close()
        service_folder = os.path.join(self.zooservices_folder, self.service_identifier)
        if os.path.isdir(service_folder):
            shutil.rmtree(service_folder)

        service_configuration_file = f"{service_folder}.zcfg"
        if os.path.exists(service_configuration_file):
            os.remove(service_configuration_file)



def UndeployProcess(conf, inputs, outputs):
    try:
        undeploy_process = UndeployService(conf, inputs, outputs)

        undeploy_process.remove_service()

        return zoo.SERVICE_UNDEPLOYED
    except Exception as err:
        conf["lenv"]["message"]=str(err)
        return zoo.SERVICE_FAILED
