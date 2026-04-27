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

# ====== CONFIGURAÇÕES DO FLUXO ======
GRUPOS_ALVO = [
    "Transporte UEFS-UFRB 2026",
    "Transporte FTC INTEGRAL 2026",
    "Transporte IFBA-UNEF Matutino 2026",
    "Transporte Matutino (Centro) 2026"
]
GRUPO_COORDENACAO = "Coordenação Transporte Universitário"
MENSAGEM_FECHAMENTO = "❌✖️❌✖️Lista Fechada ❌✖️❌✖️"

textos_coletados = {}

# --- FUNÇÕES DA IA E EXTRAÇÃO ---

def extrair_texto_lista():
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
            if len(texto) > 100 and ("IDA" in texto_maiusculo or "VOLTA" in texto_maiusculo or "RETORNO" in texto_maiusculo):
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

def gerar_resumo_coordenacao_com_ia(texto_uefs_ufrb, texto_ftc, texto_unef, texto_centro, data_formatada):
    prompt = f"""
    Você é um assistente de logística de transporte universitário.
    Sua tarefa é ler as 4 listas brutas de passageiros enviadas no WhatsApp e extrair a contagem.

    REGRA ABSOLUTA: Retorne APENAS o modelo preenchido abaixo. NUNCA adicione saudações, desculpas, comentários ou explicações. Se os dados de um grupo estiverem vazios ou ausentes, preencha com 0.
    REGRA DE FORMATAÇÃO: Nos itens da lista, use somente um marcador por linha no formato "* texto". NUNCA use "* *" e NUNCA envie linha contendo apenas "*".

    REGRAS DE CONTAGEM:
    - Só conte um passageiro se houver um nome escrito.
    - Ignore linhas vazias ou números soltos.
    - Nos grupos UEFS/UFRB e FTC, foque apenas na parte do MATUTINO (Ida 06h e Retorno 12h).

    DADOS BRUTOS:
    1. UEFS/UFRB:
    {texto_uefs_ufrb}

    2. FTC:
    {texto_ftc}

    3. IFBA-UNEF:
    {texto_unef}

    4. CENTRO:
    {texto_centro}

    MODELO DE SAÍDA EXIGIDO:
    Quantitativos Manhã {data_formatada}:

    UEFS e UFRB:
    * Ida 6h: [quantidade]
    * Volta 12h: [quantidade]
    FTC:
    * Ida 6h: [quantidade]
    * Volta 12h: [quantidade]
    UNEF e IFBA:
    * Ida 6h: [quantidade]
    * Volta 12h: [quantidade]
    CENTRO:
    * Ida 6h: [quantidade]
    * Volta 12h: [quantidade]
    """
    
    # ====== SISTEMA DE RETRY PARA A IA (Evita o erro 503) ======
    tentativas = 3
    for tentativa in range(tentativas):
        try:
            logging.info(f"🧠 Enviando para a IA do Google... (Tentativa {tentativa + 1}/{tentativas})")
            resposta = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return normalizar_resumo_ia(resposta.text)
        except Exception as e:
            erro_msg = str(e)
            logging.error(f"Falha na API da IA: {erro_msg}")
            
            # Se for erro de servidor indisponível ou limite de taxa, ele espera e tenta de novo
            if "503" in erro_msg or "UNAVAILABLE" in erro_msg or "429" in erro_msg:
                if tentativa < tentativas - 1:
                    espera = (tentativa + 1) * 10 # Espera 10s, depois 20s...
                    logging.info(f"⏳ Servidor do Google sobrecarregado. Aguardando {espera}s para tentar de novo...")
                    time.sleep(espera)
                else:
                    logging.critical("❌ Todas as tentativas da IA falharam.")
                    return f"Erro na IA após {tentativas} tentativas: {erro_msg}"
            else:
                return f"Erro na IA: {erro_msg}"

# --- FUNÇÕES DE NAVEGAÇÃO WHATSAPP ---

def clicar_grupo(nome_grupo):
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
        # Aumentei o tempo de espera aqui para garantir que o menu carregou
        xpath_switch = "//div[contains(@aria-label, 'mensagens')]//input[@type='checkbox'] | //input[@role='switch' and contains(@aria-label, 'mensagens')]"
        switch = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath_switch)))
        
        if switch.get_attribute("aria-checked") == "true": 
            driver.execute_script("arguments[0].click();", switch)
            logging.info(f"🔒 Status alterado: Grupo FECHADO ({nome_grupo}).")
            time.sleep(1.5) # Aguarda confirmação do clique
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
        caixa = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"))
        )
        caixa.click()
        for linha in texto.split('\n'):
            linha_segura = linha.encode('utf-16', 'surrogatepass').decode('utf-16')
            caixa.send_keys(linha_segura)
            caixa.send_keys(Keys.SHIFT, Keys.ENTER)
        caixa.send_keys(Keys.ENTER)
        logging.info("✉️ Relatório de quantitativos enviado com sucesso.")
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
logging.info("=== INICIANDO FECHAMENTO MATUTINO ===")
driver.get("https://web.whatsapp.com")

try:
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//div[@role='grid']")))
    logging.info("✅ WhatsApp Web carregado com sucesso.")
    time.sleep(10)

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
                    voltar_fechar_paineis()
                    enviar_msg_chat_simples(MENSAGEM_FECHAMENTO)
                else:
                    voltar_fechar_paineis()
                    
            except Exception as e:
                logging.error(f"❌ Erro fatal no fluxo do grupo {grupo}: {e}")
                voltar_fechar_paineis()

    logging.info("A gerar relatório unificado com IA...")
    data_amanha = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    
    resumo_ia = gerar_resumo_coordenacao_com_ia(
        texto_uefs_ufrb=textos_coletados.get(GRUPOS_ALVO[0], ""),
        texto_ftc=textos_coletados.get(GRUPOS_ALVO[1], ""),
        texto_unef=textos_coletados.get(GRUPOS_ALVO[2], ""),
        texto_centro=textos_coletados.get(GRUPOS_ALVO[3], ""),
        data_formatada=data_amanha
    )

    if clicar_grupo(GRUPO_COORDENACAO):
        logging.info("A enviar quantitativos para a coordenação...")
        enviar_msg_chat_multilinha(resumo_ia)
        
    time.sleep(5) 

finally:
    logging.info("🏁 Processo de fechamento matutino finalizado.")
    driver.quit()