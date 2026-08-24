#!/bin/bash
# Launch Kanban Dashboard

cd "$(dirname "$0")"

# Start server if not running
if ! curl -s http://localhost:8088/api/board > /dev/null 2>&1; then
    echo "Starting server..."
    nohup python3 server.py > /tmp/kanban.log 2>&1 &
    sleep 2
fi

# Open browser
open http://localhost:8088
echo "Dashboard: http://localhost:8088"
