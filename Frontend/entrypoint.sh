#!/bin/bash

# Change ownership of the mounted volume to "appuser"
chown -R appuser:appuser /home/app/data

# Execute the specified command
exec "$@"
