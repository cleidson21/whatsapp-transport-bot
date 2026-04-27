import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_automacao.log")

# ====== CONFIGURAÇÃO DE LOGS ======
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ====== CONFIGURAÇÃO DE AMBIENTE WINDOWS ======
usuario_windows = os.getlogin()
# Definimos uma pasta segura nos seus Documentos para salvar o login do WhatsApp
perfil_path = rf"C:\Users\{usuario_windows}\Documents\WhatsApp_Bot_Profile"

opts = Options()
opts.add_argument(f"--user-data-dir={perfil_path}")
opts.add_argument("--profile-directory=Default")
opts.add_argument("--start-maximized")
# Desativamos logs desnecessários no terminal
opts.add_experimental_option("excludeSwitches", ["enable-logging"]) 

logging.info("🔥 Iniciando Warm-up do WhatsApp Web no Windows 11...")

# O webdriver_manager baixa o driver correto para a sua versão do Chrome automaticamente
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=opts)

try:
    driver.get("https://web.whatsapp.com")
    
    # Na primeira vez, você precisará ler o QR Code. 
    # O script vai esperar até 5 minutos para você fazer isso.
    logging.info("⏳ Aguardando carregamento ou leitura do QR Code (limite de 5 min)...")
    
    WebDriverWait(driver, 300).until(
        EC.presence_of_element_located((By.XPATH, "//div[@role='grid']"))
    )
    
    logging.info("✅ WhatsApp carregado com sucesso!")
    logging.info("⏳ Aguardando 60 segundos extras para garantir a sincronização do cache...")
    time.sleep(60) 

except Exception as e:
    logging.error(f"Erro no carregamento: {e}")
    logging.info("Dica: Verifique se não há outra instância do Chrome aberta usando este mesmo perfil.")

finally:
    driver.quit()
    logging.info("🏁 Warm-up concluído. Sessão salva em seu perfil local.")