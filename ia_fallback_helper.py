import time


MODELOS_PADRAO = (
    "gemini-2.5-flash",
    "gemini-3.1-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-pro",
)


def gerar_texto_ia_com_fallback(client, prompt, normalizar_func, logger, contexto="", modelos=None, tentativas_por_modelo=2, espera_base=8, espera_max=45):
    """Tenta modelos em sequência com retry e backoff para erros temporários."""
    modelos = tuple(modelos or MODELOS_PADRAO)
    ultimo_erro = None

    for indice_modelo, modelo in enumerate(modelos):
        for tentativa in range(tentativas_por_modelo):
            try:
                logger.info(
                    f"{contexto}Enviando para a IA com {modelo}... "
                    f"(Tentativa {tentativa + 1}/{tentativas_por_modelo})"
                )
                resposta = client.models.generate_content(model=modelo, contents=prompt)
                texto = getattr(resposta, "text", "") or ""

                if not texto.strip():
                    raise RuntimeError(f"Resposta vazia recebida do modelo {modelo}.")

                return normalizar_func(texto)
            except Exception as exc:
                ultimo_erro = exc
                erro_msg = str(exc)
                erro_temporario = any(
                    marcador in erro_msg
                    for marcador in ("503", "UNAVAILABLE", "429")
                )

                logger.warning(
                    f"{contexto}Falha com {modelo} na tentativa {tentativa + 1}/{tentativas_por_modelo}: {erro_msg}"
                )

                if not erro_temporario:
                    return f"Erro na IA: {erro_msg}"

                if tentativa < tentativas_por_modelo - 1:
                    espera = min(espera_base * (2 ** tentativa), espera_max)
                    logger.info(
                        f"{contexto}Modelo {modelo} indisponível. Aguardando {espera}s antes da próxima tentativa..."
                    )
                    time.sleep(espera)
                    continue

                if indice_modelo < len(modelos) - 1:
                    proximo_modelo = modelos[indice_modelo + 1]
                    logger.info(
                        f"{contexto}Mudando automaticamente para o próximo modelo: {proximo_modelo}."
                    )

    erro_final = str(ultimo_erro) if ultimo_erro else "Erro desconhecido"
    logger.critical(
        f"{contexto}Todas as tentativas falharam em todos os modelos: {erro_final}"
    )
    return f"Erro na IA após tentar {', '.join(modelos)}: {erro_final}"