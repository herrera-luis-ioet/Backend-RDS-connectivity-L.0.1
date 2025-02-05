#!/bin/bash
cd /home/kavia/workspace/Backend-RDS-connectivity-L.0.1/product_order_api

# 1.) Run the linters on the files or directories passed as arguments
flake8 "$@"
FLAKE8_EXIT_CODE=$?

black --check "$@"
BLACK_EXIT_CODE=$?

# 2.) Test the packaging of the application
pip install -e .
INSTALL_EXIT_CODE=$?

# Exit with error if any command failed
if [ $FLAKE8_EXIT_CODE -ne 0 ] || [ $BLACK_EXIT_CODE -ne 0 ] || [ $INSTALL_EXIT_CODE -ne 0 ]; then
    exit 1
fi