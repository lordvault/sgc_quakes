#!/usr/bin/with-contenv bashio

bashio::log.info "Starting SGC Quakes Colombia Add-on..."

# Run the python daemon
exec python3 -u /app.py
