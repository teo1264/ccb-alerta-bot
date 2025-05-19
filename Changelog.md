# Changelog

Todas as mudanças significativas no projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.2.0] - 2025-05-19

### Adicionado
- Implementação completa de conformidade com a LGPD (Lei Geral de Proteção de Dados)
- Comando `/remover` para permitir que usuários solicitem a exclusão de seus dados
- Comando `/privacidade` para exibir a política de privacidade completa
- Fluxo de consentimento explícito antes do cadastro
- Arquivo de política de privacidade (PRIVACY_POLICY.md)

### Alterado
- Atualizado o comando `/ajuda` para incluir informações sobre LGPD
- Modificado o processo de cadastro para verificar o consentimento LGPD
- Atualizado o README.md com informações sobre conformidade LGPD

### Corrigido
- Corrigido problema de indentação em handlers/cadastro.py
- Corrigido registro de handlers LGPD em bot.py

## [1.1.0] - 2025-04-10

### Adicionado
- Funcionalidade de edição de cadastros existentes
- Comando `/editar_buscar` para localizar cadastros
- Comando `/editar` para modificar campos específicos
- Comando `/excluir` para remover cadastros específicos

### Melhorado
- Mensagens de feedback mais detalhadas
- Confirmações antes de operações críticas
- Navegação no menu de cadastro

## [1.0.0] - 2025-03-15

### Adicionado
- Versão inicial do sistema
- Cadastro de responsáveis por casas de oração
- Interface de menu com botões
- Comandos administrativos básicos
- Sistema de logs para rastreamento de atividades
