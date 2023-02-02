[main]
encoding = utf-8
version = 1.0.0
serverAddress = http://127.0.0.1
language = en-US
lang = fr-FR,en-CA,en-US
tmpPath=/tmp/
tmpUrl = http://localhost/temp/
dataPath = /usr/com/zoo-project
cacheDir = /tmp/
templatesPath = /var/www/

[identification]
title = ADES Development Server
abstract = Development version of ADES OGC API - Processes.
fees = None
accessConstraints = none
keywords = WPS,GIS,buffer

[provider]
providerName=ADES
providerSite=http://www.zoo-project.org
individualName=Gerald FENOY
positionName=Developer
role=Dev
addressDeliveryPoint=1280, avenue des Platanes
addressCity=Lattes
addressAdministrativeArea=False
addressPostalCode=34970
addressCountry=fr
addressElectronicMailAddress=gerald.fenoy@geolabs.fr
phoneVoice=False
phoneFacsimile=False


[env]
PYTHONPATH=/usr/miniconda3/envs/ades-dev/lib/python3.8/site-packages
CONTEXT_DOCUMENT_ROOT=/usr/lib/cgi-bin/

[database]
dbname=zoo
port=5432
user=zoo
password=zoo
host={{ .Release.Name }}-postgresql
type=PG
schema=public

[metadb]
dbname=zoo
port=5432
user=zoo
password=zoo
host={{ .Release.Name }}-postgresql
type=PG
schema=public

[security]
hosts=http://localhost
attributes=Accept-Language

[cookiecutter]
configurationFile=/tmp/cookiecutter_config.yaml
templatesPath=/tmp/cookiecutter-templates
templateUrl={{ .Values.cookiecutter.templateUrl }}


[servicesNamespace]
path= {{ .Values.persistence.servicesNamespacePath }}
deploy_service_provider=DeployProcess
undeploy_service_provider=UndeployProcess

[headers]
X-Powered-By=ZOO-Project

[rabbitmq]
host={{ .Release.Name }}-rabbitmq
port=5672
user=guest
passwd=guest
exchange=amq.direct
routingkey=zoo
queue=zoo_service_queue

[server]
async_worker=20
