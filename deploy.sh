#!/bin/bash

git checkout main
git pull


heroku login
heroku git:remote -a centipede-game
git push -f heroku main


heroku addons:create heroku-postgresql:standard-0
heroku addons:create heroku-redis:premium-0
heroku ps:scale web=1:standard-1x


APP_NAME="centipede-game"
ADDONS=("heroku-postgresql" "heroku-redis")

for ADDON_TYPE in "${ADDONS[@]}"; do
  echo "Waiting for $ADDON_TYPE to be ready..."

  while true; do
    STATUS=$(heroku addons -a "$APP_NAME" | grep "$ADDON_TYPE" | awk '{print $NF}')
    if [[ "$STATUS" == "created" || "$STATUS" == "attached" ]]; then
      echo "$ADDON_TYPE is ready."
      break
    else
      echo "Current status of $ADDON_TYPE: $STATUS. Waiting 30 seconds..."
      sleep 30
    fi
  done
done
