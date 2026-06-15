# Relatório de Inconsistências

> Gerado em: 2026-06-11  
> Comparação: Fluxos (PDFs) × Checklists (CHECK-LIST GERAL.xlsx) × Roles Descriptions  
> Regra aplicada: "Atendimento" → "Relacionamento" em todas as ocorrências

---

## 1. Renomeação Incompleta — "Atendimento" → "Relacionamento"

O checklist (XLSX) já usa "relacionamento" na maioria dos itens, mas os **quatro PDFs** ainda usam "ATENDIMENTO" como nome da swim lane/papel. As ocorrências a corrigir nos PDFs são:

| Documento | Ocorrências de "Atendimento" | Ação necessária |
|---|---|---|
| FLUXO UHULL GERAL | ~10 ocorrências de "ATENDIMENTO" nos blocos | Renomear para "Relacionamento" |
| FLUXO OPERAÇÃO GERAL | ~15 ocorrências de "ATENDIMENTO" / "ATEND." / "ATEND.PROD.CONCIERGE" | Renomear para "Relacionamento" |
| FLUXO FECHAMENTO GERAL | ~15 ocorrências de "atendimento" | Renomear para "Relacionamento" |
| FLUXO COTAÇÃO GERAL | Não usa "Atendimento" (usa "NOVOS NEGÓCIOS") | Nenhuma ação necessária |

**Impacto:** Os PDFs são o material de referência visual da equipe. Enquanto não forem atualizados, haverá confusão com o nome do papel.

---

## 2. Arquivo de Roles Descriptions Ausente

**Problema crítico:** Não existe nenhum arquivo de Roles Descriptions entre os materiais exportados do Mural. O arquivo `roles-descriptions-atualizado.md` foi criado inteiramente a partir da inferência dos fluxos e do checklist.

**Consequência:** Não é possível verificar se algum papel nas roles descriptions está sem tarefas, ou se há tarefas atribuídas a papéis que não existem na descrição oficial — pois não há descrição oficial para comparar.

**Ação recomendada:** Confirmar se existe um board separado no Mural com as Roles Descriptions e exportá-lo. O arquivo `roles-descriptions-atualizado.md` pode servir como rascunho base.

---

## 3. Fluxo "Aprovação e VT" sem PDF correspondente

**Problema:** Dos 5 fluxos listados, o **"Fluxo de Aprovação e VT"** não possui um PDF exportado separado.

- O FLUXO UHULL GERAL cobre a fase de aprovação/onboarding, mas não a VT em detalhe.
- A VT (Viagem de Inspeção) está detalhada apenas no checklist (seção "VIAGEM DE INSPEÇÃO", linhas 88–171), sem diagrama de fluxo correspondente.

**Mapeamento dos 5 fluxos vs. PDFs encontrados:**

| Fluxo esperado | PDF encontrado | Status |
|---|---|---|
| Fluxo de Cotação | FLUXO COTAÇÃO GERAL | ✅ OK |
| Uhull Geral — Fluxo macro | FLUXO UHULL GERAL | ✅ OK |
| Fluxo de Aprovação e VT | *(nenhum)* | ❌ **FALTANDO** |
| Fluxo de Operação pós-VT | FLUXO OPERAÇÃO GERAL | ✅ OK |
| Uhull Fechamento | FLUXO FECHAMENTO GERAL | ✅ OK |

**Ação recomendada:** Exportar o PDF do "Fluxo de Aprovação e VT" do Mural, ou confirmar se ele foi incorporado ao FLUXO UHULL GERAL e está implícito.

---

## 4. Tarefas sem Responsável Definido

Os itens abaixo estão no checklist sem nenhum papel atribuído na coluna "quem":

| Linha | Tarefa | Fluxo | Responsável provável |
|---|---|---|---|
| 267 | Pedir regras de campanha e logo para plataforma | Operação | Relacionamento [INFERIDO] |
| 284 | Receber régua de comunicação e artes para inserir no WhatsApp | Operação | Concierge [INFERIDO] |
| 294 | Preparar inventário | Operação | Operações [INFERIDO] |
| 347 | Comprar farmacinha, Kit higiene e separar material de escritório | Pré-Embarque | Operações [INFERIDO] — duplicata da linha 322 que tem "operações" |

---

## 5. Papel Inválido como Responsável

### 5.1 "Belezura" como responsável (linha 157)
- **Tarefa:** "Montar nova belezura e enviar para relacionamento"
- **Problema:** "Belezura" é o nome de um documento/produto da empresa, não um papel. Aparece como responsável por erro de preenchimento.
- **Responsável inferido:** Planejamento (com base nas demais tarefas de criação da belezura no Fluxo Cotação)

### 5.2 "Gestora" como responsável (linhas 18–19)
- **Tarefas:** "Definir quem será responsável pelo projeto em operações, aéreo e terrestre" e "Inserir nome do responsável aéreo e terrestre no Slack"
- **Problema:** "Gestora" aparece como papel secundário junto a "aéreo e terrestre", mas não é um papel definido em nenhum dos fluxos.
- **Ação:** Confirmar se "Gestora" refere-se a um cargo específico (ex.: Gestora de Operações) e substituir pelo nome oficial do papel.

### 5.3 "Plataforma" como responsável (linha 91)
- **Tarefa:** "Preparar Plataforma para a VT"
- **Problema:** "Plataforma" é um sistema/fornecedor externo, não um papel interno.
- **Responsável inferido:** Concierge / Relacionamento (quem opera a plataforma internamente)

---

## 6. Tarefas Duplicadas

| Linhas duplicadas | Tarefa | Fluxo | Recomendação |
|---|---|---|---|
| 72 e 74 | "Com base nas infos de fornecedores, montar cash flow e prazos para emissão e enviar para financeiro" | Uhull | Remover uma das ocorrências |
| 135/207/302/318 | "Pedir para concierge solicitar foto e mensagem para contato de emergência" | VT / Operação / Pré-Embarque | Verificar se são momentos diferentes (VT × Grupo) ou duplicata — unificar se for o mesmo momento |
| 136/208/303/319 | "Receber foto e mensagem e enviar para marketing produzir cartão postal" | VT / Operação / Pré-Embarque | Idem acima |
| 322 e 347 | "Comprar farmacinha, Kit higiene e separar material de escritório" | Pré-Embarque | Remover linha 347 (sem responsável); manter linha 322 (Operações) |

**Nota:** As tarefas de "foto/mensagem para contato de emergência" que aparecem na VT e no grupo principal podem ser intencionais (contextos distintos). Confirmar antes de remover.

---

## 7. Ambiguidades de Papéis

### 7.1 "Planejamento" vs. "Planner" — são o mesmo papel?
- No FLUXO COTAÇÃO, existem duas swim lanes distintas: **PLANNER** (elabora o ST inicial) e **PLANEJAMENTO** (elabora o ST final, KV, belezura, textos roteiro).
- No checklist, "planejamento" cria o conceito, KV e belezura, enquanto "planner" faz dicas, roteiro e sobe conteúdo na plataforma.
- **Recomendação:** Confirmar se são papéis distintos ou se "Planner" e "Planejamento" são nomes diferentes para a mesma função.

### 7.2 "Operações" vs. "Terrestre" — são o mesmo papel?
- No checklist, "terrestre" aparece com tarefas de cotação DMC e planilha comercial (fase cotação).
- Em outros fluxos, "operações" executa as mesmas funções operacionais.
- **Recomendação:** Confirmar se "Terrestre" é uma sub-especialidade dentro de Operações ou um papel separado.

### 7.3 "Comercial" vs. "Novos Negócios" — são o mesmo papel?
- O FLUXO COTAÇÃO usa "NOVOS NEGÓCIOS" para todas as atividades de pré-venda.
- Os demais fluxos (Uhull, Fechamento) usam "comercial" para as mesmas responsabilidades.
- **Recomendação:** Unificar para um único nome (provavelmente "Comercial", pois é o mais usado no checklist).

---

## 8. Responsável Incorreto — Linha 160

- **Tarefa:** "Aprovar dicas com cliente e liberar para planner publicar na plataforma"
- **Responsável registrado:** Planner
- **Problema:** A ação de "aprovar com cliente" é sempre responsabilidade de Relacionamento (padrão consistente em todo o checklist). O Planner é quem publica, não quem aprova.
- **Correção sugerida:** Alterar responsável para **Relacionamento**; Planner executa a publicação após a aprovação.

---

## 9. Questões Abertas nos PDFs (Sticky Notes sem Resolução)

Dois sticky notes no FLUXO UHULL GERAL registram dúvidas sem resposta:

1. **"em que momento pedir direito de uso de imagem???"** — Não há tarefa correspondente no checklist para obtenção do direito de uso de imagem.
2. **"em que momento temos prazos DMC e aéreo? Como conciliar?"** — Tensão de prazos não resolvida no fluxo.

**Ação recomendada:** Incluir ambas como tarefas no checklist com responsável definido, após alinhamento interno.

---

## 10. Etapas de Fluxo sem Tarefas de Checklist

| Fluxo | Etapa sem cobertura no checklist |
|---|---|
| Cotação | Processo de criação do ST pelo Planner (citado no PDF, não detalhado no checklist) |
| Uhull | Pergunta sobre direito de uso de imagem (sticky note — sem tarefa) |
| Uhull | Conciliação de prazos DMC × aéreo (sticky note — sem tarefa) |
| Fechamento | Reunião de debriefing com guia (aparece no PDF, não está no checklist na seção "APÓS A VIAGEM") |

---

## Resumo das Inconsistências

| Categoria | Qtd. de itens | Prioridade |
|---|---|---|
| Renomeação Atendimento → Relacionamento nos PDFs | 4 documentos | Alta |
| Roles Descriptions ausente | 1 arquivo crítico | Alta |
| Fluxo VT sem PDF | 1 fluxo | Alta |
| Tarefas sem responsável | 4 itens | Média |
| Papel inválido como responsável | 3 casos | Média |
| Tarefas duplicadas | 4 grupos | Média |
| Ambiguidades de papéis | 3 pares | Média |
| Responsável incorreto | 1 item | Baixa |
| Questões abertas não resolvidas | 2 itens | Baixa |
| Etapas sem cobertura no checklist | 4 etapas | Baixa |
