#!/bin/sh
# Guarda as variáveis de ambiente (.env) para o cron conseguir ler
env >> /etc/environment
# Inicia o cron em segundo plano e mantém o contentor vivo
exec cron -f