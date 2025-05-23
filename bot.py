"""
Arquivo principal corrigido para o Bot de Alertas de Água via Telegram
Implementa limpeza de webhook e polling robusto para evitar conflitos
"""
import logging
import os
import asyncio
import signal
import sys
from datetime import datetime
from telegram.ext import Application
from telegram.error import Conflict, NetworkError, TimedOut

from config import (
    TOKEN, inicializar_sistema, logger, BOT_NAME, 
    POLLING_CONFIG, obter_info_sistema
)
from handlers.commands import registrar_comandos_basicos
from handlers.cadastro import registrar_handlers_cadastro
from handlers.admin import registrar_handlers_admin
from handlers.mensagens import registrar_handlers_mensagens
from handlers.alerta import registrar_handlers_alerta
from handlers.error import registrar_error_handler

# Variável global para controle do bot
bot_application = None
bot_running = False

async def limpar_webhook_se_necessario(application):
    """
    Remove webhook ativo para evitar conflitos com polling
    
    Args:
        application: Instância da aplicação do bot
        
    Returns:
        bool: True se limpeza foi bem-sucedida, False caso contrário
    """
    try:
        logger.info("Verificando e removendo webhook se necessário...")
        
        # Obter informações do webhook atual
        webhook_info = await application.bot.get_webhook_info()
        
        if webhook_info.url:
            logger.warning(f"Webhook ativo encontrado: {webhook_info.url}")
            logger.info("Removendo webhook para usar polling...")
            
            # Remover webhook
            success = await application.bot.delete_webhook(drop_pending_updates=True)
            
            if success:
                logger.info("✅ Webhook removido com sucesso")
                # Aguardar um pouco para a mudança ter efeito
                await asyncio.sleep(2)
                return True
            else:
                logger.error("❌ Falha ao remover webhook")
                return False
        else:
            logger.info("✅ Nenhum webhook ativo - pronto para polling")
            return True
            
    except Exception as e:
        logger.error(f"Erro ao verificar/remover webhook: {e}")
        return False

async def iniciar_polling_robusto(application):
    """
    Inicia polling com tratamento robusto de erros e retry automático
    
    Args:
        application: Instância da aplicação do bot
    """
    max_tentativas = 5
    tentativa = 0
    
    while tentativa < max_tentativas and bot_running:
        try:
            tentativa += 1
            logger.info(f"Tentativa {tentativa}/{max_tentativas} - Iniciando polling...")
            
            # Limpar webhook antes de cada tentativa
            webhook_limpo = await limpar_webhook_se_necessario(application)
            if not webhook_limpo:
                logger.warning("Falha ao limpar webhook, tentando continuar...")
            
            # Iniciar polling com configurações robustas
            await application.run_polling(
                timeout=POLLING_CONFIG["timeout"],
                poll_interval=POLLING_CONFIG["poll_interval"],
                drop_pending_updates=POLLING_CONFIG["drop_pending_updates"],
                allowed_updates=POLLING_CONFIG["allowed_updates"],
                read_timeout=POLLING_CONFIG["read_timeout"],
                write_timeout=POLLING_CONFIG["write_timeout"],
                connect_timeout=POLLING_CONFIG["connect_timeout"],
                close_loop=False
            )
            
            # Se chegou aqui, o polling foi interrompido normalmente
            logger.info("Polling interrompido normalmente")
            break
            
        except Conflict as e:
            logger.error(f"❌ Conflito detectado (tentativa {tentativa}): {e}")
            
            if "webhook" in str(e).lower():
                logger.info("Tentando resolver conflito de webhook...")
                try:
                    # Força remoção do webhook
                    await application.bot.delete_webhook(drop_pending_updates=True)
                    await asyncio.sleep(5)  # Aguarda mais tempo
                except Exception as webhook_error:
                    logger.error(f"Erro ao forçar remoção do webhook: {webhook_error}")
            
            if tentativa < max_tentativas:
                delay = min(30, 5 * tentativa)  # Delay progressivo, máximo 30s
                logger.info(f"Aguardando {delay}s antes da próxima tentativa...")
                await asyncio.sleep(delay)
            else:
                logger.error("❌ Máximo de tentativas atingido para resolver conflito")
                raise
        
        except (NetworkError, TimedOut) as e:
            logger.warning(f"Erro de rede (tentativa {tentativa}): {e}")
            if tentativa < max_tentativas:
                delay = min(15, 3 * tentativa)
                logger.info(f"Aguardando {delay}s antes da próxima tentativa...")
                await asyncio.sleep(delay)
            else:
                logger.error("❌ Máximo de tentativas atingido para erros de rede")
                raise
        
        except Exception as e:
            logger.error(f"Erro inesperado no polling (tentativa {tentativa}): {e}")
            if tentativa < max_tentativas:
                delay = min(20, 4 * tentativa)
                logger.info(f"Aguardando {delay}s antes da próxima tentativa...")
                await asyncio.sleep(delay)
            else:
                logger.error("❌ Máximo de tentativas atingido")
                raise

def configurar_signal_handlers():
    """
    Configura handlers para sinais do sistema (SIGTERM, SIGINT)
    """
    def signal_handler(signum, frame):
        global bot_running
        logger.info(f"Sinal {signum} recebido - iniciando shutdown graceful...")
        bot_running = False
        
        if bot_application:
            try:
                # Para o bot de forma assíncrona
                asyncio.create_task(bot_application.stop())
            except Exception as e:
                logger.error(f"Erro ao parar o bot: {e}")
        
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

async def main():
    """Função principal assíncrona para iniciar o bot"""
    global bot_application, bot_running
    
    try:
        logger.info(f"🚀 Iniciando {BOT_NAME}...")
        
        # Inicializar sistema
        inicializar_sistema()
        
        # Log de informações do sistema
        info_sistema = obter_info_sistema()
        logger.info(f"Informações do sistema: {info_sistema}")
        
        # Configurar handlers de sinal
        configurar_signal_handlers()
        
        # Criar a aplicação
        logger.info("Criando aplicação do bot...")
        bot_application = Application.builder().token(TOKEN).build()
        
        # Registrar handlers
        logger.info("Registrando handlers...")
        registrar_comandos_basicos(bot_application)
        registrar_handlers_cadastro(bot_application)
        registrar_handlers_admin(bot_application)
        registrar_handlers_mensagens(bot_application)
        registrar_handlers_alerta(bot_application)
        registrar_error_handler(bot_application)
        
        # Marcar como rodando
        bot_running = True
        
        # Inicializar a aplicação
        logger.info("Inicializando aplicação...")
        await bot_application.initialize()
        
        # Testar conexão com o bot
        logger.info("Testando conexão com Telegram...")
        me = await bot_application.bot.get_me()
        logger.info(f"✅ Bot conectado: @{me.username} ({me.first_name})")
        
        # Iniciar polling robusto
        logger.info("=" * 50)
        logger.info(f"🤖 {BOT_NAME} INICIADO COM SUCESSO!")
        logger.info("Pressione Ctrl+C para parar o bot")
        logger.info("=" * 50)
        
        # Iniciar polling com retry automático
        await iniciar_polling_robusto(bot_application)
        
    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO ao iniciar o bot: {e}")
        raise
    finally:
        # Cleanup
        bot_running = False
        if bot_application:
            try:
                logger.info("Finalizando aplicação...")
                await bot_application.shutdown()
            except Exception as e:
                logger.error(f"Erro no shutdown: {e}")
        
        logger.info(f"🔴 {BOT_NAME} finalizado")

def run_bot():
    """
    Função síncrona para executar o bot
    Lida com o loop de eventos asyncio
    """
    try:
        # Configurar política de loop de eventos para Windows (se necessário)
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Executar função principal
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal na execução: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_bot()
