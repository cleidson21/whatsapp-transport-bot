import os
import time
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
from google import genai
from ia_fallback_helper import gerar_texto_ia_com_fallback

# ====== CONFIGURAÇÃO DE LOGS (NOVO) ======
# Grava tudo na tela E num arquivo de texto para auditoria
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ====== CONFIGURAÇÃO DA IA ======
try:
    from api_key_config import GOOGLE_API_KEY
except ImportError as exc:
    raise RuntimeError(
        "Arquivo api_key_config.py nao encontrado. Crie o arquivo com GOOGLE_API_KEY='sua_chave'."
    ) from exc

if not GOOGLE_API_KEY or GOOGLE_API_KEY == "sua_chave_aqui":
    raise RuntimeError("Defina GOOGLE_API_KEY corretamente no arquivo api_key_config.py.")

client = genai.Client(api_key=GOOGLE_API_KEY)

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

# ====== CONFIGURAÇÕES DO FLUXO (NOTURNO PRODUÇÃO) ======
GRUPOS_ALVO = [
    "Transporte SENAI-PITAGORAS Noturno 2026",
    "Transporte UEFS Noturno 2026",
    "Transporte IFBA-UNEF Noturno 2026",
    "Transporte UNIFACS Noturno 2026",
    "Transporte FAT Noturno 2026",
    "Transporte FAN Noturno 2026",
    "Transporte FTC Noturno 2026"
]
GRUPO_COORDENACAO = "Coordenação Transporte Universitário"
MENSAGEM_FECHAMENTO = "❌✖️❌✖️Lista Fechada ❌✖️❌✖️"

textos_coletados = {}

# --- FUNÇÕES DA IA E EXTRAÇÃO ---

def extrair_texto_lista():
    """Lê as mensagens da tela, clica em 'Ler mais' e busca a lista completa."""
    try:
        time.sleep(2) 
        try:
            botoes_ler_mais = driver.find_elements(By.XPATH, "//*[contains(text(), 'Ler mais')]")
            for btn in botoes_ler_mais:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
        except:
            pass
            
        mensagens = driver.find_elements(By.XPATH, "//div[@role='row']")
        
        for msg in reversed(mensagens):
            texto = msg.text
            texto_maiusculo = texto.upper()
            
            if len(texto) > 100 and ("LISTA" in texto_maiusculo or "IDA" in texto_maiusculo or "VOLTA" in texto_maiusculo):
                return texto
                
        return "NENHUMA LISTA IDENTIFICADA"
    except Exception as e:
        logging.error(f"Erro ao extrair lista: {e}")
        return f"ERRO NA EXTRAÇÃO: {e}"

def normalizar_resumo_ia(texto):
    """Normaliza marcadores para evitar linhas com '* *' no WhatsApp."""
    texto = (texto or "").replace("\u2060", "").replace("\ufeff", "")
    linhas_limpas = []

    for linha in texto.splitlines():
        conteudo = linha.strip()

        if conteudo == "*":
            continue

        while re.match(r"^\*\s+\*", conteudo):
            conteudo = re.sub(r"^\*\s+\*\s*", "* ", conteudo, count=1)

        if conteudo.startswith("*") and not conteudo.startswith("* ") and not conteudo.endswith("*"):
            conteudo = "* " + conteudo[1:].lstrip()

        linhas_limpas.append(conteudo)

    return "\n".join(linhas_limpas).strip()

def gerar_resumo_coordenacao_com_ia(t_senai, t_uefs, t_unef, t_unifacs, t_fat, t_fan, t_ftc, data_formatada):
    """Envia os textos dos 7 grupos para a IA e retorna o quantitativo máximo de cada rota."""
    prompt = f"""
    Você é um assistente de logística de transporte universitário.
    Sua tarefa é ler 7 listas brutas de passageiros enviadas no WhatsApp e extrair a contagem para o turno NOTURNO.

    REGRA ABSOLUTA: Retorne APENAS o modelo preenchido abaixo. NUNCA adicione saudações, desculpas ou explicações. Se os dados estiverem vazios, preencha com 0. Mantenha os asteriscos exatamente onde estão.
    REGRA DE FORMATAÇÃO: Nos itens da lista, use somente um marcador por linha no formato "* texto". NUNCA use "* *" e NUNCA envie linha contendo apenas "*".

    REGRAS DE CONTAGEM (MUITO IMPORTANTE):
    1. Só conte um passageiro se houver um nome escrito. Ignore linhas em branco ou números isolados.
    2. INCLUSÃO DE INSTITUIÇÕES: Muitas listas possuem uma seção "Demais instituições", "Outras instituições" ou nomes de outras faculdades no final. Os nomes nessas seções DEVEM ser obrigatoriamente somados ao total da lista.
    3. LÓGICA DE MAIOR VALOR (Ida vs Volta): Se a lista estiver dividida entre "Ida" e "Volta", você deve contar quantos vão na Ida (incluindo demais instituições da ida) e quantos vão na Volta (incluindo demais instituições da volta). O valor final para aquele grupo será o MAIOR NÚMERO entre a Ida e a Volta. NUNCA some a Ida com a Volta.
    4. Lógica de Lista Única: Se a lista não tiver divisão de Ida e Volta, apenas conte o total de nomes válidos (incluindo demais instituições).

    DADOS BRUTOS (7 GRUPOS):
    1. SENAI:
    {t_senai}

    2. UEFS:
    {t_uefs}

    3. UNEF/IFBA:
    {t_unef}

    4. UNIFACS:
    {t_unifacs}

    5. FAT:
    {t_fat}

    6. FAN:
    {t_fan}

    7. FTC:
    {t_ftc}

    MODELO DE SAÍDA EXIGIDO:
    *Quantitativo Da Noite - {data_formatada} :*

    * SENAI - [quantidade]
    * ⁠UEFS - [quantidade]
    * UNEF - [quantidade]
    * UNIFACS - [quantidade]
    * FAT - [quantidade]
    * FAN - [quantidade]
    * FTC - [quantidade]
    """
    
    return gerar_texto_ia_com_fallback(
        client=client,
        prompt=prompt,
        normalizar_func=normalizar_resumo_ia,
        logger=logging,
        contexto="[NOTURNO] ",
    )

# --- FUNÇÕES DE NAVEGAÇÃO WHATSAPP ---

def clicar_grupo(nome_grupo):
    """Lógica de busca com XPath atualizado para a nova versão do WhatsApp Web."""
    try:
        logging.info(f"🔍 Buscando grupo: {nome_grupo}")
        xpath_busca = "//input[@data-tab='3'] | //input[contains(@placeholder, 'Pesquisar')] | //div[@contenteditable='true' and @data-tab='3']"
        
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, xpath_busca))
        )
        search_box.click()
        search_box.send_keys(Keys.CONTROL + "a")
        search_box.send_keys(Keys.BACK_SPACE)
        time.sleep(0.5)
        search_box.send_keys(nome_grupo)
        time.sleep(2)
        
        xpath_result = f"//div[@role='row']//span[@title='{nome_grupo}']"
        grupo = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, xpath_result)))
        grupo.click()
        logging.info(f"✅ Entrou no grupo: {nome_grupo}")
        time.sleep(1)
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
            time.sleep(1.5)
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
        logging.info("✉️ Relatório de quantitativos noturnos enviado com sucesso.")
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
logging.info("=== INICIANDO FECHAMENTO NOTURNO ===")
driver.get("https://web.whatsapp.com")

try:
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//div[@role='grid']")))
    logging.info("✅ WhatsApp Web carregado com sucesso.")
    time.sleep(10)

    # 1. PASSA NOS 7 GRUPOS, EXTRAI A LISTA E DEPOIS FECHA
    for grupo in GRUPOS_ALVO:
        logging.info(f"--- Processando: {grupo} ---")
        if clicar_grupo(grupo):
            try:
                texto_extraido = extrair_texto_lista()
                textos_coletados[grupo] = texto_extraido
                logging.info(f"📄 Lista capturada: {len(texto_extraido)} caracteres.")

                header_xpath = '//*[@id="main"]/header'
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, header_xpath))).click()
                time.sleep(2)
                
                xpath_perm = "//span[text()='Permissões do grupo']"
                btn_perm = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_perm)))
                driver.execute_script("arguments[0].scrollIntoView(true);", btn_perm)
                time.sleep(1)
                btn_perm.click()

                if tentar_fechar_grupo(grupo):
                    logging.info(f"📣 Enviando aviso de fechamento para {grupo}.")
                else:
                    logging.info(f"📣 Grupo {grupo} já estava fechado; enviando aviso mesmo assim.")

                voltar_fechar_paineis()
                enviar_msg_chat_simples(MENSAGEM_FECHAMENTO)
                    
            except Exception as e:
                logging.error(f"❌ Erro fatal no fluxo do grupo {grupo}: {e}")
                voltar_fechar_paineis()

    # 2. IA PROCESSA OS DADOS COLETADOS
    logging.info("A gerar relatório unificado com IA...")
    data_amanha = (datetime.now() + timedelta(days=1)).strftime("%d/%m")

    try:
        logging.info(
            "🧠 Iniciando IA com textos: SENAI=%s, UEFS=%s, UNEF=%s, UNIFACS=%s, FAT=%s, FAN=%s, FTC=%s",
            len(textos_coletados.get(GRUPOS_ALVO[0], "")),
            len(textos_coletados.get(GRUPOS_ALVO[1], "")),
            len(textos_coletados.get(GRUPOS_ALVO[2], "")),
            len(textos_coletados.get(GRUPOS_ALVO[3], "")),
            len(textos_coletados.get(GRUPOS_ALVO[4], "")),
            len(textos_coletados.get(GRUPOS_ALVO[5], "")),
            len(textos_coletados.get(GRUPOS_ALVO[6], "")),
        )
        # Passa as variáveis garantindo a ordem definida na lista GRUPOS_ALVO
        resumo_ia = gerar_resumo_coordenacao_com_ia(
            t_senai=textos_coletados.get(GRUPOS_ALVO[0], ""),
            t_uefs=textos_coletados.get(GRUPOS_ALVO[1], ""),
            t_unef=textos_coletados.get(GRUPOS_ALVO[2], ""),
            t_unifacs=textos_coletados.get(GRUPOS_ALVO[3], ""),
            t_fat=textos_coletados.get(GRUPOS_ALVO[4], ""),
            t_fan=textos_coletados.get(GRUPOS_ALVO[5], ""),
            t_ftc=textos_coletados.get(GRUPOS_ALVO[6], ""),
            data_formatada=data_amanha
        )
        logging.info("✅ IA concluída. Tamanho do resumo: %s caracteres.", len(resumo_ia))
    except Exception as e:
        logging.error(f"Falha inesperada na etapa da IA: {e}")
        resumo_ia = f"Erro ao gerar resumo da IA: {e}"

    # 3. ENVIA PARA A COORDENAÇÃO IMEDIATAMENTE
    if clicar_grupo(GRUPO_COORDENACAO):
        logging.info("A enviar quantitativos para a coordenação...")
        enviar_msg_chat_multilinha(resumo_ia)
        
    time.sleep(5) 

finally:
    logging.info("🏁 Processo de fechamento noturno finalizado.")
    driver.quit()