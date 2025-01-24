#!/bin/bash

# Define the environment name
ENV_NAME="env"

# Check if virtual environment directory already exists
if [ -d "$ENV_NAME" ]; then
    echo "Virtual environment '$ENV_NAME' already exists."
else
    # Create a virtual environment
    echo "Creating virtual environment..."
    python3 -m venv "$ENV_NAME"
    echo "Virtual environment '$ENV_NAME' created."
fi

# Activate the virtual environment


if [ -d "$ENV_NAME/bin/activate" ]; then
    source "$ENV_NAME/bin/activate"
else
    # Create a virtual environment
    .\env\Scripts\activate
fi


# Install the required packages
echo "Installing requirements..."
pip install -r requirements.txt

echo "Setup complete. To activate the environment, use 'source $ENV_NAME/bin/activate'."
