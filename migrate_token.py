#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: migrate_token.py
🔧 FUNÇÃO: Migrar token válido para local correto
⚠️ IMPORTANTE: Script único, deletar após uso
"""

import os
import json
import shutil

def migrar_token():
    """
    Migra token válido de data/ para locais corretos
    """
    print("🔧 CCB Alerta Bot - Migração de Token")
    print("=" * 50)
    
    # Arquivos de origem e destino
    token_origem = "/opt/render/project/src/data/token.json"
    
    # Locais de destino
    destino_hardcoded = "/opt/render/project/storage/token.json"  # Onde o sistema procura
    destino_persistente = "/opt/render/project/disk/shared_data/token.json"  # Backup persistente
    
    # Verificar se token origem existe
    if not os.path.exists(token_origem):
        print(f"❌ Token origem não encontrado: {token_origem}")
        return False
    
    print(f"✅ Token origem encontrado: {token_origem}")
    
    try:
        # Ler e validar token
        with open(token_origem, 'r') as f:
            token_data = json.load(f)
        
        if 'access_token' not in token_data or 'refresh_token' not in token_data:
            print("❌ Token inválido - faltam campos necessários")
            return False
        
        print("✅ Token validado - campos obrigatórios presentes")
        
        # Criar diretórios necessários
        os.makedirs(os.path.dirname(destino_hardcoded), exist_ok=True)
        os.makedirs(os.path.dirname(destino_persistente), exist_ok=True)
        
        print("✅ Diretórios criados")
        
        # Copiar para local hardcoded (onde sistema procura)
        shutil.copy2(token_origem, destino_hardcoded)
        os.chmod(destino_hardcoded, 0o600)  # Permissões seguras
        print(f"✅ Token copiado para: {destino_hardcoded}")
        
        # Copiar para disco persistente (backup)
        shutil.copy2(token_origem, destino_persistente)
        os.chmod(destino_persistente, 0o600)  # Permissões seguras
        print(f"✅ Backup salvo em: {destino_persistente}")
        
        # Tentar usar MicrosoftAuth para salvar com criptografia
        print("🔒 Tentando salvar com criptografia...")
        try:
            from auth.microsoft_auth import MicrosoftAuth
            
            auth = MicrosoftAuth()
            auth.access_token = token_data['access_token']
            auth.refresh_token = token_data['refresh_token']
            
            if auth.salvar_token_persistent():
                print("✅ Token salvo com criptografia!")
            else:
                print("⚠️ Criptografia falhou, mas arquivo JSON está disponível")
                
        except Exception as e:
            print(f"⚠️ Erro na criptografia: {e}")
            print("   Arquivo JSON disponível como fallback")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        return False

def testar_carregamento():
    """
    Testa se o token pode ser carregado
    """
    print("\n🧪 Testando carregamento...")
    
    try:
        from auth.microsoft_auth import MicrosoftAuth
        
        auth = MicrosoftAuth()
        
        if auth.carregar_token():
            print("✅ Token carregado com sucesso!")
            print(f"   Access token: {'✅ Presente' if auth.access_token else '❌ Ausente'}")
            print(f"   Refresh token: {'✅ Presente' if auth.refresh_token else '❌ Ausente'}")
            
            # Testar validação
            print("🔍 Testando validação com Microsoft Graph...")
            if auth.validar_token():
                print("✅ Token VÁLIDO e funcional!")
                return True
            else:
                print("⚠️ Token carregado mas pode estar expirado")
                print("   Sistema tentará renovar automaticamente")
                return True
        else:
            print("❌ Falha no carregamento")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def verificar_arquivos():
    """
    Verifica quais arquivos de token existem
    """
    print("\n📁 Verificando arquivos de token...")
    
    arquivos = [
        "/opt/render/project/src/data/token.json",
        "/opt/render/project/storage/token.json",
        "/opt/render/project/storage/token.enc",
        "/opt/render/project/disk/shared_data/token.json",
        "/opt/render/project/disk/shared_data/token.enc"
    ]
    
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            size = os.path.getsize(arquivo)
            print(f"✅ {arquivo} ({size} bytes)")
        else:
            print(f"❌ {arquivo}")

def main():
    """
    Função principal
    """
    print("🚀 Iniciando migração de token...")
    
    # Verificar estado atual
    verificar_arquivos()
    
    # Migrar token
    if migrar_token():
        print("\n🎉 MIGRAÇÃO CONCLUÍDA!")
        print("=" * 50)
        
        # Testar carregamento
        if testar_carregamento():
            print("\n✅ SUCESSO TOTAL!")
            print("🔄 Reinicie o bot para aplicar mudanças")
            print("⚠️ Delete este script: rm migrate_token.py")
        else:
            print("\n⚠️ MIGRAÇÃO OK, MAS TESTE FALHOU")
            print("   Token foi copiado, mas pode precisar de correções")
    else:
        print("\n❌ MIGRAÇÃO FALHOU!")
        print("=" * 50)
    
    # Mostrar estado final
    print("\n📁 Estado final dos arquivos:")
    verificar_arquivos()

if __name__ == "__main__":
    main()
