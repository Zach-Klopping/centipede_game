#!/bin/bash

heroku ps:scale web=0 worker=0 -a centipede-game
heroku addons:destroy heroku-postgresql --confirm centipede-game
heroku addons:destroy heroku-redis --confirm centipede-game
