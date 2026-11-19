# Acervo diário — atualização automática

Alimenta a aba **"Visão Geral"** do portal (`index.html`, seção `section-home`), que lê `acervo/acervo.json`
e desenha os cartões, os gráficos de evolução e a tabela. O número "Acervo total" do topo do portal também vem daqui.

Fonte: PJe 1º grau (pje.trt15.jus.br), uma leitura por unidade do total de processos em **"Exibir todos"**.
Coleta feita pela skill **acervo-diario-pje** (Claude no Chrome), uma vez por dia.

## Unidades

| Fase | Unidades |
|---|---|
| Conhecimento | CON1, CON2 |
| Liquidação | LIQ1, LIQ2 |
| Execução | EXE1, EXE2, EXE3, EXE4 |
| DAM | DAM |
| DIVEX | DIVEX |

## Gravar uma coleta

```bash
cd acervo/pipeline
python3 registrar.py 2026-11-19 08:40 CON1=24050 CON2=1810 LIQ1=12020 LIQ2=13590 \
  EXE1=9010 EXE2=14990 EXE3=12010 EXE4=10290 DAM=585 DIVEX=51
```

- Uma entrada por dia (rodar de novo no mesmo dia substitui os valores do dia).
- Se alguma unidade variar **mais de 15%** em relação à coleta anterior, nada é gravado (código de saída 3).
  Confira o número na tela do PJe e, se estiver certo, rode de novo com `--forcar`.
- Enquanto não houver nenhuma coleta, a Visão Geral mostra a apuração de 30/09/2026.

Depois de gravar: `git add acervo/acervo.json && git commit -m "Acervo: coleta de AAAA-MM-DD" && git push`.

## Tarefa Análise

Além do acervo, a coleta lê no **Painel Global → card "Análises"** de cada unidade:
- a quantidade de processos na tarefa (rodapé "1 - 20 de N");
- os **20 mais antigos** na tarefa, com a coluna **"Desde"** ordenada do mais antigo para o mais novo
  (o script confere a ordem e clica no cabeçalho se precisar).

O roteiro está em `coletar.js` (funções `acv`, `ana` e `salvar`). Os resultados ficam no localStorage do PJe
(chave `acv_analise`) e são gravados com:

```bash
python3 registrar_analise.py coleta_analise.json
```

No site, a seção **"Tarefa Análise"** da Visão Geral mostra os cartões por unidade (com o mais antigo e há quantos dias),
o gráfico por unidade, a evolução diária e a tabela dos 20 mais antigos por unidade (dias acima de 60 em destaque).
