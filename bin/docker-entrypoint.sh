#!/usr/bin/env bash
set -e

pipenv run ./manage.py migrate
pipenv run $@
