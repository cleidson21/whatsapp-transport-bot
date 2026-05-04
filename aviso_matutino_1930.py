import os
import time
import humanizer
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
perfil_path = rf"C:\Users\{usuario_windows}\Documents\WhatsApp_Bot_Profile"

# Usamos uc.ChromeOptions() em vez das Options padrão do Selenium
opts = uc.ChromeOptions()
opts.add_argument(f"--user-data-dir={perfil_path}")
opts.add_argument("--profile-directory=Default")

# Inicia o Driver Indetetável
logging.info("Iniciando o Undetected Chrome...")
driver = uc.Chrome(options=opts, version_main=147)
driver.maximize_window()

# ====== CONFIGURAÇÕES DO FLUXO ======
GRUPOS_ALVO = [
    "Transporte UEFS-UFRB 2026",
    "Transporte FTC INTEGRAL 2026",
    "Transporte IFBA-UNEF Matutino 2026",
    "Transporte Matutino (Centro) 2026"
]
MENSAGEM_AVISO = "⚠️ *Aviso Sistema*: Lista fecha em 30 minutos!"

# --- FUNÇÕES DE NAVEGAÇÃO WHATSAPP ---

def clicar_grupo(nome_grupo):
    """Lógica de busca com XPath atualizado para a nova versão do WhatsApp Web."""
    try:
        logging.info(f"🔍 Buscando grupo: {nome_grupo}")
        
        # XPATH BLINDADO: Procura pela versão nova (<input>) e pela antiga (<div>)
        xpath_busca = "//input[@data-tab='3'] | //input[contains(@placeholder, 'Pesquisar')] | //div[@contenteditable='true' and @data-tab='3']"
        
        search_box = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, xpath_busca))
        )
        search_box.click()
        search_box.send_keys(Keys.CONTROL + "a")
        search_box.send_keys(Keys.BACK_SPACE)
        humanizer.human_sleep(0.5, 1.5)
        search_box.send_keys(nome_grupo)
        
        xpath_result = f"//div[@role='row']//span[@title='{nome_grupo}']"
        grupo = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, xpath_result)))
        grupo.click()
        logging.info(f"✅ Entrou no grupo: {nome_grupo}")
        return True
    except Exception as e:
        logging.error(f"Erro ao abrir grupo '{nome_grupo}': {e}")
        return False

# --- EXECUÇÃO ---
logging.info("=== INICIANDO AVISOS MATUTINOS (19:30H) ===")
driver.get("https://web.whatsapp.com")

try:
    # Aguarda o carregamento inicial (limite 5 min)
    WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.XPATH, "//div[@role='grid']")))
    logging.info("✅ WhatsApp Web carregado com sucesso.")
    humanizer.human_sleep(8.0, 12.0)

    avisos_enviados = 0
    avisos_falhados = []
    
    for grupo in GRUPOS_ALVO:
        if clicar_grupo(grupo):
            try:
                caixa = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true' and @data-tab='10']"))
                )
                caixa.click()
                caixa.send_keys(MENSAGEM_AVISO)
                caixa.send_keys(Keys.ENTER)
                logging.info(f"✉️ Aviso enviado em: {grupo}")
                avisos_enviados += 1
                humanizer.short_human_sleep()
            except Exception as e:
                logging.error(f"Erro ao enviar aviso em {grupo}: {e}")
                avisos_falhados.append(grupo)
        else:
            avisos_falhados.append(grupo)

    logging.info(f"📊 Resumo de Avisos: {avisos_enviados}/{len(GRUPOS_ALVO)} enviados com sucesso.")
    if avisos_falhados:
        logging.info(f"Falhados: {avisos_falhados}")

finally:
    logging.info("🏁 Rotina de avisos (19:30H) finalizada.")
    driver.quit()