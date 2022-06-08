#!/bin/bash

function setup_environment {
    . scripts/.env.sh
    . scripts/build-and-pack.sh

    source ./.venv/bin/activate
}

function run_project {
    cd test_project
    pip install -r requirements.txt

    python manage.py runserver "${SERVER}:${PORT}"
}


# Main
setup_environment
install_package_locally
run_project
