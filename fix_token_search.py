#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: fix_token_search.py
💾 ONDE SALVAR: ccb-alerta-bot/fix_token_search.py (TEMPORÁRIO)
🔧 FUNÇÃO: Corrigir busca automática do token .enc
⚠️ IMPORTANTE: DELETAR após uso
"""

import os
import re

def corrigir_busca_token():
    """
    Corrige a função carregar_token() para encontrar arquivo .enc
    """
    print("🔧 Corrigindo busca automática do token...")
    
    arquivo_auth = "auth/microsoft_auth.py"
    
    if not os.path.exists(arquivo_auth):
        print(f"❌ Arquivo não encontrado: {arquivo_auth}")
        return False
    
    try:
        # Ler arquivo atual
        with open(arquivo_auth, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        print("🔍 Arquivo carregado para correção...")
        
        # Procurar pela função carregar_token
        if 'def carregar_token(self)' not in conteudo:
            print("❌ Função carregar_token não encontrada")
            return False
        
        # Substituição 1: Corrigir ordem de verificação de arquivos
        padrao_verificacao = r'if os\.path\.exists\(self\.token_file_persistent\):'
        
        if re.search(padrao_verificacao, conteudo):
            print("✅ Padrão de verificação encontrado")
            
            # Substituir a lógica de verificação
            conteudo_novo = re.sub(
                r'if os\.path\.exists\(self\.token_file_persistent\):\s*\n\s*logger\.info\(f"🔍 DEBUG: Arquivo persistent encontrado: \{self\.token_file_persistent\}"\)\s*\n\s*return self\._carregar_do_arquivo\(self\.token_file_persistent\)',
                '''# Verificar arquivo criptografado primeiro
        encrypted_file = self.token_file_persistent.replace('.json', '.enc')
        if os.path.exists(encrypted_file):
            logger.info(f"🔍 DEBUG: Arquivo criptografado encontrado: {encrypted_file}")
            return self._carregar_do_arquivo(encrypted_file)
        elif os.path.exists(self.token_file_persistent):
            logger.info(f"🔍 DEBUG: Arquivo persistent encontrado: {self.token_file_persistent}")
            return self._carregar_do_arquivo(self.token_file_persistent)''',
                conteudo,
                flags=re.MULTILINE | re.DOTALL
            )
            
            if conteudo_novo != conteudo:
                print("✅ Correção aplicada na verificação persistent")
                conteudo = conteudo_novo
            else:
                print("⚠️ Não conseguiu aplicar correção na verificação persistent")
        
        # Substituição 2: Corrigir também a verificação local
        padrao_local = r'elif os\.path\.exists\(self\.token_file_local\):'
        
        if re.search(padrao_local, conteudo):
            conteudo_novo = re.sub(
                r'elif os\.path\.exists\(self\.token_file_local\):\s*\n\s*logger\.info\(f"🔍 DEBUG: Arquivo local encontrado: \{self\.token_file_local\}"\)\s*\n\s*return self\._carregar_do_arquivo\(self\.token_file_local\)',
                '''elif os.path.exists(self.token_file_local.replace('.json', '.enc')):
            encrypted_local = self.token_file_local.replace('.json', '.enc')
            logger.info(f"🔍 DEBUG: Arquivo local criptografado encontrado: {encrypted_local}")
            return self._carregar_do_arquivo(encrypted_local)
        elif os.path.exists(self.token_file_local):
            logger.info(f"🔍 DEBUG: Arquivo local encontrado: {self.token_file_local}")
            return self._carregar_do_arquivo(self.token_file_local)''',
                conteudo,
                flags=re.MULTILINE | re.DOTALL
            )
            
            if conteudo_novo != conteudo:
                print("✅ Correção aplicada na verificação local")
                conteudo = conteudo_novo
            else:
                print("⚠️ Não conseguiu aplicar correção na verificação local")
        
        # Fazer backup do arquivo original
        backup_file = f"{arquivo_auth}.backup"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"📁 Backup criado: {backup_file}")
        
        # Salvar arquivo corrigido
        with open(arquivo_auth, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        print("✅ Arquivo corrigido salvo!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante correção: {e}")
        return False

def testar_correcao():
    """
    Testa se a correção funcionou
    """
    print("🧪 Testando correção...")
    
    try:
        from auth.microsoft_auth import MicrosoftAuth
        
        # Criar nova instância para testar
        auth = MicrosoftAuth()
        
        print("🔍 Testando carregamento automático...")
        resultado = auth.carregar_token()
        
        if resultado:
            print("✅ SUCESSO! Token carregado automaticamente")
            print(f"   Access token: {'✅ Presente' if auth.access_token else '❌ Ausente'}")
            print(f"   Refresh token: {'✅ Presente' if auth.refresh_token else '❌ Ausente'}")
            return True
        else:
            print("❌ Carregamento automático ainda falha")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """
    Função principal
    """
    print("🔧 CCB Alerta Bot - Correção de Busca Token")
    print("=" * 50)
    
    # Verificar se arquivo .enc existe
    token_enc = "/opt/render/project/storage/token.enc"
    if not os.path.exists(token_enc):
        print(f"❌ Arquivo token não encontrado: {token_enc}")
        print("   Execute primeiro o setup_token_v2.py")
        return
    
    print(f"✅ Token encontrado: {token_enc}")
    
    # Aplicar correção
    if corrigir_busca_token():
        print("\n🧪 Testando correção aplicada...")
        
        if testar_correcao():
            print("\n🎉 CORREÇÃO BEM-SUCEDIDA!")
            print("=" * 50)
            print("✅ Token agora é carregado automaticamente")
            print("✅ Sistema Microsoft Graph funcional")
            print("⚠️ IMPORTANTE: Delete este arquivo e reinicie o bot!")
            print("   rm fix_token_search.py")
            print("🔄 Faça novo deploy para aplicar mudanças")
        else:
            print("\n❌ CORREÇÃO FALHOU!")
            print("=" * 50)
            print("🔄 Tentando restaurar backup...")
            
            # Restaurar backup se teste falhou
            try:
                with open("auth/microsoft_auth.py.backup", 'r', encoding='utf-8') as f:
                    backup_content = f.read()
                with open("auth/microsoft_auth.py", 'w', encoding='utf-8') as f:
                    f.write(backup_content)
                print("✅ Backup restaurado")
            except:
                print("❌ Erro restaurando backup")
    else:
        print("\n❌ FALHA NA APLICAÇÃO DA CORREÇÃO!")
        print("=" * 50)

if __name__ == "__main__":
    main()
