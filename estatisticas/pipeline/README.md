# Estatísticas do 1º Grau — atualização mensal

Gera o painel `estatisticas/index.html` (lê `estatisticas/dados.json`) e o documento
`estatisticas/Estatisticas_SC_e_VT_TRT15.docx` a partir dos relatórios do e-Gestão
enviados no e-mail **"Estatística do 1º Grau – <Mês> de <Ano>"**
(remetentes: cooesp.secgge@trt15.jus.br / cep.age@trt15.jus.br).

## Arquivos

| Arquivo | Função |
|---|---|
| `base/serie.json` | Série mensal por vara (chave `AAAA-MM`): recebidos, solucionados, pendentes, extinções na liquidação e na execução forçada |
| `base/recebidos_anuais.json` | Recebidos de 2023, 2024 e 2025 por vara (exportação do e-Gestão) |
| `base/conferencia_AAAA-MM.json` | Totais do relatório usados na conferência de cada mês |
| `scmap.py` | Composição das 10 Secretarias Conjuntas (cidade → SC) |
| `extrair_mes.py` | Lê os dois PDFs de um mês, confere com a linha "Total" e grava em `base/serie.json` |
| `gerar.py` | Gera `../dados.json`, gráficos e textos (em `build/`) |
| `build_docx.js` | Monta o documento Word |

## Passo a passo (feito automaticamente pela tarefa agendada)

```bash
cd estatisticas/pipeline
pip install --break-system-packages pdfplumber matplotlib   # se faltar
npm install                                                   # instala docx
python3 extrair_mes.py 2026-11 "11_2026_VT_Conhecimento....pdf" "11_2026_VT_Execucao....pdf"
python3 gerar.py
node build_docx.js
```

Use somente os anexos **VT_Conhecimento** e **VT_Execucao** (às vezes chamado *VT_Extincoes*);
os anexos *Juizes_\** não são usados.

`extrair_mes.py` termina com código **2** e não grava nada se:
- alguma vara estiver faltando ou houver vara nova sem SC definida em `scmap.py`;
- a soma dos pendentes, das extinções na liquidação (item 90493) ou na execução forçada
  (item 90093) não bater com a linha "Total" do relatório;
- o PDF vier escaneado (sem texto) — nesse caso é preciso transcrever o mês manualmente.

Nesses casos o painel não é atualizado e o responsável deve ser avisado.
