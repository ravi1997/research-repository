#!/bin/bash

# Define the environment name
ENV_NAME="env"

# Activate the virtual environment
if [ -d "$ENV_NAME/bin/activate" ]; then
    source "$ENV_NAME/bin/activate"
else
    # Create a virtual environment
    .\env\Scripts\activate
fi

if [ -d "migrations" ]; then
    rm -rf migrations
    rm -rf app/app.db
fi

# Install the required packages
flask db init
flask db migrate
flask db upgrade

flask seed-db