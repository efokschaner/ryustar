set -o errexit
set -o verbose

cd "$(dirname "$0")"

docker build -t gcr.io/studious-osprey-189923/locust-tasks:latest docker-image

# Deploys
gcloud docker -- push gcr.io/studious-osprey-189923/locust-tasks:latest
kubectl apply --context="gke_studious-osprey-189923_us-central1-a_ryustar-load-generator-cluster-0" -f k8s
