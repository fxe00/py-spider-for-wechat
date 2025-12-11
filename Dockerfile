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
# 运行时敏感配置请通过 docker-compose/.env 注入，不在镜像内硬编码
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "backend.app:app", "--timeout", "120"]