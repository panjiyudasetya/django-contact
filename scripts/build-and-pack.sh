#!/bin/bash

function clean_code_dist {
    echo "Removing built code distribution..."
    rm -rf ./build
    rm -rf ./dist

    echo "Removing egg-info..."
    rm -rf *.egg-info
}


function build_code_distribution {
    clean_code_dist

    echo "Build and pack the \"django_contact\" source code"
    echo "Creating a new code distribution..."
    python setup.py sdist
}


function install_package_locally {
    echo "Uninstalling \"django_contact\"..."
    yes | pip uninstall django-contact

    echo "Installing \"django_contact\" to the \"test_project\"..."
    python setup.py install

    clean_code_dist
}
