# ============================================================
# VOCA — Single-container deployment (Backend + Frontend)
# ============================================================

# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install --include=dev
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + serve frontend static files
FROM python:3.13-slim
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./

# Copy built frontend into backend/static
COPY --from=frontend-build /app/frontend/dist ./static

# Expose the port Railway provides
ENV PORT=8080
EXPOSE 8080

# Start the server
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
