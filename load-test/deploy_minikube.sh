set -o errexit
set -o verbose

cd "$(dirname "$0")"

eval $(minikube docker-env)
docker build -t gcr.io/studious-osprey-189923/locust-tasks:latest docker-image

kubectl apply --context="minikube" -f k8s
