#!/bin/bash
echo "Checking for requirements.txt..."
if [ ! -f requirements.txt ]; then
    echo "ERROR: requirements.txt not found!"
    exit 1
fi

echo "Validating requirements.txt format..."
pip check requirements.txt

echo "Testing virtual environment creation..."
python -m venv test_venv
source test_venv/bin/activate
pip install --upgrade pip
echo "Attempting to install dependencies..."
pip install -r requirements.txt

echo "Debug complete. If no errors appeared, your setup should work with Docker."
deactivate
rm -rf test_venv
