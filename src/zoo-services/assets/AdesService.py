from pprint import pprint
from workflow_executor import prepare, client, result, clean, helpers, execute
from time import sleep
import zoo
import sys


def prepare():
    print("Preparing namespace",file=sys.stderr)

def isPrepareFinished():
    print("Checking if namespace is ready",file=sys.stderr)
    finished=True
    success=True
    return finished,success

def getJobStatus():
    print("Get job status",file=sys.stderr)
    finished=True
    success=True
    return finished,success

def run():
    print("running job",file=sys.stderr)
    sleep(3)



def AdesService(conf,inputs,outputs):
    
    # Prepare process namespace"
    prepare()

    # Check if namespace is ready
    checkPollTime = 3
    maxAttempts=30
    attempts=0
    finished= False
    success= False
    while not finished:
        if attempts > maxAttempts:
            break
        finished,success = isPrepareFinished()
        sleep(checkPollTime)
        attempts+=1
    
    # Run job
    run()

    # Check if job has finished running
    maxAttempts=30
    attempts=0
    finished= False
    success= False
    while not finished:
        if attempts > maxAttempts:
            break
        sleep(checkPollTime)
        finished,success = getJobStatus()
        attempts+=1

    print(f"Job success: {success}",file=sys.stderr)

    outputs["Result"]["value"]="Hello "+inputs["a"]["value"]+" from Python World !"

    if success:
        return zoo.SERVICE_SUCCEEDED
    else:
        return zoo.SERVICE_FAILED
    