#!/bin/bash
# Startup script for Railway deployment
# Ensures Streamlit binds to the correct PORT

PORT=${PORT:-8501}
echo "Starting Streamlit on port $PORT..."

exec streamlit run dashboard/app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
