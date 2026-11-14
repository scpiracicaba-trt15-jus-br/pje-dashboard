# Férias e afastamentos dos servidores — atualização automática

Alimenta a aba **"Férias 2026 e 2027"** do portal (`index.html`, seção `section-ferias`, sub-aba Servidores),
que lê `ferias/ferias.json`.

Fonte: e-mails **"Solicitação de afastamento"** enviados pelo sistema ROL
(remetente `requerimentosfrequencia_naoresponder@trt15.jus.br`) ao diretor da Secretaria.

## Arquivos

| Arquivo | Função |
|---|---|
| `rol.py` | Lê o texto de um e-mail (texto puro ou HTML) e identifica servidor, matrícula, tipo e períodos |
| `adicionar_email.py` | Acrescenta e-mails novos à base e reconsolida |
| `consolidar.py` | Aplica as solicitações sobre a escala e gera `../ferias.json` |
| `base/solicitacoes.json` | Todas as solicitações lidas (desde jul/2025) |
| `base/ids_processados.json` | IDs das mensagens do Gmail já processadas (evita duplicar) |
| `base/escala_2026_portal.json` | Escala de 2026 que estava digitada no portal — usada só para quem não tem pedido de 2026 por e-mail |

## Regras

- **Férias** e **Férias – Fruição de Saldo Interrompido**: acrescenta os períodos.
- **Alteração de férias**: remove os períodos da "Fruição Original" e acrescenta os "Novos Períodos".
- **Cancelamento de férias**: remove o período.
- **Folga compensatória** (plantão / eleição): aparece como ponto no calendário.
- **Averbação de trabalho** (plantão / eleição): não é afastamento — ignorada.
- Períodos sobrepostos são unidos e marcados para conferência no ROL.
- A unidade (setor) de cada servidor vem do organograma do portal (`ojData` no `index.html`).
  Quem não estiver no organograma aparece em "Não localizado no organograma".

## Passo a passo (feito pela tarefa agendada)

```bash
cd ferias/pipeline
# para cada e-mail novo: salvar o corpo em um arquivo de texto
python3 adicionar_email.py <message_id> <AAAA-MM-DD> corpo1.txt [<id2> <data2> corpo2.txt ...]
```

Código de saída 2 = algum e-mail não pôde ser lido (os demais são gravados normalmente).
