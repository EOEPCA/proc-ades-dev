import sys
import json
import yaml
import re


class Process:
    def __init__(
        self,
        identifier,
        version,
        title=None,
        description=None,
        store_supported=True,
        status_supported=True,
        service_type=None,
        service_provider=None,
    ):
        self.identifier = identifier
        self.version = version
        self.title = title or identifier
        if self.title:
            self.title = str(self.title)
        self.description = description or title
        if self.description:
            self.description = str(self.description)
        self.store_supported = store_supported
        self.status_supported = status_supported
        self.service_type = service_type
        self.service_provider = service_provider
        self.version = version
        self.inputs = []
        self.outputs = []

    @classmethod
    def create_from_cwl(cls, cwl, workflow_id=None):
        """
        Creates a Process object from a dictionary representing the CWL YAML file.
        """

        if "$graph" not in cwl:
            raise Exception("'$graph' key not found in CWL")

        # Find namespace
        software_namespace_prefix = None
        if "$namespaces" in cwl and isinstance(cwl["$namespaces"], dict):
            for (prefix, uri) in cwl["$namespaces"].items():
                if uri in [
                    "https://schema.org/SoftwareApplication",
                    "https://schema.org/",
                ]:
                    software_namespace_prefix = prefix

        workflows = [
            item
            for item in cwl["$graph"]
            if "class" in item and item["class"] == "Workflow"
        ]
        if len(workflows) == 0:
            raise Exception("No workflow found")
        if workflow_id is None:
            workflow = workflows[0]
        else:
            workflow = next(
                (wf for wf in workflows if "id" in wf and wf["id"] == workflow_id), None
            )
            if workflow is None:
                raise Exception("Workflow '{0}' not found".format(workflow_id))

        if "id" not in workflow:
            raise Exception("Workflow has no identifier")

        version = None
        for key in ["softwareVersion", "version"]:
            key = "{0}:{1}".format(software_namespace_prefix, key)
            if key in workflow:
                version = str(workflow[key])
                break
        if not version:
            for key in ["softwareVersion", "version"]:
                key = "{0}:{1}".format(software_namespace_prefix, key)
                if key in cwl:
                    version = str(cwl[key])
                    break

        if not version:
            raise Exception("Workflow '{0}' has no version".format(workflow["id"]))

        if "inputs" not in workflow:
            raise Exception("Workflow '{0}' has no inputs".format(workflow["id"]))

        process = Process(
            identifier=workflow["id"],
            version=version,
            title=workflow["label"] if "label" in workflow else None,
            description=workflow["doc"] if "doc" in workflow else None,
        )

        process.add_inputs_from_cwl(workflow["inputs"])
        process.add_outputs_from_cwl(workflow["outputs"])

        return process

    def add_inputs_from_cwl(self, inputs):
        """
        Adds a process input from a CWL input representation.
        """

        for input_id, input in inputs.items():
            process_input = ProcessInput.create_from_cwl(str(input_id), input)
            self.inputs.append(process_input)

    def add_outputs_from_cwl(self, outputs):
        """
        Adds a process output from a CWL input representation.
        """
        print(str(outputs),file=sys.stderr)
        for output_id, output in outputs.items():
            print(f"output_id: {output_id}\n output: {output}",file=sys.stderr)
            process_output = ProcessOutput.create_from_cwl(str(output_id), output)
            self.outputs.append(process_output)

    def write_zcfg(self, stream):
        """
        Writes the configuration file for the Zoo process (.zfcg) to a stream.
        """

        print("[{0}]".format(self.identifier), file=stream)
        if self.title:
            print("  Title = {0}".format(self.title), file=stream)
        if self.description:
            print("  Abstract = {0}".format(self.description), file=stream)
        if self.service_provider:
            print("  serviceType = {0}".format(self.service_type), file=stream)
            print("  serviceProvider = {0}".format(self.service_provider), file=stream)
        if self.version:
            print("  processVersion = {0}".format(self.version), file=stream)
        print(
            "  storeSupported = {0}".format(
                "true" if self.store_supported else "false"
            ),
            file=stream,
        )
        print(
            "  statusSupported = {0}".format(
                "true" if self.status_supported else "false"
            ),
            file=stream,
        )

        print("  <DataInputs>", file=stream)
        for input in self.inputs:
            print("    [{0}]".format(input.identifier), file=stream)
            print("      Title = {0}".format(input.title), file=stream)
            print("      Abstract = {0}".format(input.description), file=stream)
            print("      minOccurs = {0}".format(input.min_occurs), file=stream)
            print(
                "      maxOccurs = {0}".format(
                    999 if input.max_occurs == 0 else input.max_occurs
                ),
                file=stream,
            )
            if input.is_complex:
                pass
            else:
                print("      <LiteralData>", file=stream)
                print("        dataType = {0}".format(input.type), file=stream)
                if input.possible_values:
                    print(
                        "        AllowedValues = {0}".format(
                            ",".join(input.possible_values)
                        ),
                        file=stream,
                    )
                if input.default_value:
                    print("        <Default>", file=stream)
                    print(
                        "          value = {0}".format(input.default_value), file=stream
                    )
                    print("        </Default>", file=stream)
                else:
                    print("        <Default/>", file=stream)
                print("      </LiteralData>", file=stream)
        print("  </DataInputs>", file=stream)

        print("  <DataOutputs>", file=stream)
        for output in self.outputs:
            print("    [{0}]".format(output.identifier), file=stream)
            print("      Title = {0}".format(output.title), file=stream)
            print("      Abstract = {0}".format(output.description), file=stream)
            if output.is_complex:
                print("      <ComplexData>", file=stream)
                print("        <Default>", file=stream)
                print(
                    "          mimeType = {0}".format(
                        output.file_content_type
                        if output.file_content_type
                        else "text/plain"
                    ),
                    file=stream,
                )
                print("        </Default>", file=stream)
                print("      </ComplexData>", file=stream)
            else:
                print("      <LiteralData>", file=stream)
                print("        dataType = {0}".format(input.type), file=stream)
                print("        <Default/>", file=stream)
                print("      </LiteralData>", file=stream)
        print("  </DataOutputs>", file=stream)

    def write_ogc_api_json(self, stream):
        ogc = self.get_ogc_api_json()
        print(json.dumps(ogc, indent=2), file=stream)

    def write_ogc_api_yaml(self, stream):
        ogc = self.get_ogc_api_json()
        print(yaml.dump(ogc), file=stream)

    def get_ogc_api_json(self):
        ogc = {
            "id": self.identifier,
            "version": self.version,
            "title": self.title,
            "description": self.description,
            "jobControlOptions": [],
            "outputTransmission": [],
            "links": [],
            "inputs": {},
            "outputs": {},
        }

        for input in self.inputs:
            ogc_input_schema = {"type": input.type}
            if input.min_occurs == 0:
                ogc_input_schema["nullable"] = True
            elif input.max_occurs != 1:
                ogc_input_schema["minItems"] = input.min_occurs
            if input.max_occurs != 1:
                ogc_input_schema["type"] = "array"
                ogc_input_schema["maxItems"] = (
                    input.max_occurs if input.max_occurs > 1 else 100
                )
                ogc_input_schema["items"] = {"type": input.type}
            if input.possible_values:
                ogc_input_schema["enum"] = input.possible_values.copy()
            if input.default_value:
                ogc_input_schema["default"] = input.default_value
            if input.is_file:
                ogc_input_schema["contentMediaType"] = input.file_content_type()
            elif input.is_directory:
                ogc_input_schema["contentMediaType"] = input.file_content_type()

            ogc_input = {
                "title": input.title,
                "description": input.description,
                "schema": ogc_input_schema,
            }

            if input.is_complex:
                pass  # TODO
            else:
                ogc["inputs"][input.identifier] = ogc_input

        for output in self.outputs:
            ogc_output_schema = {"type": output.type}

            ogc_output = {
                "title": output.title,
                "description": output.description,
                "schema": ogc_output_schema,
            }

            if output.is_complex:
                pass  # TODO
            else:
                ogc["outputs"][output.identifier] = ogc_output
        return ogc


class ProcessInput:

    cwl_type_map = {
        "boolean": "boolean",
        "int": "integer",
        "long": "integer",
        "float": "number",
        "double": "number",
        "string": "string",
        "enum": None,
    }

    cwl_input_type_regex = re.compile(
        r"^(?P<name>[A-Za-z_][A-Za-z0-9_]+?)(?P<array>\[\])?(?P<optional>\?)?$"
    )

    def __init__(self, identifier, title=None, description=None, input_type="string"):
        self.identifier = str(identifier)
        self.title = title or identifier
        if self.title:
            self.title = str(self.title)
        self.description = description or title
        if self.description:
            self.description = str(self.description)
        self.type = input_type
        self.min_occurs = 1
        self.max_occurs = 1
        self.default_value = None
        self.possible_values = None
        self.is_complex = False  # TODO
        self.is_file = False
        self.file_content_type = None
        self.is_directory = False

    @classmethod
    def create_from_cwl(cls, input_id, cwl_input):

        cwl_input_type = cwl_input["type"] if "type" in cwl_input else "string"

        process_input = cls(
            input_id,
            cwl_input["label"] if "label" in cwl_input else None,
            cwl_input["doc"] if "doc" in cwl_input else None,
        )

        process_input.set_type_from_cwl(input_id, cwl_input_type)

        if "default" in cwl_input:
            process_input.default_value = cwl_input["default"]

        return process_input

    def set_type_from_cwl(self, input_id, cwl_input_type):
        if isinstance(cwl_input_type, str):
            type_match = self.__class__.cwl_input_type_regex.match(cwl_input_type)

            if not type_match:
                raise Exception(
                    "Incorrect type for input '{0}': '{1}'".format(
                        input_id, cwl_input_type
                    )
                )

            type_name = type_match.group("name")
            if type_name in self.__class__.cwl_type_map:
                type_name = self.__class__.cwl_type_map[type_name]
            elif type_name == "File":
                type_name = "string"
                self.file_content_type = "text/plain"
            elif type_name == "Directory":
                type_name = "string"
                self.file_content_type = "text/plain"
            else:
                raise Exception(
                    "Unsupported type for input '{0}': {1}".format(input_id, type_name)
                )

            self.type = type_name
            self.min_occurs = 0 if type_match.group("optional") else 1
            self.max_occurs = (
                0 if type_match.group("array") else 1
            )  # 0 means unbounded, TODO: what should be the maxOcccurs value if unbounded is not available?

        elif isinstance(cwl_input_type, dict):
            if "type" not in cwl_input_type:
                raise Exception(
                    "Type missing for input '{0}': '{1}'".format(
                        input_id, cwl_input_type
                    )
                )

            type_match = self.__class__.cwl_input_type_regex.match(
                cwl_input_type["type"]
            )

            if not type_match:
                raise Exception(
                    "Incorrect type for input '{0}': '{1}'".format(
                        input_id, cwl_input_type
                    )
                )

            type_name = type_match.group("name")
            if type_name == "enum":
                type_name = "string"
                if "symbols" not in cwl_input_type:
                    raise Exception(
                        "Missing symbols (possible values) for enum input '{0}'".format(
                            input_id
                        )
                    )
                elif not isinstance(cwl_input_type["symbols"], list):
                    raise Exception(
                        "Symbols (possible values) are not a list for enum input for '{0}'".format(
                            input_id
                        )
                    )
                self.possible_values = [str(s) for s in cwl_input_type["symbols"]]
            elif type_name == "array":
                if "items" not in cwl_input_type:
                    raise Exception(
                        "Missing item type for array input '{0}'".format(input_id)
                    )
                type_name = cwl_input_type["items"]
                if type_name in self.__class__.cwl_type_map:
                    type_name = self.__class__.cwl_type_map[type_name]
                else:
                    type_name = None
                self.min_occurs = 1
                self.max_occurs = 0
            else:
                type_name = None

            if not type_name:
                raise Exception("Unsupported type: '{0}'".format(type_name))

            self.type = type_name


class ProcessOutput:
    def __init__(self, identifier, title=None, description=None, input_type="string"):
        self.identifier = str(identifier)
        self.title = title or identifier
        if self.title:
            self.title = str(self.title)
        self.description = description or title
        if self.description:
            self.description = str(self.description)
        self.type = input_type
        self.min_occurs = 1
        self.max_occurs = 1
        self.default_value = None
        self.possible_values = None
        self.is_complex = False
        self.is_file = False
        self.file_content_type = None
        self.is_directory = False

    @classmethod
    def create_from_cwl(cls, output_id, cwl_output):
        cwl_output_type = cwl_output["type"] if "type" in cwl_output else "string"

        process_output = cls(
            output_id,
            cwl_output["label"] if "label" in cwl_output else None,
            cwl_output["doc"] if "doc" in cwl_output else None,
        )

        process_output.set_type_from_cwl(output_id, cwl_output_type)

        return process_output

    def set_type_from_cwl(self, output_id, cwl_output_type):
        if isinstance(cwl_output_type, str):
            type_name = cwl_output_type
            if type_name == "string":
                pass
            elif type_name == "File":
                type_name = "string"
                self.file_content_type = "text/plain"
            elif type_name == "Directory":
                self.is_complex = True
                self.file_content_type = "application/json"
            else:
                raise Exception(
                    "Unsupported type for output '{0}': {1}".format(
                        output_id, type_name
                    )
                )

            self.type = type_name
