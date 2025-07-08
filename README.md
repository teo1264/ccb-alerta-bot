# 📱 CCB Alerta Bot - Guia do Usuário

## 🎯 **O QUE É O CCB ALERTA BOT?**

Sistema automatizado que **cadastra responsáveis das Casas de Oração da CCB Região Mauá** para recebimento de **alertas automáticos** sobre:

- 💧 **Consumo excessivo de água** (integração Sistema BRK)
- ⚡ **Consumo anormal de energia** (ENEL)
- ☀️ **Relatórios fotovoltaicos** mensais
- 📊 **Comunicados administrativos**

---

## 🤖 **COMO USAR O BOT**

### **1️⃣ PRIMEIRO ACESSO**

1. **Abra o Telegram** no seu celular
2. **Procure por**: `@CCBAlertaBot` (nome do bot)
3. **Clique em "Iniciar"** ou digite qualquer mensagem
4. **Aceite os termos LGPD** (proteção de dados)

### **2️⃣ MENU PRINCIPAL**

Após aceitar os termos, você verá o menu com botões:

- 📝 **CADASTRAR RESPONSÁVEL** - Principal função
- ℹ️ **Ajuda** - Lista de comandos
- 🆔 **Meu ID** - Mostra seu ID do Telegram

---

## 📝 **PROCESSO DE CADASTRO PASSO A PASSO**

### **ETAPA 1: SELECIONAR CASA DE ORAÇÃO**
- Lista com todas as 38 Casas da Região Mauá
- Navegue com botões **⬅️ Anterior** / **Próxima ➡️**
- Clique na sua Casa de Oração (ex: BR21-0270 - CENTRO)

### **ETAPA 2: INFORMAR SEU NOME**
- Digite seu nome completo
- Mínimo 3 caracteres
- Exemplo: "João da Silva"

### **ETAPA 3: SELECIONAR FUNÇÃO**
Escolha sua função no menu:
- 🤝 **Cooperador**
- ⛪ **Diácono**
- 👴 **Ancião**
- 📝 **Auxiliar da Escrita**
- 🔧 **Encarregado da Manutenção**

*Ou use* **🔄 Outra Função** *para digitar uma função personalizada*

### **ETAPA 4: CONFIRMAÇÃO**
- Revise seus dados
- Clique em **✅ Confirmar** para finalizar
- Ou **❌ Cancelar** para recomeçar

### **✅ CADASTRO CONCLUÍDO!**
Mensagem de sucesso confirma que você receberá os alertas automáticos.

---

## 💬 **COMANDOS DISPONÍVEIS**

### **👤 PARA TODOS OS USUÁRIOS:**
```
/start - Mensagem de boas-vindas + menu
/cadastrar - Iniciar cadastro passo a passo
/meu_id - Mostrar seu ID do Telegram
/ajuda - Lista todos os comandos
/remover - Excluir seus dados (LGPD)
/privacidade - Política de privacidade
```

### **👨‍💼 PARA ADMINISTRADORES:**
```
/exportar - Gerar planilha com todos cadastros
/listar - Listar cadastros (com filtros)
/editar_buscar - Buscar cadastros para edição
/admin_add - Adicionar novo administrador
```

---

## 🚨 **TIPOS DE ALERTAS QUE VOCÊ RECEBERÁ**

### **🔗 INTEGRAÇÃO COM SISTEMA BRK**
O bot está **integrado ao Sistema BRK** (controle financeiro da CCB), que monitora automaticamente todas as contas de água e energia.

### **📱 ALERTAS AUTOMÁTICOS:**

#### **💧 ÁGUA (Sistema BRK)**
- **Normal**: "Consumo dentro do esperado - 18m³"
- **Alto**: "⚠️ Consumo elevado detectado - 35m³ (+94%)"
- **Crítico**: "🚨 Possível vazamento - 65m³ (+260%)"
- **Emergência**: "🚨🚨 URGENTE: Consumo anormal - 120m³ (+550%)"

#### **⚡ ENERGIA (ENEL)**
- Padrões de consumo fora do normal
- Picos de demanda não usuais
- Relatórios comparativos mensais

#### **☀️ FOTOVOLTAICO**
- Relatórios mensais de compensação
- Eficiência da geração solar
- Economia obtida

#### **📊 ADMINISTRATIVOS**
- Comunicados da administração
- Informações sobre manutenção
- Instruções preventivas

---

## 🎯 **QUEM DEVE SE CADASTRAR?**

### **✅ RESPONSÁVEIS DIRETOS:**
- **Cooperadores** - Responsabilidade geral da Casa
- **Encarregados da Manutenção** - Cuidados técnicos
- **Auxiliares da Escrita** - Controle administrativo
- **Diáconos e Anciãos** - Supervisão geral

### **📍 COBERTURA COMPLETA:**
**38 Casas de Oração da Região Mauá:**
```
BR21-0270 - CENTRO
BR21-0271 - JARDIM PRIMAVERA
BR21-0272 - JARDIM MIRANDA D'AVIZ
BR21-0273 - JARDIM SANTISTA
BR21-0274 - JARDIM SÔNIA MARIA
BR21-0275 - JARDIM ZAÍRA
BR21-0276 - PARQUE DAS AMÉRICAS
BR21-0277 - PARQUE SÃO VICENTE
BR21-0278 - VILA NOVA MAUÁ
BR21-0373 - JARDIM ORATÓRIO
BR21-0395 - JARDIM LUZITANO
BR21-0408 - VILA CARLINA
BR21-0448 - JARDIM ZAÍRA - GLEBA C
BR21-0472 - JARDIM ARACY
BR21-0511 - ESTRADA SAPOPEMBA - KM 11
BR21-0520 - VILA ASSIS BRASIL
BR21-0562 - CAPUAVA
BR21-0566 - JARDIM ALTO DA BOA VISTA
BR21-0573 - JARDIM BOM RECANTO
BR21-0574 - JARDIM BRASÍLIA
BR21-0589 - ALTO DO MACUCO
BR21-0591 - JARDIM GUAPITUBA
BR21-0616 - JARDIM ZAÍRA - GLEBA A
BR21-0653 - JARDIM ITAPARK VELHO
BR21-0668 - VILA MAGINI
BR21-0727 - VILA MERCEDES
BR21-0736 - JARDIM ESPERANÇA
BR21-0745 - JARDIM HÉLIDA
BR21-0746 - JARDIM COLÚMBIA
BR21-0751 - VILA VITÓRIA
BR21-0757 - JARDIM CRUZEIRO
BR21-0774 - JARDIM MAUÁ
BR21-0856 - JARDIM ZAÍRA - GLEBA D
BR21-0920 - CHÁCARA MARIA FRANCISCA
BR21-1082 - JARDIM ITAPARK NOVO
BR21-1108 - RECANTO VITAL BRASIL
```

---

## 🔒 **PROTEÇÃO DOS SEUS DADOS (LGPD)**

### **📋 O QUE COLETAMOS:**
- Nome completo
- Função na Igreja
- ID do Telegram
- Username do Telegram (se disponível)

### **🎯 PARA QUE USAMOS:**
- Envio de alertas sobre sua Casa de Oração
- Comunicação administrativa específica
- Relacionamento com Sistema BRK (automação)

### **🛡️ COMO PROTEGEMOS:**
- Dados criptografados no OneDrive
- Acesso restrito a administradores
- Conformidade total com LGPD
- Não compartilhamos com terceiros

### **✅ SEUS DIREITOS:**
- **Acessar**: Ver seus dados armazenados
- **Remover**: Comando `/remover` exclui tudo
- **Atualizar**: Refazer cadastro atualiza dados
- **Revogar**: Sair do sistema a qualquer momento

---

## 💡 **EXEMPLO PRÁTICO DE USO**

### **📋 CENÁRIO REAL:**
```
📧 Sistema BRK detecta consumo alto na JARDIM BRASÍLIA
🔍 Consulta: Quem são os responsáveis por BR21-0574?
👥 Encontra: João (Cooperador), Maria (Aux. Escrita)
📱 Envia alertas personalizados via Telegram:
```

**📱 MENSAGEM PARA JOÃO:**
```
🚨 ALERTA CONSUMO - JARDIM BRASÍLIA

A Paz de Deus, João!

Detectamos consumo elevado de água:
📍 Casa: BR21-0574 - JARDIM BRASÍLIA  
💧 Consumo: 45m³ (Normal: 18m³)
📈 Aumento: +150% acima da média
📅 Período: Julho/2025

⚠️ Verificar possível vazamento.

Deus te abençoe! 🙏
```

### **⚡ RESULTADO:**
- **Responsável notificado** imediatamente
- **Ação preventiva** pode evitar prejuízos
- **Sistema BRK protege** contra débitos suspeitos
- **Histórico completo** para auditoria

---

## 🛠️ **PROBLEMAS COMUNS E SOLUÇÕES**

### **❓ "Não consigo me cadastrar"**
- Certifique-se de aceitar os termos LGPD primeiro
- Use o botão **📝 CADASTRAR RESPONSÁVEL**
- Se der erro, digite `/cadastrar`

### **❓ "Minha função não está na lista"**
- Use **🔄 Outra Função**
- Digite sua função específica
- Sistema detecta funções similares automaticamente

### **❓ "Quero alterar meus dados"**
- Faça um novo cadastro (substitui o anterior)
- Ou peça ajuda a um administrador

### **❓ "Não estou recebendo alertas"**
- Verifique se completou o cadastro
- Confirme que não bloqueou o bot
- Entre em contato com administração

### **❓ "Quero sair do sistema"**
- Use o comando `/remover`
- Confirme a exclusão dos dados
- Processo irreversível (LGPD)

---

## 📞 **SUPORTE E CONTATO**

### **🤖 SUPORTE TÉCNICO:**
- **Desenvolvedor**: Sidney Gubitoso - Auxiliar Tesouraria
- **Sistema**: Integrado ao BRK (proteção financeira)
- **Disponibilidade**: 24/7 automático

### **👨‍💼 ADMINISTRADORES:**
Lista atual de administradores configurados via variável `ADMIN_IDS`

### **📋 REPORTAR PROBLEMAS:**
1. Use `/ajuda` para verificar comandos
2. Tente `/cadastrar` novamente  
3. Entre em contato com administração local
4. Reporte problemas técnicos ao desenvolvedor

---

## 🚀 **BENEFÍCIOS DO SISTEMA**

### **✅ PARA OS RESPONSÁVEIS:**
- **Alertas instantâneos** sobre suas Casas
- **Prevenção de prejuízos** por vazamentos
- **Comunicação direcionada** sem spam
- **Histórico completo** de todos alertas
- **Interface simples** via Telegram

### **✅ PARA A ADMINISTRAÇÃO:**
- **Monitoramento automático** 38 Casas
- **Proteção financeira** contra consumos altos
- **Base atualizada** de responsáveis
- **Comunicação eficiente** e rastreável
- **Integração total** com Sistema BRK

### **✅ PARA A CCB:**
- **Economia significativa** prevenindo vazamentos
- **Gestão moderna** das Casas de Oração
- **Conformidade LGPD** em dados pessoais
- **Automação completa** reduz trabalho manual
- **Transparência total** no processo

---

## 🎯 **CONCLUSÃO**

O **CCB Alerta Bot** é mais que um simples bot do Telegram - é um **sistema completo de proteção e comunicação** que:

🔗 **Se integra ao Sistema BRK** para monitoramento financeiro  
📱 **Automatiza alertas direcionados** para cada responsável  
🛡️ **Protege contra prejuízos** por vazamentos e consumos altos  
📊 **Facilita a gestão** das 38 Casas de Oração  
🙏 **Serve à obra de Deus** com tecnologia moderna e eficiente  

**Cadastre-se hoje e faça parte desta rede de proteção automática!**

---

> **📱 Para usar**: Procure `@CCBAlertaBot` no Telegram  
> **🔧 Desenvolvido por**: Sidney Gubitoso - Auxiliar Tesouraria Administrativa Mauá  
> **🔗 Integrado ao**: Sistema BRK (proteção financeira CCB)  
> **🛡️ Conformidade**: LGPD - Lei Geral de Proteção de Dados  
> **⚡ Status**: Ativo 24/7 - Deploy automático Render

_Deus abençoe este trabalho em favor da Sua obra! 🙏_
