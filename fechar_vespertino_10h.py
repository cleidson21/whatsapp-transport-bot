import os
import time
import humanizer
import logging
import re
from datetime import datetime, timedelta
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

# (Modo enxuto) Removida integração com IA e coleta de listas.
# O script apenas controla abertura/fechamento e envia solicitações simples.
# ====== CONFIGURAÇÃO DE AMBIENTE WINDOWS ======
usuario_windows = os.getlogin()
perfil_path = rf"C:\Users\{usuario_windows}\Documents\WhatsApp_Bot_Profile"

opts = Options()
opts.add_argument(f"--user-data-dir={perfil_path}")
opts.add_argument("--profile-directory=Default")
opts.add_argument("--start-maximized")
opts.add_experimental_option("excludeSwitches", ["enable-logging"])

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=opts)
GRUPOS_ALVO = [
    "Transporte UEFS-UFRB 2026",
    "Transporte FTC INTEGRAL 2026",
    "Transporte Vespertino 2026"
]
GRUPO_COORDENACAO = "Operação Transporte Universitário"
MENSAGEM_FECHAMENTO = "❌✖️❌✖️Lista Fechada ❌✖️❌✖️"
MENSAGEM_SOLICITAR_LISTA = "Por favor, enviar a lista do turno fechado: VESPERTINO."

# --- FUNÇÕES DE NAVEGAÇÃO WHATSAPP ---

def clicar_grupo(nome_grupo):
    """Lógica de busca com XPath atualizado para a nova versão do WhatsApp Web."""
    try:
        logging.info(f"🔍 Buscando grupo: {nome_grupo}")
        
        # XPATH BLINDADO: Procura pela versão nova (<input>) e pela antiga (<div>)
        xpath_busca = "//input[@data-tab='3'] | //input[contains(@placeholder, 'Pesquisar')] | //div[@contenteditable='true' and @data-tab='3']"
        
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, xpath_busca))
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

def tentar_fechar_grupo(nome_grupo):
    try:
        logging.info(f"Procurando o botão de fechar para {nome_grupo}...")
        xpath_switch = "//div[contains(@aria-label, 'mensagens')]//input[@type='checkbox'] | //input[@role='switch' and contains(@aria-label, 'mensagens')]"
        switch = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath_switch)))
        
        if switch.get_attribute("aria-checked") == "true": 
            driver.execute_script("arguments[0].click();", switch)
            logging.info(f"🔒 Status alterado: Grupo FECHADO ({nome_grupo}).")
            humanizer.short_human_sleep(1.5, 2.5)
            return True
        else:
            logging.info(f"ℹ️ O grupo {nome_grupo} já estava fechado.")
            return False
    except Exception as e:
        logging.error(f"Falha ao clicar no switch de fechamento do grupo {nome_grupo}: {e}")
        return False

def enviar_msg_chat_simples(mensagem):
    try:
        caixa = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"))
        )
        caixa.click()
        caixa.send_keys(mensagem)
        caixa.send_keys(Keys.ENTER)
        logging.info("✉️ Mensagem simples enviada.")
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem simples: {e}")

def enviar_msg_chat_multilinha(texto):
    try:
        xpath_caixa = "//div[@contenteditable='true' and @role='textbox'] | //footer//div[@contenteditable='true'] | //div[@contenteditable='true'][@data-tab='10']"
        caixa = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_caixa))
        )
        caixa.click()
        for linha in texto.split('\n'):
            linha_segura = linha.encode('utf-16', 'surrogatepass').decode('utf-16')
            caixa.send_keys(linha_segura)
            caixa.send_keys(Keys.SHIFT, Keys.ENTER)
        caixa.send_keys(Keys.ENTER)
        logging.info("✉️ Quantitativos da tarde enviados com sucesso.")
    except Exception as e: 
        logging.error(f"Erro ao enviar relatório multilinha: {e}")

def voltar_fechar_paineis():
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ESCAPE)
        time.sleep(0.5)
        body.send_keys(Keys.ESCAPE)
    except: pass

# --- FLUXO PRINCIPAL ---
logging.info("=== INICIANDO FECHAMENTO VESPERTINO (10H) ===")
driver.get("https://web.whatsapp.com")

try:
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//div[@role='grid']")))
    logging.info("✅ WhatsApp Web carregado com sucesso.")
    time.sleep(10)

    grupos_fechados = 0
    grupos_falhados = []
    
    for grupo in GRUPOS_ALVO:
        logging.info(f"--- Processando: {grupo} ---")
        if clicar_grupo(grupo):
            try:
                header_xpath = '//*[@id="main"]/header'
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, header_xpath)))
                humanizer.human_sleep(2.5, 5.0)
                driver.find_element(By.XPATH, header_xpath).click()

                xpath_perm = "//span[text()='Permissões do grupo']"
                btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_perm)))
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                humanizer.short_human_sleep()
                btn.click()

                if tentar_fechar_grupo(grupo):
                    grupos_fechados += 1
                    logging.info(f"📣 Enviando aviso de fechamento para {grupo}.")
                else:
                    logging.info(f"📣 Grupo {grupo} já estava fechado; enviando aviso mesmo assim.")

                voltar_fechar_paineis()
                humanizer.short_human_sleep()
                enviar_msg_chat_simples(MENSAGEM_FECHAMENTO)
                humanizer.look_at_screen_pause()
                    
            except Exception as e:
                logging.error(f"❌ Erro fatal no fluxo do grupo {grupo}: {e}")
                grupos_falhados.append(grupo)
                voltar_fechar_paineis()
        else:
            grupos_falhados.append(grupo)

    logging.info(f"📊 Resumo: {grupos_fechados}/{len(GRUPOS_ALVO)} grupos processados. Falhados: {grupos_falhados}")
    
    # Envia solicitação simples ao grupo de operação
    if clicar_grupo(GRUPO_COORDENACAO):
        logging.info("A enviar solicitação de lista para o grupo de operação...")
        enviar_msg_chat_simples(MENSAGEM_SOLICITAR_LISTA)
        
    time.sleep(5) 

finally:
    logging.info("🏁 Processo de fechamento vespertino finalizado.")
    driver.quit()