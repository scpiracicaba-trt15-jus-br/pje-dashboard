# SISE-JT — `juizos.json` conforme os afastamentos dos magistrados

Rotina diária que mantém `sise-jt/juizos.json` (finais de processo por magistrado em cada vara, lido pela
extensão SISE-JT) de acordo com os afastamentos publicados no site da SC — aba **Férias 2026 e 2027 >
Magistrados** (`index.html`, tabela `#ferias-mag-table`, fonte satelites.trt15.jus.br/designacoes).

| Arquivo | Função |
|---|---|
| `ler_site.py` | Lê a tabela de magistrados do `index.html` (mesma lógica do painel "Magistrados afastados hoje") |
| `atualizar_juizos.py` | Calcula o `juizos.json` do dia e grava se mudou; imprime um resumo em JSON |
| `base_escala.json` | **Escala normal** (todos presentes). Mudou a divisão de finais ou entrou/saiu juiz da vara? Atualize aqui |
| `cobertura.json` | Quem assume **todos** os finais de um juiz afastado, quando a vara tem mais de um colega (ex.: Sumaré — Dra. Francina → Dr. Ronaldo) |
| `estado.json` | Varas que a rotina ajustou por afastamento (para restaurar no retorno) |

## Regras
- Juiz afastado na data → seus finais vão para o colega presente da mesma vara (mais de um colega: vai para quem estiver em `cobertura.json`; sem regra, divididos alternadamente, com aviso para conferir).
- Fim do afastamento → a vara volta à `base_escala.json`.
- Todos os juízes da vara afastados → mantém a base e avisa (verificar substituto).
- Vara com nome fora da base (substituto lançado à mão no `juizos.json`) não é alterada; só avisa.
- Vara diferente da base sem afastamento e sem registro em `estado.json` = ajuste manual: é preservada, com aviso.
- Aviso se a tabela do site estiver com "Atualizado em" há mais de 7 dias.

```bash
cd sise-jt/pipeline
python3 atualizar_juizos.py            # hoje (America/Sao_Paulo)
python3 atualizar_juizos.py 2026-12-01 # simular outra data (grava! use git checkout depois)
```
