import os
import time
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

# ====== LISTA DE GRUPOS PARA ABRIR ======
GRUPOS_ALVO = [
    "Transporte UEFS Sábado 2026"
]

# --- LÓGICA VALIDADA NO TESTE ---

def clicar_grupo(nome_grupo):
    """Versão antiga validada que funciona perfeitamente no Windows."""
    try:
        logging.info(f"🔍 Buscando grupo: {nome_grupo}")
        search_box = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true' and @data-tab='3']"))
        )
        search_box.click()
        search_box.send_keys(Keys.CONTROL + "a")
        search_box.send_keys(Keys.BACK_SPACE)
        time.sleep(0.5)
        search_box.send_keys(nome_grupo)
        time.sleep(2)
        
        xpath_result = f"//div[@role='row']//span[@title='{nome_grupo}']"
        grupo = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_result)))
        grupo.click()
        logging.info(f"✅ Grupo aberto: {nome_grupo}")
        return True
    except Exception as e:
        logging.error(f"Erro ao abrir grupo '{nome_grupo}': {e}")
        return False

def abrir_permissoes_do_grupo():
    """Versão nova validada com o texto exato do span."""
    try:
        logging.info("🔍 Buscando botão 'Permissões do grupo'...")
        xpath_perm = "//span[text()='Permissões do grupo']"
        btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_perm)))
        
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        time.sleep(1)
        btn.click()
        logging.info("✅ Menu 'Permissões do grupo' aberto.")
        return True
    except Exception as e:
        logging.error(f"Erro ao abrir 'Permissões do grupo': {e}")
        return False

def ativar_envio_mensagens():
    """Versão nova validada usando o switch dinâmico."""
    try:
        xpath_switch = "//div[contains(@aria-label, 'mensagens')]//input[@type='checkbox'] | //input[@role='switch' and contains(@aria-label, 'mensagens')]"
        switch = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath_switch)))
        
        estado_atual = switch.get_attribute("aria-checked")
        
        if estado_atual == "false": # Se estiver fechado, abre
            driver.execute_script("arguments[0].click();", switch)
            logging.info("✅ Grupo ABERTO (mensagens ativadas).")
            time.sleep(1)
        else:
            logging.info("ℹ️ Grupo já estava aberto.")
        return True
    except Exception as e:
        logging.error(f"Erro ao ativar mensagens: {e}")
        return False

def processo_abrir_grupo(nome_grupo):
    if not clicar_grupo(nome_grupo): return
    
    try:
        # ESTRATÉGIA ATUALIZADA: Mapeia o cabeçalho inteiro e usa clique nativo
        logging.info(f"🖱️ Abrindo painel de dados para {nome_grupo}...")
        header_xpath = '//*[@id="main"]/header'
        header_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, header_xpath))
        )
        header_btn.click()
        time.sleep(2)
        
        if abrir_permissoes_do_grupo():
            ativar_envio_mensagens()
            
            # Fecha os painéis com ESC
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            time.sleep(0.5)
            body.send_keys(Keys.ESCAPE)
            logging.info(f"✅ Processamento concluído para {nome_grupo}\n")
            
    except Exception as e:
        logging.error(f"Erro no fluxo do grupo {nome_grupo}: {e}")

# --- EXECUÇÃO PRINCIPAL ---
logging.info("=== INICIANDO ABERTURA DE GRUPO SÁBADO (12H) ===")
driver.get("https://web.whatsapp.com")

try:
    # Aguarda o carregamento inicial da grade de mensagens
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//div[@role='grid']")))
    logging.info("✅ WhatsApp Web carregado com sucesso.")
    time.sleep(10)

    grupos_abertos = 0
    grupos_falhados = []
    
    for grupo in GRUPOS_ALVO:
        logging.info(f"--- Processando: {grupo} ---")
        if clicar_grupo(grupo):
            try:
                header_xpath = '//*[@id="main"]/header'
                header_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, header_xpath))
                )
                header_btn.click()
                time.sleep(2)
                
                if abrir_permissoes_do_grupo():
                    if ativar_envio_mensagens():
                        grupos_abertos += 1
                    
                    body = driver.find_element(By.TAG_NAME, "body")
                    body.send_keys(Keys.ESCAPE)
                    time.sleep(0.5)
                    body.send_keys(Keys.ESCAPE)
                        
            except Exception as e:
                logging.error(f"❌ Erro no fluxo do grupo {grupo}: {e}")
                grupos_falhados.append(grupo)
        else:
            grupos_falhados.append(grupo)

    logging.info(f"📊 Resumo: {grupos_abertos}/{len(GRUPOS_ALVO)} grupos abertos. Falhados: {grupos_falhados}")

finally:
    logging.info("🏁 Rotina de abertura de sábado finalizada.")
    driver.quit()