FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements-backend.txt .
RUN pip install --no-cache-dir -r requirements-backend.txt
COPY backend backend
COPY crawler crawler
COPY utils utils
# 拷贝前端编译产物
COPY --from=frontend-builder /app/frontend/dist frontend/dist
ENV MONGO_URI=mongodb://mongo:27017/wechat_spider \
    JWT_SECRET=change-me \
    ADMIN_USER=admin \
    ADMIN_PASS=admin123
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "backend.app:app", "--timeout", "120"]

