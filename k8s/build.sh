set -o errexit
set -o verbose

cd "$(dirname "$0")"

# needed for mustache
yarn install

rm -rf dist
for K8_ENV in gcloud minikube; do
  TEMPLATE_DATA="$(jq --compact-output "(.base + .$K8_ENV)" ../global-config.json)"
  mkdir -p dist/$K8_ENV
  find src/$K8_ENV src/all -type f -name "*.mustache" | while read file; do
    IN_FILENAME="${file#src/*/}"
    OUT_FILENAME="${IN_FILENAME%.mustache}"
    OUT_FILEPATH="dist/$K8_ENV/$OUT_FILENAME"
    yarn run mustache <(echo "$TEMPLATE_DATA") "$file" "$OUT_FILEPATH"
  done
done
