<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/EOEPCA/proc-ades">
    <img src="https://raw.githubusercontent.com/EOEPCA/proc-ades/master/images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">ADES building block</h3>

  <p align="center">
    Application Deployment and Execution Service (ADES) building block
    <br />
    <a href="https://github.com/EOEPCA/proc-ades/wiki"><strong>Get Started »</strong></a>
    <br />
    <a href="https://eoepca.github.io/proc-ades/master/">Open Design</a>
    .
    <a href="https://github.com/EOEPCA/proc-ades/issues">Report Bug</a>
    ·
    <a href="https://github.com/EOEPCA/proc-ades/issues">Request Feature</a>
  </p>
</p>

<!-- TABLE OF CONTENTS -->
## Table of Contents

- [Table of Contents](#table-of-contents)
- [About The Project](#about-the-project)
- [Getting Started & Usage](#getting-started--usage)

<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot](https://raw.githubusercontent.com/EOEPCA/proc-ades/master/images/screenshot.png)](https://github.com/EOEPCA/)

The Processing & Chaining domain area provides an extensible repository of processing functions, tools and applications that can be discovered by search query, invoked individually, and utilised in workflows. ADES is responsible for the execution of the processing service through both a [OGC WPS 1.0 & 2.0 OWS service](https://www.ogc.org/standards/wps) and an [OGC Processes REST API](https://github.com/opengeospatial/wps-rest-binding). The processing request are executed within the target Exploitation Platform (i.e., the one that is close to the data).

The ADES software uses [ZOO-Project](http://zoo-project.org/) as the main framework for exposing the OGC compliant web services. The [ZOO-kernel](http://zoo-project.org/docs/kernel/) powering the web services is included in the software package.

The ADES functions are designed to perform the processing and chaining function on a [Kubernetes](https://kubernetes.io) cluster using the [Calrissian Tool](https://github.com/Duke-GCB/calrissian). Calrissian uses CWL, that is a robust workflow engine, over Kubernetes that enables the implementation of each step in a workflow as a container. It provides simple, flexible mechanisms for specifying constraints between the steps in a workflow and artifact management for linking the output of any step as an input to subsequent steps.

<!-- GETTING STARTED -->
## Getting Started & Usage

The various containers making up the ADES architecture are built and launched using the following commands (this will take a while when done for the first time):

```bash
# Clone the project and open the folder
git clone https://github.com/EOEPCA/proc-ades-dev.git
cd proc-ades-dev

# Build and launch the multi-container Docker application for ADES
docker-compose up
```

### Run the ADES Container

The various containers making up the ADES architecture are launched using the following command (which may take a while when run for the first time):


### List Processes

To see a list of deployed processes, you can query them the OGC API `/processes` endpoint:

```bash
curl --location --request GET 'http://localhost/ogc-api/processes' \
--header 'Accept: application/json'
```

As it is a simple GET request, you can see the same content using a web browser too:

http://localhost/ogc-api/processes/


### Deploy Process

To deploy a new process, send an execution request to the DeployProcess OGC API endpoint:

```bash
curl --location --request POST 'http://localhost/ogc-api/processes/DeployProcess' \
--header 'Content-Type: application/json' \
--data-raw '{
    "inputs": {
        "applicationPackage": {
            "mimeType": "application/cwl",
            "value": {
                "href": "https://raw.githubusercontent.com/EOEPCA/proc-ades/develop/test/sample_apps/dNBR/dNBR.cwl#dnbr"
            }
        }
    },
    "outputs": {
        "Result": {
            "format": {
                "mediaType": "application/json"
            },
            "transmissionMode": "reference"
        }
    }
}'
```
The ouput should look like this:

```bash
{
    "message": "Service dnbr version 0.1.0 successfully deployed.",
    "service": "dnbr",
    "status": "success"
}
```


### Undeploy Process

To undeploy an existing process, send an execution request to the UndeployProcess OGC API endpoint:

```bash
curl --location --request POST 'http://localhost/ogc-api/processes/UndeployProcess' \
--header 'Content-Type: application/json' \
--data-raw '{
    "inputs": {
        "applicationPackageIdentifier": "dnbr" 
    },
    "outputs": {
        "undeployResult": {
            "format": {
                "mediaType": "application/json"
            },
            "transmissionMode": "reference"
        }
    }
}'
```

The ouput should look like this:

```bash
{
    "message": "Service dnbr successfully undeployed.",
    "service": "dnbr",
    "status": "success"
}
```

<!-- DEVELOPER NOTES -->
## Developer Notes

This section contains some short information on how to use this repository for further development.


### Develop Within Container

It is a good practice for development to use a container that provides already all required dependencies and tools. In order to do so with Visual Studio Code, follow [these instructions](https://github.com/EOEPCA/proc-ades-dev/blob/develop/.devcontainer/README.MD).


### Run Unit Tests

The following sections assume that the Docker container is used (see previous section).

Unit tests are defined in [this folder](src/zoo-services/tests/). They can be run with the following commands:

```bash
# Change into the local copy of the folder containing the tests:
cd src/zoo-services/tests/

# Launch the tests
sh run_tests.sh
```

The test produces an output similar to this:

```txt
----------------------------------------------------------------------
Ran 7 tests in 4.656s

OK
Name                                                                   Stmts   Miss  Cover   Missing
----------------------------------------------------------------------------------------------------
/workspaces/proc-ades-dev/src/zoo-services/services/DeployProcess.py     118     18    85%   14, 17, 41, 103, 110, 117, 144-167, 189, 215-216
----------------------------------------------------------------------------------------------------
TOTAL                                                                    118     18    85%
```


### Tests in GitHub Actions

The file GitHub workflow file [docker-image.yml](.github/workflows/docker-image.yml) defines a series of actions for testing purposes that are performed server-side at every `git push` operation.

