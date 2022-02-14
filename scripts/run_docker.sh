docker run --rm -ti -p 80:80 \
            #-v /workspaces/proc-ades-dev/src/zoo-services/services/DeployProcess.py:/usr/lib/cgi-bin/DeployProcess.py \
            #-v /workspaces/proc-ades-dev/src/zoo-services/services/DeployProcess.zcfg:/usr/lib/cgi-bin/DeployProcess.zcfg \
            ades:latest