@echo off
echo ========================================================
echo   INICIANDO SERVIDOR DO WHATSAPP (EVOLUTION API)
echo ========================================================
echo.
echo Aguardando 30 segundos para o motor do Docker carregar...
timeout /t 30 /nobreak

echo.
echo Navegando para a pasta do servidor...
cd /d "C:\Users\cleid\Music\servidor-whatsapp"

echo.
echo Subindo os containers (Postgres, Redis, API, Manager)...
docker compose up -d

echo.
echo Servidor online! Esta janela fechar-se-a em 5 segundos.
timeout /t 5 /nobreak
exit