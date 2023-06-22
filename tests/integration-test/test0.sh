# prerequisites:
# - helm
# - kubectl
# - curl
# - mc
# - docker
# - jq
# - minikube



oneTimeSetUp() {

  # MINIKUBE
  echo Starting minikube
  minikube start

  echo "creating namespace 'ades-test'"
  kubectl create ns ades-test
}

oneTimeTearDown() {

  # MINIKUBE
  echo Deleting minikube
  minikube delete
}

testDeployingAdesHelmChart() {

  #  MINIKUBE
  helm upgrade --install ades  ../../charts/ades/ -f ../../charts/ades/mycharts/values_minikube.yaml -n ades-test


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
  POD_NAME=$(kubectl get pods --namespace ades-test -l "app.kubernetes.io/name=ades,app.kubernetes.io/instance=ades" -o jsonpath="{.items[0].metadata.name}")
  kubectl --namespace ades-test port-forward $POD_NAME 8080:80 > /dev/null 2>&1 &

}
#
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
  echo "waiting 20 seconds for minio to be ready"
  sleep 20
  echo "port-forwarding minio to port 9000"
  kubectl port-forward svc/my-minio-fs 9000:9000 -n minio > /dev/null 2>&1 &
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
  sleep 10
  jobid="$(curl --request  POST 'http://127.0.0.1:8080/eoepca/ogc-api/processes/dnbr' \
             --header 'Accept: application/json' \
             --header 'Content-Type: application/json' \
             --data-raw '{
                 "inputs":
                     {
                         "post_stac_item": "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_53HPA_20210723_0_L2A",
                         "pre_stac_item": "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_53HPA_20210703_0_L2A",
                         "aoi": "136.659,-35.96,136.923,-35.791",
                         "bands": ["B8A", "B12", "SCL"]
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
             }' | jq --raw-output .jobID  )"
  echo "$jobid"
  location="http://localhost:8080/eoepca/ogc-api/jobs/${jobid}"

  assertNotNull "$jobid"
}


testStartingDnbrAppJob() {
  echo "Polling job status"

# TODO update pycalrissian to add labels to job namespaces
#  JOB_NAMESPACE=$(kubectl get ns  -l app=ades-app -o jsonpath="{.items[0].metadata.name}" )
#  echo "job namespace is: $JOB_NAMESPACE"
  JOB_NAMESPACE="dnbr-${jobid}"
  echo "job namespace: ${JOB_NAMESPACE}"
  SUB="No resources found in "

  n=0
  until [ "$n" -ge 30 ]; do
    JOB_LIST="$( kubectl get jobs --namespace $JOB_NAMESPACE )"
    if [ -z "$JOB_LIST" ] ||  [[ "$JOB_LIST" == *"$SUB"* ]]; then
        echo "Job has not been created yet "
        n=$((n + 1))
        sleep 20
    else
      echo "Job has been created"
      break
    fi
  done

  JOB_NAME="$(kubectl get jobs --namespace $JOB_NAMESPACE -o jsonpath='{.items[0].metadata.name}' )"
  echo "job name is: ${JOB_NAME}"

  # waiting for pods to be created
  n=0
  until [ "$n" -ge 30 ]; do
    POD_LIST="$( kubectl get pods --namespace $JOB_NAMESPACE 2>&1 )"
    if [ -z "$POD_LIST" ] || [[ "$POD_LIST" == *"$SUB"* ]]; then
        echo "Pod has not been created yet "
        n=$((n + 1))
        sleep 20
    else
      echo "Pod has been created"
      break
    fi
  done

  POD_NAME=$( kubectl get pods --namespace $JOB_NAMESPACE -o jsonpath="{.items[0].metadata.name}" )
  echo "pod name is: $POD_NAME"
  # checking if job pod is ready
  n=0
  until [ "$n" -ge 5 ]; do
    READY=$( kubectl get pod $POD_NAME -n $JOB_NAMESPACE -o jsonpath="{.status.containerStatuses[0].ready}" )

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
    if [[ "$STATUS" == "Running" ]]; then
        echo "Pod is running"
      break
    fi
    echo "Pod is not running yet. Status: ${STATUS}"
    n=$((n + 1))
    sleep 20
  done

  sleep 5
}

testMonitoringDnbrApp(){
    # polling job status
    n=0
    until [ "$n" -ge 1000 ]; do
      echo "location is: $location"
      PROCESS_STATUS="$(curl $location --header 'Accept: application/json' | jq --raw-output .status )"
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

  assertEquals "successful" "$PROCESS_STATUS"
}


testGetDnbrAppResults() {
  sleep 10
  PROCESS_RESULT="$(curl "${location}/results" \
    --header 'Accept: application/json' | jq )"
  echo " Process result: $PROCESS_RESULT"

  assertNotNull "$PROCESS_RESULT"
}


# Load shUnit2.
. $()./shunit2
