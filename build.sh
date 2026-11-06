#!/bin/bash
# Railway build script: builds frontend and copies dist into backend/static
set -e

echo "=== Building VOCA Frontend ==="
cd /app/frontend
npm install --include=dev
npm run build

echo "=== Copying frontend build to backend/static ==="
mkdir -p /app/backend/static
cp -r /app/frontend/dist/* /app/backend/static/

echo "=== Installing Backend Dependencies ==="
cd /app/backend
pip install -r requirements.txt

echo "=== Build Complete ==="
ls -la /app/backend/static/

