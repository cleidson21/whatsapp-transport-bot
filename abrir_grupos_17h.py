import os
import time
import humanizer
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CORREÇÃO DE DIRETÓRIO PARA O WINDOWS ---
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
driver = uc.Chrome(options=opts)
driver.maximize_window()

# ====== LISTA DE GRUPOS PARA ABRIR ======
GRUPOS_ALVO = [
    "Transporte SENAI-PITAGORAS Noturno 2026",
    "Transporte UEFS Noturno 2026",
    "Transporte IFBA-UNEF Noturno 2026",
    "Transporte UNIFACS Noturno 2026",
    "Transporte FAT Noturno 2026",
    "Transporte FAN Noturno 2026",
    "Transporte FTC Noturno 2026"
]

# --- LÓGICA VALIDADA NO TESTE ---

def clicar_grupo(nome_grupo):
    """Versão antiga validada que funciona perfeitamente no Windows com o novo XPATH."""
    try:
        logging.info(f"🔍 Buscando grupo: {nome_grupo}")
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
        logging.info(f"✅ Grupo aberto: {nome_grupo}")
        return True
    except Exception as e:
        logging.error(f"⚠️ Erro ao abrir grupo {nome_grupo}: {e}")
        return False

def abrir_permissoes_do_grupo():
    """Versão nova validada com o texto exato do span."""
    try:
        logging.info("🔍 Buscando botão 'Permissões do grupo'...")
        xpath_perm = "//span[text()='Permissões do grupo']"
        btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_perm)))
        
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        humanizer.human_sleep(1.0, 2.0)
        btn.click()
        logging.info("✅ Menu 'Permissões do grupo' clicado.")
        return True
    except Exception as e:
        logging.error(f"⚠️ Não encontrou 'Permissões do grupo': {e}")
        return False

def ativar_envio_mensagens():
    """Versão nova validada usando o switch dinâmico."""
    try:
        xpath_switch = "//div[contains(@aria-label, 'mensagens')]//input[@type='checkbox'] | //input[@role='switch' and contains(@aria-label, 'mensagens')]"
        switch = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath_switch)))
        
        estado_atual = switch.get_attribute("aria-checked")
        
        if estado_atual == "false": # Se estiver fechado, abre
            driver.execute_script("arguments[0].click();", switch)
            logging.info("✅ Switch ativado: Grupo ABERTO.")
            humanizer.human_sleep(1.0, 2.0)
        else:
            logging.info("ℹ️ Grupo já estava aberto.")
        return True
    except Exception as e:
        logging.error(f"⚠️ Erro ao ativar mensagens: {e}")
        return False

# --- EXECUÇÃO PRINCIPAL ---
logging.info("=== INICIANDO ABERTURA DE GRUPOS (17H) ===")
driver.get("https://web.whatsapp.com")

try:
    # Aguarda o carregamento inicial da grade de mensagens (com tempo estendido de 5 min)
    WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.XPATH, "//div[@role='grid']")))
    logging.info("✅ WhatsApp Web carregado com sucesso.")
    humanizer.human_sleep(8.0, 12.0)

    grupos_abertos = 0
    grupos_falhados = []
    
    for grupo in GRUPOS_ALVO:
        logging.info(f"--- Processando: {grupo} ---")
        if clicar_grupo(grupo):
            try:
                logging.info(f"🖱️ Abrindo painel de dados...")
                
                header_xpath = '//*[@id="main"]/header'
                header_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, header_xpath))
                )
                header_btn.click()
                humanizer.human_sleep(1.5, 3.0)
                
                if abrir_permissoes_do_grupo():
                    if ativar_envio_mensagens():
                        grupos_abertos += 1
                    
                    body = driver.find_element(By.TAG_NAME, "body")
                    body.send_keys(Keys.ESCAPE)
                    humanizer.short_human_sleep()
                    body.send_keys(Keys.ESCAPE)
                        
            except Exception as e:
                logging.error(f"❌ Erro no fluxo do grupo {grupo}: {e}")
                grupos_falhados.append(grupo)
        else:
            grupos_falhados.append(grupo)

    logging.info(f"📊 Resumo: {grupos_abertos}/{len(GRUPOS_ALVO)} grupos abertos.")
    if grupos_falhados:
        logging.info(f"Falhados: {grupos_falhados}")

finally:
    logging.info("🏁 Rotina de abertura (17H) finalizada.")
    driver.quit()