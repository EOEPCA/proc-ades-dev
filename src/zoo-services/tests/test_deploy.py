
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

from services.deploy_util import Process
from services.DeployProcess import DeployService
import shutil
import unittest

class Tests(unittest.TestCase):
    
    def test_empty_conf(self):
        
        conf = {}
        inputs = {}
        outputs = {}
        try:
            deploy_process = DeployService(conf, inputs, outputs)
        except:
            self.assertRaises(ValueError)

    def test_no_write_zoo_services_folder(self):

        conf["renv"] = {}
        conf["renv"]["CONTEXT_DOCUMENT_ROOT"] = "/usr/lib/cgi-bin/"
        inputs = {}
        inputs['applicationPackage'] = "https://raw.githubusercontent.com/EOEPCA/proc-ades/develop/test/sample_apps/dNBR/dNBR.cwl#dnbr"
        
        outputs = {}

        try:
            deploy_process = DeployService(conf, inputs, outputs)
        except:
            self.assertRaises(Exception)

    def test_init(self):

        conf["renv"] = {}
        conf["renv"]["CONTEXT_DOCUMENT_ROOT"] = "/tmp"
        conf["cookiecutter"] = {"templatesPath": "", "templateUrl": ""}
        conf["main"] = {"tmpPath": "/tmp"}
        conf["lenv"] = {"usid": "process_id_value"}
        inputs = {}
        inputs['applicationPackage'] = {"value": '{"href": "https://raw.githubusercontent.com/EOEPCA/proc-ades/develop/test/sample_apps/dNBR/dNBR.cwl#dnbr"}'}
        
        outputs = {}

        deploy_process = DeployService(conf, inputs, outputs)

        shutil.rmtree("/tmp/DeployProcess-process_id_value")

        self.assertTrue(isinstance(deploy_process, DeployService))

    def test_get_http_cwl(self):

        conf["renv"] = {}
        conf["renv"]["CONTEXT_DOCUMENT_ROOT"] = "/tmp"
        conf["cookiecutter"] = {"templatesPath": "", "templateUrl": ""}
        conf["main"] = {"tmpPath": "/tmp"}
        conf["lenv"] = {"usid": "process_id_value"}
        inputs = {}
        inputs['applicationPackage'] = {"value": '{"href": "https://raw.githubusercontent.com/EOEPCA/proc-ades/develop/test/sample_apps/dNBR/dNBR.cwl#dnbr"}'}
        
        outputs = {}

        deploy_process = DeployService(conf, inputs, outputs)

        shutil.rmtree("/tmp/DeployProcess-process_id_value")

        cwl_content = deploy_process.cwl_content

        self.assertTrue(isinstance(cwl_content, dict))


    def test_cwl_identifier(self):

        conf["renv"] = {}
        conf["renv"]["CONTEXT_DOCUMENT_ROOT"] = "/tmp"
        conf["cookiecutter"] = {"templatesPath": "", "templateUrl": ""}
        conf["main"] = {"tmpPath": "/tmp"}
        conf["lenv"] = {"usid": "process_id_value"}
        inputs = {}
        inputs['applicationPackage'] = {"value": '{"href": "https://raw.githubusercontent.com/EOEPCA/proc-ades/develop/test/sample_apps/dNBR/dNBR.cwl#dnbr"}'}
        
        outputs = {}

        deploy_process = DeployService(conf, inputs, outputs)

        shutil.rmtree("/tmp/DeployProcess-process_id_value")

        self.assertEqual("dnbr", deploy_process.service_configuration.identifier)

    def test_generate_service(self):
        
        conf["renv"] = {}
        conf["renv"]["CONTEXT_DOCUMENT_ROOT"] = "/tmp"
        conf["cookiecutter"] = {"templatesPath": "", "templateUrl": "https://github.com/EOEPCA/proc-service-template.git"}
        conf["main"] = {"tmpPath": "/tmp"}
        conf["lenv"] = {"usid": "process_id_value"}
        inputs = {}
        inputs['applicationPackage'] = {"value": '{"href": "https://raw.githubusercontent.com/EOEPCA/proc-ades/develop/test/sample_apps/dNBR/dNBR.cwl#dnbr"}'}
        
        outputs = {}
        
        deploy_process = DeployService(conf, inputs, outputs)
        print(deploy_process.service_tmp_folder)
        print(deploy_process.tmp_folder)

        deploy_process.generate_service()
        
        shutil.rmtree("/tmp/DeployProcess-process_id_value")