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


import os
from genericpath import exists
import sys
from pathlib import Path
services_dir = os.path.join(Path(os.path.abspath(os.path.dirname(__file__))).parent,"services")
sys.path.insert(0, services_dir)
from DeployProcess import DeployService, DeployProcess
import shutil
import unittest
import shutil, tempfile
import random, string


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a temporary directory
        cls.tmp_dir = tempfile.mkdtemp()

        # create cookiecutter templates folder
        cls.cookiecutter_templates_folder = os.path.join(
            cls.tmp_dir, "cookiecutter_templates"
        )
        os.makedirs(cls.cookiecutter_templates_folder)

        # create cookiecutter config file
        cls.cookiecutter_config_file = os.path.join(
            cls.tmp_dir, "cookiecutter_config.yaml"
        )

        # create cookiecutter config file
        cookiecutter_config_file = open(cls.cookiecutter_config_file, "w")
        cookiecutter_config_file.write(
            f'replay_dir: "{cls.cookiecutter_templates_folder}"'
        )
        cookiecutter_config_file.write(
            f'cookiecutters_dir: "{cls.cookiecutter_templates_folder}"'
        )
        cookiecutter_config_file.close()

        # create zoo services folder
        cls.zoo_services_folder = os.path.join(cls.tmp_dir, "cgi-bin")
        os.makedirs(cls.zoo_services_folder)

    @classmethod
    def tearDownClass(self):
        # Remove the directory after the test
        shutil.rmtree(self.tmp_dir)

    def setUp(self):
        self.conf = {}
        self.conf["renv"] = {}
        self.conf["renv"]["CONTEXT_DOCUMENT_ROOT"] = self.tmp_dir
        self.conf["cookiecutter"] = {
            "templatesPath": self.cookiecutter_templates_folder,
            "templateUrl": "https://github.com/EOEPCA/proc-service-template.git",
            "configurationFile": self.cookiecutter_config_file,
        }
        self.conf["main"] = {"tmpPath": self.tmp_dir}
        self.conf["lenv"] = {
            "usid": "".join(random.choice(string.digits) for i in range(10))
        }

        # load application package from file
        cwl_file = open("dnbr.cwl", "r")
        cwl_data = cwl_file.read()
        cwl_file.close()

        self.inputs = {}
        self.inputs["applicationPackage"] = {"value": cwl_data}

        self.outputs = {}
        self.outputs["deployResult"] = {}

    def tearDown(self):
        process_tmp = os.path.join(self.tmp_dir, "DeployProcess-process_id_value")
        deployed_service = os.path.join(
            self.conf["renv"]["CONTEXT_DOCUMENT_ROOT"], "dnbr"
        )
        if exists(process_tmp):
            shutil.rmtree(process_tmp)
        if exists(deployed_service):
            shutil.rmtree(deployed_service)

    def test_empty_conf(self):

        conf = {}
        inputs = {}
        outputs = {}
        try:
            deploy_process = DeployService(conf, inputs, outputs)
        except:
            self.assertRaises(ValueError)

    def test_no_write_zoo_services_folder(self):
        conf = {}
        conf["renv"] = {}
        conf["renv"]["CONTEXT_DOCUMENT_ROOT"] = "/usr/lib/cgi-bin/"
        inputs = {}
        inputs[
            "applicationPackage"
        ] = "https://raw.githubusercontent.com/EOEPCA/proc-ades/develop/test/sample_apps/dNBR/dNBR.cwl#dnbr"

        outputs = {}

        try:
            deploy_process = DeployService(conf, inputs, outputs)
        except:
            self.assertRaises(Exception)

    def test_init(self):
        deploy_process = DeployService(self.conf, self.inputs, self.outputs)
        self.assertTrue(isinstance(deploy_process, DeployService))

    def test_get_http_cwl(self):

        deploy_process = DeployService(self.conf, self.inputs, self.outputs)
        cwl_content = deploy_process.cwl_content
        self.assertTrue(isinstance(cwl_content, dict))

    def test_cwl_identifier(self):
        deploy_process = DeployService(self.conf, self.inputs, self.outputs)
        self.assertEqual("dnbr", deploy_process.service_configuration.identifier)

    def test_generate_service(self):

        deploy_process = DeployService(self.conf, self.inputs, self.outputs)
        deploy_process.generate_service()
        self.assertTrue(
            os.path.isdir(
                os.path.join(
                    self.conf["renv"]["CONTEXT_DOCUMENT_ROOT"],
                    deploy_process.service_configuration.identifier,
                )
            )
        )
        self.assertTrue(
            os.path.exists(
                os.path.join(
                    self.conf["renv"]["CONTEXT_DOCUMENT_ROOT"],
                    deploy_process.service_configuration.identifier + ".zcfg",
                )
            )
        )

    def test_deploy_service(self):

        r = DeployProcess(self.conf, self.inputs, self.outputs)
        self.assertEqual(
            os.path.isdir(
                os.path.join(self.conf["renv"]["CONTEXT_DOCUMENT_ROOT"], "dnbr")
            ),
            True,
        )
        self.assertEqual(
            os.path.exists(
                os.path.join(self.conf["renv"]["CONTEXT_DOCUMENT_ROOT"], "dnbr.zcfg")
            ),
            True,
        )
        self.assertEqual(r, zoo.SERVICE_SUCCEEDED)


if __name__ == '__main__':
    unittest.main()