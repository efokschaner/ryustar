# Load Test for RyuStar

## Notes on cluster size

Based on some very scientific reading of blog posts, I predict we may be able to get on the order of 1000 locust users per core.
Each locust worker is single threaded so distribute them 1 per core

## Local run

    locust -f docker-image/locust-tasks/tasks.py --host=https://www.ryustar.io

## Minikiube run

    ./deploy_minikube

## GKE Deploy

First create the cluster using the `gcloud` command as shown below. Using pre-emptible VMs which are in `beta`

    gcloud beta container clusters create CLUSTER-NAME --cluster-version=1.8.4-gke.1 --addons= --disk-size=10G --machine-type=n1-standard-1 --num-nodes=NUM_WORKERS_PLUS_ONE --zone=us-central1-a --preemptible

**Note:** the output from the `gcloud container clusters create` command will contain the specific `kubectl config` command to execute for your platform/project.

### Deploy locust

    ./deploy_gke.sh

## Execute Tests

To execute the Locust tests, navigate to the master on port `8089`, likely using `kubectl` proxy or expose or something, and enter the number of clients to spawn and the client hatch rate then start the simulation.

## Deployment Cleanup

To teardown the workload simulation cluster, just delete the Kubernetes cluster:

    gcloud container clusters delete CLUSTER-NAME
