import os
import time
import humanizer
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
# Definimos uma pasta segura nos seus Documentos para guardar o login do WhatsApp
perfil_path = rf"C:\Users\{usuario_windows}\Documents\WhatsApp_Bot_Profile"

# Usamos uc.ChromeOptions() em vez das Options padrão do Selenium
opts = uc.ChromeOptions()
opts.add_argument(f"--user-data-dir={perfil_path}")
opts.add_argument("--profile-directory=Default")

logging.info("🔥 A iniciar Warm-up do WhatsApp Web no Windows com Undetected Chrome...")

# Inicia o Driver Indetetável
driver = uc.Chrome(options=opts)
driver.maximize_window()

try:
    driver.get("https://web.whatsapp.com")
    
    # Na primeira vez, precisará de ler o QR Code. 
    # O script vai esperar até 5 minutos para que possa fazer isso com calma.
    logging.info("⏳ A aguardar carregamento ou leitura do QR Code (limite de 5 min)...")
    
    WebDriverWait(driver, 300).until(
        EC.presence_of_element_located((By.XPATH, "//div[@role='grid']"))
    )
    
    logging.info("✅ WhatsApp carregado com sucesso!")
    logging.info("⏳ A aguardar alguns segundos extras para garantir a sincronização do cache...")
    humanizer.human_sleep(50.0, 70.0)

except Exception as e:
    logging.error(f"❌ Erro durante o warm-up: {e}")

finally:
    logging.info("🏁 Warm-up concluído. Sessão guardada no seu perfil local.")
    driver.quit()