#! /bin/sh

# prerequisites:
# - helm
# - kubectl
# - curl
# - mc
# - docker
# - jq
# - minikube

# optional for kind tests:
# - kind
# - nfs-common


runKindCluster() {
  echo "creating a cluster called 'ades-kind-cluster'"
  kind create cluster --name ades-kind-cluster

  echo "Set kubectl context to 'kind-ades-kind-cluster'"
  kubectl cluster-info --context kind-ades-kind-cluster

  echo "installing open-iscsi on kind control plane pod"
  docker exec ades-kind-cluster-control-plane apt-get update
  echo "Installing open-iscs1"
  docker exec ades-kind-cluster-control-plane apt-get install -y open-iscsi
  echo "running iscsid"
  docker exec ades-kind-cluster-control-plane iscsid

  echo "installing longhorn"
  helm repo add longhorn https://charts.longhorn.io
  helm repo update
  helm install longhorn longhorn/longhorn --namespace longhorn-system --create-namespace --version 1.4.1
  # takes 3 mins to install longhorn
  sleep 220
}


runLocalK8sCluster(){
  echo "connecting to existing kubernetes cluster"
  export KUBECONFIG=~/.kube_creodias_develop/config
}

runMinikubeCluster(){
  echo Starting minikube
  minikube start
  minikube docker-env
  eval $(minikube -p minikube docker-env)


}


oneTimeSetUp() {

  # MINIKUBE  
  runMinikubeCluster

  # LOCAL K8S
  # runLocalK8sCluster

  # KIND
  # this options does not work yet because kind does not support read write many volumes
  # it works until the deploy phase. Hopefully this will be fixed soon.
  # runKindCluster

  # check if ades-test namespace exists
  

  echo "creating namespace 'ades-test'"
  kubectl create ns ades-test
}

oneTimeTearDown() {
  
  # MINIKUBE
  echo Deleting minikube
  #minikube delete

  # KIND
  # echo "Delete kind cluster 'kind-ades-kind-cluster'"
  #kind delete cluster --name ades-kind-cluster

}

testDeployingAdesHelmChart() {

  #  MINIKUBE
  #helm install -f ./values.ades-minikube-test.yaml ades ../../charts/ades/ -n ades-test
  helm upgrade --install ades  ../../charts/ades/ -f ../../charts/ades/mycharts/values_minikube.yaml -n ades-test
  # LOCAL K8S

  # KIND
  #helm install -f ./values.ades-kind-test.yaml ades ../../charts/ades/ -n ades-test
  
  
  STATUS_STRING=$(helm status ades -n ades-test)
  assertContains "$STATUS_STRING" 'STATUS: deployed'
}

testAdesIsRunning() {
  sleep 15
  POD_NAME=$(kubectl get pods --namespace ades-test -l "app.kubernetes.io/name=ades,app.kubernetes.io/instance=ades" -o jsonpath="{.items[0].metadata.name}")
  echo "pod name is: $POD_NAME"
  n=0
  until [ "$n" -ge 50 ]; do
    STATUS="$(kubectl get pod $POD_NAME -n ades-test -o custom-columns=':status.phase' | tr '\n' ' ' | xargs)"
    if [ $STATUS = "Running" ]; then
      break
    fi
    echo "Pod is not running yet. Status: ${STATUS}"
    n=$((n + 1))
    sleep 20
  done

  assertEquals "Running" "$STATUS"
}

testPortforwardAdesOn8080() {
  export POD_NAME=$(kubectl get pods --namespace ades-test -l "app.kubernetes.io/name=ades,app.kubernetes.io/instance=ades" -o jsonpath="{.items[0].metadata.name}")
  kubectl --namespace ades-test port-forward $POD_NAME 8080:80 >/dev/null 2>&1 &

}

testAdesIsReady() {
  sleep 5
  POD_NAME=$(kubectl get pods --namespace ades-test -l "app.kubernetes.io/name=ades,app.kubernetes.io/instance=ades" -o jsonpath="{.items[0].metadata.name}")
  n=0
  until [ "$n" -ge 10 ]; do
    READY=$(kubectl get pod $POD_NAME -n ades-test -o jsonpath="{.status.containerStatuses[0].ready}")

    if [ "$READY" = "true" ]; then
      break
    fi
    echo "Pod is not ready yet "
    n=$((n + 1))
    sleep 20
  done

  assertEquals "$READY" "true"
}

testInstallMinio() {
  kubectl create ns minio
  kubectl create -f my-minio-fs.yaml -n minio
  kubectl expose deployment/my-minio-fs --type="NodePort" --port 9000 -n minio
  echo "waiting 10 seconds for minio to be ready"
  sleep 20
  echo "port-forwarding minio to port 9000"
  kubectl port-forward svc/my-minio-fs 9000:9000 -n minio >/dev/null 2>&1 &
}

testCreateBucket() {
  sleep 5
  echo "Creating mc alias for LOCAL_MINIO"
  mc alias set LOCAL_MINIO http://127.0.0.1:9000/ minio minio123
  echo "Creating bucket LOCAL_MINIO/processingresults"
  result=$(mc mb LOCAL_MINIO/processingresults)
  echo "Result: $result"
  assertEquals "Bucket created successfully \`LOCAL_MINIO/processingresults\`." "$result"
}

testDeployDnbrApp() {
  result=$(curl --location --request POST 'http://127.0.0.1:8080/eoepca/ogc-api/processes/' \
           --header 'Content-Type: application/cwl' \
           --data-binary "@apps/dNBR.cwl")
  expected_result=$(cat ./data_assertions/testDeployDnbrApp_assertion.txt)
  assertEquals "$expected_result" "$result"
}

testExecuteDnbrApp() {

  #              --header 'Prefer: respond-async;return=representation'
  sleep 5
  location=$(curl -D- --location --request  POST 'http://127.0.0.1:8080/eoepca/ogc-api/processes/dnbr' \
             --header 'Accept: application/json' \
             --header 'Content-Type: application/json' \
             --data-raw '{
                 "inputs":
                     {
                         "post_stac_item": "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_53HPA_20210723_0_L2A",
                         "pre_stac_item": "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_53HPA_20210703_0_L2A",
                         "aoi": "136.659,-35.96,136.923,-35.791",
                         "bands": ["B8A"]
                     },
                 "outputs": {
                     "stac": {
                         "format": {
                             "mediaType": "application/json"
                         },
                         "transmissionMode": "value"
                     }
                 },
                 "response": "document",
                 "mode": "async"
             }' | grep Location | cut -d' ' -f2 )
  echo "$location"
  assertNotNull "$location"
}


testMonitoringDnbrApp() {
  echo "Polling job status"

#  JOB_NAMESPACE=$(kubectl get ns  -l app=ades-app -o jsonpath="{.items[0].metadata.name}" )
#  echo "job namespace is: $JOB_NAMESPACE"
  jobid=$(basename "$location")
  JOB_NAMESPACE="dnbr-${jobid}"
  echo "job namespace: ${JOB_NAMESPACE}"

  sleep 60
  # TODO : check if job has been created

  JOB_NAME=$(kubectl get jobs --namespace $JOB_NAMESPACE -o jsonpath="{.items[0].metadata.name}" )
  echo "job name is: $JOB_NAME"

  # waiting for pods to be created
  SUB="No resources found in "
  n=0
  until [ "$n" -ge 30 ]; do
    POD_LIST=$(kubectl get pods --namespace $JOB_NAMESPACE -l job-name=$JOB_NAME )
    if [ "$POD_LIST" = *"$SUB"* ]; then
        echo "Pod has not been created yet "
        n=$((n + 1))
        sleep 20
    else
      echo "Pod has been created"
      break
    fi
  done

  POD_NAME=$(kubectl get pods --namespace $JOB_NAMESPACE -l job-name=$JOB_NAME -o jsonpath="{.items[0].metadata.name}")
  echo "pod name is: $POD_NAME"

  # checking if job pod is ready
  n=0
  until [ "$n" -ge 5 ]; do
    READY=$(kubectl get pod $POD_NAME -n $JOB_NAMESPACE -o jsonpath="{.status.containerStatuses[0].ready}")

    if [ "$READY" = "true" ]; then
        echo "Pod is ready"
      break
    fi
    echo "Pod is not ready yet "
    n=$((n + 1))
    sleep 20
  done

  # checking if  job pod is running
  n=0
  until [ "$n" -ge 10 ]; do
    STATUS="$(kubectl get pod $POD_NAME -n $JOB_NAMESPACE -o custom-columns=':status.phase' | tr '\n' ' ' | xargs)"
    if [ $STATUS = "Running" ]; then
        echo "Pod is running"
      break
    fi
    echo "Pod is not running yet. Status: ${STATUS}"
    n=$((n + 1))
    sleep 20
  done

  sleep 5
  # polling job status
  n=0
  until [ "$n" -ge 1000 ]; do
    echo "location is: $location"
    echo "http://127.0.0.1:8080$location"
    PROCESS_STATUS="$(curl  http://127.0.0.1:8080$location --header 'Accept: application/json' | jq --raw-output .status )"
    echo "Process status: ${PROCESS_STATUS}"

    POD_STATUS="$(kubectl get pod $POD_NAME -n $JOB_NAMESPACE -o custom-columns=':status.phase' | tr '\n' ' ' | xargs)"
    echo "Pod status: ${POD_STATUS}"

    if [ "$PROCESS_STATUS" != "running" ]; then
        echo "Job finished running. Process status: ${PROCESS_STATUS}  Pod status: ${POD_STATUS}"
      break
    fi
    echo "Pod is still running."
    n=$((n + 1))
    sleep 20
  done

assertEquals "Succeeded" "$PROCESS_STATUS"

}


testGetDnbrAppResults() {
  PROCESS_RESULT="$(curl "http://127.0.0.1:8080$location" \
    --header 'Accept: application/json' | jq )"
  echo " Process result: $PROCESS_RESULT"

  assertNotNull $PROCESS_RESULT
}


# Load shUnit2.
. $()./shunit2
