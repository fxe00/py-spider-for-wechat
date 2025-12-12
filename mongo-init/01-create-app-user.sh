#!/bin/bash
set -eu

# This script runs inside the mongo container during initialization
# It uses environment variables from docker-compose (.env)

echo "[mongo-init] creating app user in database '${MONGO_DB:-wechat_spider}'"

DB_NAME=${MONGO_DB:-wechat_spider}
APP_USER=${MONGO_USER:-app_user_123}
APP_PASS=${MONGO_PASS:-app_user_password_123}

cat <<EOF | mongo --quiet
use ${DB_NAME}
db.createUser({user: "${APP_USER}", pwd: "${APP_PASS}", roles: [ { role: "readWrite", db: "${DB_NAME}" } ]})
EOF

echo "[mongo-init] finished creating user '${APP_USER}' on '${DB_NAME}'"
