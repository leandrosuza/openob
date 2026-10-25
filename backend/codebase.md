# OpenOB - Regras de Codificação

## 📋 Princípios Fundamentais

- **SEGUIR O PROMPT**: Implementar exatamente o solicitado
- **ORGANIZAÇÃO**: Manter boa organização de código, arquivos e pastas
- **CLEAN CODE**: Código limpo, legível e manutenível

## 🎯 Regras de Formatação

- **ESPAÇAMENTO**: Exatamente 5 linhas de espaço entre blocos de código
- **ESTRUTURA**: Usar cabeçalhos e bullets para melhor legibilidade

## 📝 Padrão de Commit

Formato convencional:
```
<tipo>(<escopo>): <descrição curta>

<body opcional>
```

Tipos: feat, fix, refactor, docs, test, chore

## ✅ FEAT Final da Task

Ao final de cada task, gerar o FEAT com o seguinte formato:

---
## 📋 FEAT: [Nome da Feature]

**Título:** feat(escopo): descrição curta

**Descrição:** Resumo conciso do que foi implementado. Mencionar arquivos criados/modificados, padrões usados, e benefícios. Máximo 3-4 linhas.

**Arquivos:** Lista de arquivos criados/modificados

**Benefícios:** Principais benefícios da implementação

---

## 🔍 Exemplo de FEAT

---
## 📋 FEAT: Implementação de Camada de Repositório

**Título:** feat(repositories): adicionar camada de persistência de dados com interface e PostgreSQL

**Descrição:** Implementou arquitetura de repositórios para persistência de dados seguindo princípios SOLID. Criou interfaces para todos os repositórios, RepositoryFactory e implementações PostgreSQL com banco de dados cloud.

**Arquivos:**
- config/settings.py
- repositories/repository_factory.py
- repositories/interfaces/*_repository_interface.py
- repositories/postgresql/postgres_*_repository.py
- core/monitor.py (modificado)

**Benefícios:**
- Código desacoplado e testável
- Fácil extensão para outros bancos (Redis, InfluxDB)
- Configurações centralizadas via .env
- Persistência automática de dados em PostgreSQL cloud
---