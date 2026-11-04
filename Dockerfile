FROM python:3.10-slim

# Instalar o cron e configurar o fuso horário para a Bahia
RUN apt-get update && apt-get install -y cron tzdata && rm -rf /var/lib/apt/lists/*
ENV TZ=America/Bahia
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Instalar dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o projeto para dentro do contentor
COPY . .

# Configurar o cron e o script de inicialização
COPY crontab_bot /etc/cron.d/bot-cron
RUN chmod 0644 /etc/cron.d/bot-cron
RUN crontab /etc/cron.d/bot-cron
RUN touch /app/whatsapp-transport-bot-main/whatsapp_api_automacao.log

RUN chmod +x entrypoint.sh

# O entrypoint garante que as variáveis do .env chegam ao cron
ENTRYPOINT ["/app/entrypoint.sh"]