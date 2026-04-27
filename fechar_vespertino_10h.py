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

# ====== CONFIGURAÇÃO DE LOGS ======
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

# ====== CONFIGURAÇÕES DO FLUXO (VESPERTINO PRODUÇÃO) ======
GRUPOS_ALVO = [
    "Transporte UEFS-UFRB 2026",
    "Transporte FTC INTEGRAL 2026",
    "Transporte Vespertino 2026"
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
            if len(texto) > 100 and ("IDA" in texto_maiusculo or "VOLTA" in texto_maiusculo or "RETORNO" in texto_maiusculo):
                return texto
                
        return "NENHUMA LISTA IDENTIFICADA"
    except Exception as e:
        print(f"⚠️ Erro ao extrair: {e}")
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

def gerar_resumo_coordenacao_com_ia(texto_uefs_ufrb, texto_ftc, texto_centro, data_formatada):
    """Envia os textos do Vespertino para a IA e retorna apenas o quantitativo no molde exato."""
    prompt = f"""
    Você é um assistente de logística de transporte universitário.
    Sua tarefa é ler as 3 listas brutas de passageiros enviadas no WhatsApp e extrair a contagem exata.

    REGRA ABSOLUTA: Retorne APENAS o modelo preenchido abaixo. NUNCA adicione saudações, desculpas ou explicações. Mantenha os asteriscos (*) exatamente onde estão, pois servem para negrito no WhatsApp. Se os dados estiverem vazios, preencha com 0.
    REGRA DE FORMATAÇÃO: Nos itens da lista, use somente um marcador por linha no formato "* texto". NUNCA use "* *" e NUNCA envie linha contendo apenas "*".

    REGRAS DE CONTAGEM:
    - Só conte um passageiro se houver um nome escrito.
    - Ignore linhas em branco ou números isolados.
    - Nos grupos UEFS/UFRB e FTC, foque EXCLUSIVAMENTE na seção VESPERTINO (Ida 12:30/13h e Retorno 18h). IGNORE COMPLETAMENTE a seção Matutino (06h/12h).
    - No grupo Vespertino (que representa o trajeto Centro), conte a Ida e a Volta normalmente.

    DADOS BRUTOS:
    1. UEFS/UFRB:
    {texto_uefs_ufrb}

    2. FTC:
    {texto_ftc}

    3. CENTRO (Grupo Vespertino):
    {texto_centro}

    MODELO DE SAÍDA EXIGIDO:
    *Quantitativos Tarde {data_formatada}:*

    *UEFS e UFRB:*
    * IDA às 13h: [quantidade]
    * VOLTA às 18h: [quantidade]
    *FTC:*
    * IDA às 13h: [quantidade]
    * VOLTA às 18h: [quantidade]
    *CENTRO*
    * IDA às 13h: [quantidade]
    * VOLTA às 18h: [quantidade]
    """
    
    # ====== SISTEMA DE RETRY PARA A IA (Evita o erro 503) ======
    tentativas = 3
    for tentativa in range(tentativas):
        try:
            logging.info(f"🧠 IA analisando os dados da tarde... (Tentativa {tentativa + 1}/{tentativas})")
            resposta = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return normalizar_resumo_ia(resposta.text)
        except Exception as e:
            erro_msg = str(e)
            logging.error(f"Falha na API da IA: {erro_msg}")
            
            if "503" in erro_msg or "UNAVAILABLE" in erro_msg or "429" in erro_msg:
                if tentativa < tentativas - 1:
                    espera = (tentativa + 1) * 10
                    logging.info(f"⏳ Servidor do Google sobrecarregado. Aguardando {espera}s para tentar de novo...")
                    time.sleep(espera)
                else:
                    logging.critical("❌ Todas as tentativas da IA falharam.")
                    return f"Erro na IA após {tentativas} tentativas: {erro_msg}"
            else:
                return f"Erro na IA: {erro_msg}"

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
        time.sleep(0.5)
        
        # Digita o nome do grupo
        search_box.send_keys(nome_grupo)
        time.sleep(2)
        
        # Seleciona o grupo na lista
        xpath_result = f"//div[@role='row']//span[@title='{nome_grupo}']"
        grupo = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, xpath_result)))
        grupo.click()
        
        logging.info(f"✅ Grupo aberto: {nome_grupo}")
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
        caixa = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"))
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
                texto_extraido = extrair_texto_lista()
                textos_coletados[grupo] = texto_extraido
                logging.info(f"📄 Lista capturada: {len(texto_extraido)} caracteres.")

                header_xpath = '//*[@id="main"]/header'
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, header_xpath))).click()
                time.sleep(2)
                
                xpath_perm = "//span[text()='Permissões do grupo']"
                btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_perm)))
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(1)
                btn.click()
                
                if tentar_fechar_grupo(grupo):
                    grupos_fechados += 1
                    voltar_fechar_paineis()
                    enviar_msg_chat_simples(MENSAGEM_FECHAMENTO)
                else:
                    voltar_fechar_paineis()
                    
            except Exception as e:
                logging.error(f"❌ Erro fatal no fluxo do grupo {grupo}: {e}")
                grupos_falhados.append(grupo)
                voltar_fechar_paineis()
        else:
            grupos_falhados.append(grupo)

    logging.info(f"📊 Resumo: {grupos_fechados}/{len(GRUPOS_ALVO)} grupos processados. Falhados: {grupos_falhados}")
    
    logging.info("A gerar relatório unificado com IA...")
    data_amanha = (datetime.now() + timedelta(days=1)).strftime("%d/%m")
    
    resumo_ia = gerar_resumo_coordenacao_com_ia(
        texto_uefs_ufrb=textos_coletados.get(GRUPOS_ALVO[0], ""),
        texto_ftc=textos_coletados.get(GRUPOS_ALVO[1], ""),
        texto_centro=textos_coletados.get(GRUPOS_ALVO[2], ""),
        data_formatada=data_amanha
    )

    if clicar_grupo(GRUPO_COORDENACAO):
        logging.info("A enviar quantitativos para a coordenação...")
        enviar_msg_chat_multilinha(resumo_ia)
        
    time.sleep(5) 

finally:
    logging.info("🏁 Processo de fechamento vespertino finalizado.")
    driver.quit()