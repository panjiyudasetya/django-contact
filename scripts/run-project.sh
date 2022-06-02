#!/bin/bash

. scripts/build-and-pack.sh

function activate_virtual_env {
    source ./.venv/bin/activate
}

function run_on_port {
    PORT=$1
    cd test_project
    pip install -r requirements.txt
    python manage.py runserver "0.0.0.0:${PORT}"
}


# Main
activate_virtual_env
install_package_locally
run_on_port "1234"
