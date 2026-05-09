# --- Stage 1: Build Frontend ---
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Build Backend & Final Image ---
FROM python:3.11-slim
WORKDIR /app

# Instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do backend
COPY app/ ./app/

# Copia os arquivos estáticos do frontend do Stage 1 para a pasta 'static'
COPY --from=frontend-builder /app/frontend/dist ./static

# Define variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Comando para rodar a aplicação usando uvicorn
# Usamos 0.0.0.0 para que o Cloud Run possa acessar o serviço
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
