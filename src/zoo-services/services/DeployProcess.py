import os
from selectors import EpollSelector
import subprocess
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

from cookiecutter.main import cookiecutter
import sys
import shutil
import json
from pathlib import Path
import sys
from .deploy_util import Process
import yaml
import requests


class DeployService(object):
    def __init__(self, conf, inputs, outputs):

        self.conf = conf
        self.inputs = inputs
        self.outputs = outputs

        self.zooservices_folder = self.get_zoo_services_folder()

        self.application_package_url = self.get_application_package_url()

        self.cookiecutter_templates_folder = self._get_conf_value(
            key="templatesPath", section="cookiecutter"
        )
        self.cookiecutter_template_url = self._get_conf_value(
            key="templateUrl", section="cookiecutter"
        )

        self.tmp_folder = self._get_conf_value("tmpPath")
        # set via conf
        # self.deploy_template = self._get_conf_value("deployTemplate")

        self.process_id = self.conf["lenv"]["usid"]

        self.service_tmp_folder = self.create_service_tmp_folder()

        self.cwl_content = self.get_application_package()

        self.service_configuration = Process.create_from_cwl(self.cwl_content)

        self.service_configuration.service_provider = (
            f"{self.service_configuration.identifier}.service"
        )
        self.service_configuration.service_type = "Python"

    def get_zoo_services_folder(self):

        zooservices_folder = self._get_conf_value(
            key="CONTEXT_DOCUMENT_ROOT", section="renv"
        )

        # Checking if zoo can write in the servicePath
        self.check_write_permissions(zooservices_folder)

        return zooservices_folder

    def get_application_package_url(self):

        if "applicationPackage" not in self.inputs.keys():
            raise ValueError("The inputs dot not include applicationPackage")

        input_value = json.loads(self.inputs["applicationPackage"]["value"])

        if "href" in input_value.keys():
            return input_value["href"]
        else:
            return input_value

    def _get_conf_value(self, key, section="main"):

        if key in self.conf[section].keys():
            return self.conf[section][key]
        else:
            raise ValueError(f"{key} not set, check configuration")

    @staticmethod
    def check_write_permissions(folder):

        if not os.access(folder, os.W_OK):
            errorMsg = f"Cannot write to {folder}. Please check folder"
            print(errorMsg, file=sys.stderr)
            raise Exception(errorMsg)

    def create_service_tmp_folder(self):
        # creating the folder where we will download the applicationPackage
        tmp_path = os.path.join(self.tmp_folder, f"DeployProcess-{self.process_id}")
        os.makedirs(tmp_path)

        return tmp_path

    def get_application_package(self):

        cwl_content = None

        if self.application_package_url.startswith("http"):

            r = requests.get(self.application_package_url)

            cwl_content = yaml.safe_load(r.content)

        elif self.application_package_url.startswith("s3://"):

            raise ValueError("S3 not implemented")

        return cwl_content

    def generate_service(self):

        # checking if the template location is remote or local
        if self.cookiecutter_template_url.endswith(".git"):

            template_folder = os.path.join(
                self.cookiecutter_templates_folder,
                Path(self.cookiecutter_template_url).stem,
            )

            # checking if template had already been cloned
            if os.path.isdir(template_folder):

                shutil.rmtree(template_folder)

            os.system(f"git clone {self.cookiecutter_template_url} {template_folder}")

        else:
            raise ValueError(
                f"{self.cookiecutter_template_url} is not a valid git repo"
            )

        cookicutter_values = {}
        cookicutter_values["workflow_id"] = self.service_configuration.identifier
        cookicutter_values["conf"] = self.conf["cookiecutter"]

        # Create project from template
        path = cookiecutter(
            template_folder,
            extra_context=cookicutter_values,
            output_dir=self.service_tmp_folder,
            no_input=True,
            config_file="/tmp/cookiecutter_config.yaml",
            overwrite_if_exists=True,
        )

        zcfg_file = os.path.join(
            self.zooservices_folder, f"{self.service_configuration.identifier}.zcfg"
        )

        with open(zcfg_file, "w") as file:
            self.service_configuration.write_zcfg(file)

        app_package_file = os.path.join(
            path,
            f"{self.service_configuration.identifier}_{self.service_configuration.version}.cwl",
        )

        with open(app_package_file, "w") as file:
            yaml.dump(self.cwl_content, file)

        shutil.move(path, self.zooservices_folder)

        shutil.rmtree(self.service_tmp_folder)

        return True


# def create_service_tmp_folder(application_package_url, process_id, destination_folder):
#     # creating the folder where we will download the applicationPackage
#     tmp_folder_application_package = os.path.join(
#         destination_folder, f"DeployProcess-{process_id}"
#     )
#     os.makedirs(tmp_folder_application_package)
#     return tmp_folder_application_package


# def download_application_package(application_package_url, destination_folder):
#     # retrieving package name from filename
#     application_package_name = Path(application_package_url).stem

#     # downloading the application package
#     application_package_file = os.path.join(
#         destination_folder, f"{application_package_name}.cwl"
#     )
#     urllib.request.urlretrieve(application_package_url, application_package_file)
#     return application_package_file


# def refactor_with_service_name(
#     application_package_file, service_tmp_folder, service_name
# ):
#     # retrieving filname
#     application_package_name = Path(application_package_file).stem

#     # renaming application package name with service name
#     new_application_package_file = application_package_file.replace(
#         f"{application_package_name}.cwl", f"{service_name}/{service_name}.cwl"
#     )
#     os.rename(application_package_file, new_application_package_file)

#     return new_application_package_file


# def get_service_config_from_application_package(application_package_file):

#     with open(application_package_file, "r") as stream:
#         try:
#             cwl = yaml.safe_load(stream)

#         except yaml.YAMLError as e:
#             print("ERROR")

#     service_zcfg = Process.create_from_cwl(cwl)
#     return service_zcfg


# def write_service_config(service_zcfg, destination_folder):
#     # retrieving package name from filename
#     application_package_name = service_zcfg.identifier
#     zcfg_file = os.path.join(destination_folder, f"{application_package_name}.zcfg")
#     print(zcfg_file, file=sys.stderr)

#     with open(zcfg_file, "w") as f:
#         service_zcfg.write_zcfg(f)

#     return zcfg_file


# def check_write_permissions(zooservices_folder):
#     # Checking if zoo can write in the servicePath
#     if not os.access(zooservices_folder, os.W_OK):
#         errorMsg = f"Cannot write to {zooservices_folder}. Please check folder"
#         print(errorMsg, file=sys.stderr)
#         raise Exception(errorMsg)


# def generate_service_provider_from_template(
#     deploy_template, destination_folder, cookiecutter_templates_folder, inputs=dict()
# ):

#     # checking if the template location is remote or local
#     if deploy_template.endswith(".git"):
#         template_name = Path(deploy_template).stem
#         template_folder = os.path.join(cookiecutter_templates_folder, template_name)

#         # checking if template had already been cloned
#         if os.path.isdir(template_folder):
#             shutil.rmtree(template_folder)

#         os.system(f"git clone {deploy_template} {template_folder}")
#     else:
#         template_folder = deploy_template

#     # Create project from template
#     path = cookiecutter(
#         template_folder,
#         extra_context={"workflow_id": inputs["workflow_id"],},
#         output_dir=destination_folder,
#         no_input=True,
#         config_file="/tmp/cookiecutter_config.yaml",
#         overwrite_if_exists=True,
#     )
#     return path


def DeployProcess(conf, inputs, outputs):

    deploy_process = DeployService(conf, inputs, outputs)

    deploy_process.generate_service()

    outputs["deployResult"][
        "value"
    ] = f"Service {deploy_process.service_configuration.identifier} version {deploy_process.service_configuration.version} successfully deployed."

    return zoo.SERVICE_SUCCEEDED
