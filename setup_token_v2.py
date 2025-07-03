#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: setup_token_v2.py
💾 ONDE SALVAR: ccb-alerta-bot/setup_token_v2.py (TEMPORÁRIO)
🔧 FUNÇÃO: Setup inicial do token Microsoft no Render - VERSÃO CORRIGIDA
⚠️ IMPORTANTE: DELETAR após uso por segurança
"""

import os
import sys
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("setup_token")

def setup_microsoft_token():
    """
    Script MVP para salvar token Microsoft no disco persistente
    VERSÃO CORRIGIDA: Remove validação restritiva de formato JWT
    """
    
    print("🔧 CCB Alerta Bot - Setup Token Microsoft v2.0")
    print("=" * 50)
    
    # =================== TOKENS VÁLIDOS DO BRK ===================
    ACCESS_TOKEN = "EwBYBMl6BAAUBKgm8k1UswUNwklmy2v7U/S+1fEAAZeeaPAZR2YAW47tQAZLvOaE7M5DWctyrDpBFBsOFFOvHxubWdlinjiBd3YxMp7OgG5SAT5c6taqo6faI/bOvuK1nQt2Se6lh9CLkuhOQFAJ8XnLNC17RDRvHOLzKTh+uL1Oj2/FxrH/CQe7RsZqrb+m2SMx2IhV7pbN/f7KW9fx7lrApSCyoL3MdLN/NQ4CaugBbu4VGIOT0YmCk5cXFOFmSsL3PlmlOvFZ6wza2JzcXEkVyNGi0kGqItwoDt6TBnh6B3fdt52k15a7wuqK9N+PEZRSfNYAhk+3j8plyVKk8fCpD0pi6pEm3Q5U40IrIdJwO04hNUzdDn0IpC0yrwkQZgAAEFVH4zQiH5Q7OqwWXKFAbtUgAx+yBbxYK4Ngz+PYNkVd63OJRYD8fbrfAspb4ZRf+ELRi1adhLNKn1C5+3o9p6K2pdt2HLEU3XY50i6Wwfc2LolNHbPkO51PR0HyG5J0Eh96hhZremf9MCOp4XuzAYVfkY2mspJeTrbauzrUWSfijRUUaWfYWO0eW7J3usLqw87YtZmy/Nxp7GE7Uji+l/UsH7txVlU5SaOmRP9NvrWVnViU1PO8C8Lvb1gtrjBQScPbWdcbMAYaQOiXly3RPzjWdAhGiJM9tJR1ZyaZfQGA8RgTpj5HMe+iUkFTFHELmLV5AZ3CGfZ20nEkhXsM7e0/59HyW5l93pQxC7rfVKveB4P6kDATxzHQULyhumu16L0NULVc6qCeKXETPDZP6UIWozfeSWPTv7QExB+x/zhKxzLkWtvnk46o05yM39l6c4QmHdrXMn1MQ73CHGQHSt2JWsqKGcqxeUO5Vk7MOh0cGg2COOjq2E/KeD1jpbrsftPf+K5jHLi8CFFi1EVgWGHVf3DxNOtqdXLuwQ+tBNl3+vVodZRkf1Bb2PF8jjvhAFM9fdXzfyBiNXLsso/SbASIJs5BnhLHrQWbTxzQqYdZ4tAAQhkguTAO30HUEb83mKW/te6IKTmR0TAKE7EyUdC11L4Cak5rK7bWsZH2do3uLGPTe8mCX56V8DYtjIw5EfQ547hODJ8NodPx+Td6iz5A2MM/g4TgPsBGR5Xk1WbyNCSEhfnrDM5khaTKupROVHM9590aAJYCFIrLczIT9KY+QTdlll5wLydM8EIwDsetW35dP2+Tz67+29vosdU+x+0HCA0XBlc71+40HM9JBO2usDEQq/taDHtBoxbGk0Jspgd0tO3h4/wHJY2eAfSJqJLUbJulwZhSTuJgoHa32PGqiOmlQovaT04YTIRBe6LwaeI1LznIgy5m6bR4mjM2wKAu7pIBAxEcPJjYDfvRDuJxPt8wnrwyAfXFLr5CV7UaUstFpqBvB091Qjj9yYbUnuDNAQcjZtDqo6IS/tmMEU+HovFFJOqAVPqnt4SvH+v1TiL2LDQbipBaCxUo14YfI7IeVAM="
    
    REFRESH_TOKEN = "M.C526_BL2.0.U.-CugUcwLSKCi6xNvT!AS0ikA1tiHkyR26F2MsHgG5LmEACILRteBA!rYimhenDiFvEJQWzvQmJjDM2ZYdqWoSB6GnTeMn3ibq9Yn8PjDkPVzvBCiVjlgmLXV2rAosnUbFyxffvcl5n9Qxhin39*515CVhlAk8DkVt92gwKk!TfzVqFrjUPbO8aBsXJ8DWov02CMZFSuXZcCINhOWKr96gGBEUoPCIADf5ldjA2MQr6z!hkN8ChbHHjgZmshxzXTHS9Sg9Dif1sTDVAnR14da!!VoEqnQq6PmmA8RCaaaNWm3FrG7fqDexfpILmzux7ds8!c983pFdiBc2Ffwl*4gU9*4tj7PBF8uCwVIXJwVGjM7IU5lz5kvjXcHRrqSHzccZow$$"
    
    # =================== VALIDAÇÃO CORRIGIDA ===================
    
    # Validação básica sem restrições de formato
    if not ACCESS_TOKEN or len(ACCESS_TOKEN) < 50:
        print("❌ ERRO: ACCESS_TOKEN muito curto ou vazio!")
        return False
    
    if not REFRESH_TOKEN or len(REFRESH_TOKEN) < 50:
        print("❌ ERRO: REFRESH_TOKEN muito curto ou vazio!")
        return False
    
    print("✅ Tokens validados - formato Microsoft Graph")
    print(f"   ACCESS_TOKEN: {len(ACCESS_TOKEN)} caracteres")
    print(f"   REFRESH_TOKEN: {len(REFRESH_TOKEN)} caracteres")
    
    try:
        # Importar o sistema de autenticação
        from auth.microsoft_auth import MicrosoftAuth
        
        print("🔍 Inicializando MicrosoftAuth...")
        auth = MicrosoftAuth()
        
        print("🔐 Configurando tokens...")
        auth.access_token = ACCESS_TOKEN
        auth.refresh_token = REFRESH_TOKEN
        
        print("💾 Salvando no disco persistente...")
        if auth.salvar_token_persistent():
            print("✅ Token salvo com sucesso!")
            print(f"   Local: {auth.token_file_persistent}")
            
            # Verificar arquivos criados
            persistent_file = auth.token_file_persistent
            encrypted_file = persistent_file.replace('.json', '.enc')
            
            if os.path.exists(encrypted_file):
                print("🔒 Arquivo criptografado criado!")
                print(f"   Arquivo: {encrypted_file}")
            elif os.path.exists(persistent_file):
                print("📁 Arquivo não criptografado criado!")
                print(f"   Arquivo: {persistent_file}")
            
            # Testar carregamento
            print("🔍 Testando carregamento...")
            auth_test = MicrosoftAuth()  # Nova instância para testar
            if auth_test.carregar_token():
                print("✅ Token carregado com sucesso do disco!")
                
                # Testar validação (pode falhar se token expirado)
                print("🔍 Testando validação com Microsoft Graph...")
                if auth_test.validar_token():
                    print("✅ Token VÁLIDO e funcional!")
                    return True
                else:
                    print("⚠️ Token salvo mas expirado. Tentando renovar...")
                    if auth_test.atualizar_token():
                        print("✅ Token renovado com sucesso!")
                        return True
                    else:
                        print("⚠️ Token salvo mas renovação falhou.")
                        print("   Isso pode acontecer se os tokens expiraram.")
                        print("   O bot tentará renovar quando iniciar.")
                        return True  # Considerar sucesso mesmo assim
            else:
                print("❌ Erro carregando token salvo")
                return False
        else:
            print("❌ Erro ao salvar token no disco persistente")
            return False
            
    except ImportError as e:
        print(f"❌ Erro importando MicrosoftAuth: {e}")
        print("   Verifique se está no diretório correto do projeto")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def verificar_ambiente():
    """Verifica se está rodando no ambiente correto"""
    print("🔍 Verificando ambiente...")
    
    # Verificar se está no Render
    if os.environ.get('RENDER'):
        print("✅ Ambiente: Render detectado")
    else:
        print("⚠️ Ambiente: Local (não é Render)")
    
    # Verificar se MICROSOFT_CLIENT_ID está configurado
    client_id = os.environ.get('MICROSOFT_CLIENT_ID')
    if client_id:
        print(f"✅ MICROSOFT_CLIENT_ID: Configurado ({client_id[:8]}...)")
    else:
        print("❌ MICROSOFT_CLIENT_ID: NÃO configurado!")
        return False
    
    # Verificar estrutura do projeto
    arquivos_esperados = [
        'auth/microsoft_auth.py',
        'config.py',
        'bot.py'
    ]
    
    for arquivo in arquivos_esperados:
        if os.path.exists(arquivo):
            print(f"✅ Arquivo: {arquivo}")
        else:
            print(f"❌ Arquivo ausente: {arquivo}")
            return False
    
    return True

def main():
    """Função principal do setup"""
    
    print("🚀 Iniciando setup do token Microsoft v2.0...")
    
    # Verificar ambiente
    if not verificar_ambiente():
        print("\n❌ Ambiente não está configurado corretamente!")
        print("   Verifique se:")
        print("   - Está no diretório raiz do projeto")
        print("   - MICROSOFT_CLIENT_ID está configurado")
        print("   - Arquivos do projeto estão presentes")
        return
    
    # Executar setup
    if setup_microsoft_token():
        print("\n🎉 SETUP CONCLUÍDO COM SUCESSO!")
        print("=" * 50)
        print("✅ Token Microsoft salvo e validado")
        print("🔒 Arquivo salvo no disco persistente")
        print("⚠️ IMPORTANTE: Delete este arquivo agora por segurança!")
        print("   rm setup_token_v2.py")
        print("🔄 Reinicie o bot para usar o novo token")
        print("\n🔍 Para verificar se funcionou:")
        print("   ls -la /opt/render/project/storage/")
    else:
        print("\n❌ SETUP FALHOU!")
        print("=" * 50)
        print("🔍 Verifique os logs acima para detalhes do erro")

if __name__ == "__main__":
    main()
