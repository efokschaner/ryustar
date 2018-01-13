# Load Test for RyuStar

## Notes on cluster size

Based on some very scientific reading of blog posts, I predict we may be able to get on the order of 1000 locust users per core.
Based on the inital actual load test run, we were able to get 2000 users simulated on a n1-standard-1 machine. We may have been coming close to the limit but I'm not sure as I didn't control too carefully.
Each locust worker is single threaded so distribute them 1 per core.

### Spotting overloaded load generator
We need to be careful that the load generator itself does not become overloaded which can produce inaccurate load test results.
To avoid this we should:
 - Monitor CPU and Memory usage on load generator machines to avoid capping out (80% rule of thumb?)
 - Run a non load generating client as a control (could even be from dev machine) to monitor the request latency metrics,
   and ensure the non-load generating machine isn't seeing request metrics that are drastically different to the swarm.

## Local run

    locust -f docker-image/locust-tasks/tasks.py --host=https://www.ryustar.io

## Minikiube run

    ./deploy_minikube
    # Then in a separate shell
    kubectl --context=minikube port-forward $(kubectl --context=minikube get pod -l name=locust,role=master -o template --template="{{(index .items 0).metadata.name}}") 38089:8089

Then open in a browser: http://127.0.0.1:38089

## GKE Deploy

First create the cluster using the `gcloud` command as shown below. Using pre-emptible VMs which are in `beta`

    # TODO figure out the --addons= syntax for excluding dashboard etc as we dont need it really in this cluster
    gcloud beta container clusters create ryustar-load-generator-cluster-0 --cluster-version=1.8.5-gke.0 --addons= --disk-size=10 --machine-type=n1-standard-1 --num-nodes=1 --zone=us-central1-a --preemptible

This will also create a new `context` for you in `kubectl config`.

Deploy the load test pods:

    load-test/deploy_gke.sh

Open ports to the locust UI:

    # Then in a separate shell
    kubectl --context=gke_studious-osprey-189923_us-central1-a_ryustar-load-generator-cluster-0 port-forward $(kubectl --context=gke_studious-osprey-189923_us-central1-a_ryustar-load-generator-cluster-0 get pod -l name=locust,role=master -o template --template="{{(index .items 0).metadata.name}}") 38089:8089

Then open in a browser: http://127.0.0.1:38089

Then delete the cluster once done:

    gcloud container clusters delete ryustar-load-generator-cluster-0 --zone=us-central1-a


### Deploy locust

    ./deploy_gke.sh

## Execute Tests

To execute the Locust tests, navigate to the master on port `8089`, likely using `kubectl` proxy or expose or something, and enter the number of clients to spawn and the client hatch rate then start the simulation.

## Deployment Cleanup

To teardown the workload simulation cluster, just delete the Kubernetes cluster:

    gcloud container clusters delete CLUSTER-NAME
