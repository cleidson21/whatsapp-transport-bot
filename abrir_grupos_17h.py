import os
import time
import humanizer
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
perfil_path = rf"C:\Users\{usuario_windows}\Documents\WhatsApp_Bot_Profile"

opts = Options()
opts.add_argument(f"--user-data-dir={perfil_path}")
opts.add_argument("--profile-directory=Default")
opts.add_argument("--start-maximized")
opts.add_experimental_option("excludeSwitches", ["enable-logging"])

# Inicia o Driver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=opts)

# ====== LISTA DE GRUPOS PARA ABRIR (17h) ======
GRUPOS_ALVO = [
    "Transporte UEFS-UFRB 2026",
    "Transporte FTC INTEGRAL 2026",
    "Transporte Vespertino 2026",
    "Transporte FTC Noturno 2026",
    "Transporte FAN Noturno 2026",
    "Transporte FAT Noturno 2026",
    "Transporte UNIFACS Noturno 2026",
    "Transporte IFBA-UNEF Noturno 2026",
    "Transporte UEFS Noturno 2026",
    "Transporte SENAI-PITAGORAS Noturno 2026"
]

# --- FUNÇÕES COM LÓGICA VALIDADA ---

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
        
        # Limpa o campo de busca
        search_box.send_keys(Keys.CONTROL + "a")
        search_box.send_keys(Keys.BACK_SPACE)
        humanizer.short_human_sleep()
        
        # Digita o nome do grupo
        search_box.send_keys(nome_grupo)
        humanizer.human_sleep(4.0, 6.0)
        
        # Seleciona o grupo na lista
        xpath_result = f"//div[@role='row']//span[@title='{nome_grupo}']"
        grupo = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, xpath_result)))
        grupo.click()
        
        logging.info(f"✅ Grupo aberto: {nome_grupo}")
        humanizer.short_human_sleep()
        return True
        
    except Exception as e:
        logging.error(f"Erro ao abrir grupo '{nome_grupo}': {e}")
        return False

def abrir_permissoes_do_grupo():
    try:
        logging.info("🔍 Buscando botão 'Permissões do grupo'...")
        xpath_perm = "//span[text()='Permissões do grupo']"
        btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_perm)))
        
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        humanizer.short_human_sleep()
        btn.click()
        logging.info("✅ Menu 'Permissões do grupo' aberto.")
        return True
    except Exception as e:
        logging.error(f"Erro ao abrir 'Permissões do grupo': {e}")
        return False

def ativar_envio_mensagens():
    try:
        xpath_switch = "//div[contains(@aria-label, 'mensagens')]//input[@type='checkbox'] | //input[@role='switch' and contains(@aria-label, 'mensagens')]"
        switch = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath_switch)))
        
        estado_atual = switch.get_attribute("aria-checked")
        
        if estado_atual == "false": 
            driver.execute_script("arguments[0].click();", switch)
            logging.info("✅ Grupo ABERTO (mensagens ativadas).")
            humanizer.short_human_sleep()
        else:
            logging.info("ℹ️ Grupo já estava aberto.")
        return True
    except Exception as e:
        logging.error(f"Erro ao ativar mensagens: {e}")
        return False

def processo_abrir_grupo(nome_grupo):
    if not clicar_grupo(nome_grupo): return
    
    try:
        print(f"🖱️ Abrindo painel de dados: {nome_grupo}")
        
        # O XPath tradicional que mapeia o cabeçalho inteiro
        header_xpath = '//*[@id="main"]/header'
        header_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, header_xpath))
        )
        
        # Clique nativo do Selenium (mira no centro da barra)
        header_btn.click()
        humanizer.human_sleep(2.5, 5.0)
        
        if abrir_permissoes_do_grupo():
            ativar_envio_mensagens()
            
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            humanizer.short_human_sleep()
            body.send_keys(Keys.ESCAPE)
            print(f"🏁 Processo concluído para {nome_grupo}\n")
            
    except Exception as e:
        print(f"⚠️ Falha no fluxo do grupo {nome_grupo}: {e}")

# --- EXECUÇÃO PRINCIPAL ---
logging.info("=== INICIANDO ABERTURA DE GRUPOS (17H) ===")
driver.get("https://web.whatsapp.com")

try:
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//div[@role='grid']")))
    logging.info("✅ WhatsApp Web carregado com sucesso.")
    humanizer.human_sleep(8.0, 12.0)

    grupos_abertos = 0
    
    for grupo in GRUPOS_ALVO:
        logging.info(f"--- Processando: {grupo} ---")
        if processo_abrir_grupo(grupo):
            grupos_abertos += 1

    logging.info(f"📊 {grupos_abertos}/{len(GRUPOS_ALVO)} grupos processados.")

finally:
    logging.info("🏁 Rotina de abertura (17H) finalizada.")
    driver.quit()