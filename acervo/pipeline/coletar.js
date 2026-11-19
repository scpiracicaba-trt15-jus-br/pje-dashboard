// Coleta no PJe 1º grau (Claude no Chrome, javascript_tool). Só leitura.
// Por unidade, com o perfil da unidade ativo:
//   1. navegar para https://pje.trt15.jus.br/pjekz/painel/global/todos/lista-processos  -> await acv()           (acervo total)
//   2. navegar para https://pje.trt15.jus.br/pjekz/painel/global                         -> await ana('<PRÓXIMA>') (tarefa Análise + troca de perfil)
// acv(): lê "1 - 20 de N" da tela Exibir todos.  -> {oj, total}
// ana(proxima): clica no card "Análises" do Painel Global, ordena a coluna "Desde" do mais antigo para o mais novo,
//   lê o total e os 20 primeiros (processo + data de entrada na tarefa) e, se informado, troca o perfil
//   para a próxima unidade (item "<UNIDADE> - Piracicaba" > "Diretor de Secretaria").
//   -> {oj, total, antigos:[{processo, desde:'DD/MM/AAAA'}], ordenado, trocou}
// Ordem: CON1 -> CON2 -> LIQ1 -> LIQ2 -> EXE1 -> EXE2 -> EXE3 -> EXE4 -> DAM -> DIVEX -> (volta a CON1).
const sleep = ms => new Promise(r => setTimeout(r, ms));
const ojAtual = () => document.body.innerText.match(/(?:CON\d|LIQ\d|EXE\d|DAM|DIVEX) - Piracicaba/)?.[0];
const lerTotal = async () => { let m = null; for (let i = 0; i < 60 && !m; i++) { m = document.body.innerText.match(/\d+ - \d+ de (\d+)/); if (!m) await sleep(500); } return m ? +m[1] : null; };
const trocar = async (proxima) => {
  if (!proxima) return null;
  if (!document.querySelector('[role="menuitem"]')) { document.querySelector('[aria-label="Trocar Órgão Julgador ou Perfil"]').click(); await sleep(1200); }
  const items = [...document.querySelectorAll('[role="menuitem"]')];
  const k = items.findIndex(e => e.textContent.trim() === proxima + ' - Piracicaba');
  const alvo = k >= 0 ? items.slice(k + 1).find(e => e.getAttribute('aria-disabled') !== 'true' && /Diretor de Secretaria/.test(e.textContent)) : null;
  if (alvo) { alvo.click(); return proxima; }
  return null;
};
const acv = async (proxima) => ({ oj: ojAtual(), total: await lerTotal(), trocou: await trocar(proxima) });
const ana = async (proxima) => {
  let card = null;
  for (let i = 0; i < 40 && !card; i++) { card = [...document.querySelectorAll('*')].find(e => e.children.length === 0 && e.textContent.trim() === 'Análises'); if (!card) await sleep(500); }
  if (!card) return { oj: ojAtual(), erro: 'card Análises não encontrado' };
  const zero = /^\s*0\s/.test(card.closest('[role="group"],mat-card,div')?.parentElement?.innerText || '');
  card.click();
  const total = await lerTotal();
  const linhas = () => { const hs = [...document.querySelectorAll('thead th')]; const ci = hs.findIndex(t => /Desde/.test(t.innerText));
    return [...document.querySelectorAll('tbody tr')].map(r => { const td = r.querySelectorAll('td'); return { processo: (r.innerText.match(/\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}/) || [''])[0], desde: ((td[ci] ? td[ci].innerText : '').match(/\d{2}\/\d{2}\/\d{4}/) || [''])[0] }; }).filter(x => x.processo && x.desde); };
  const k = d => d.split('/').reverse().join('');
  const asc = L => L.every((x, i) => i === 0 || k(L[i - 1].desde) <= k(x.desde));
  let L = total ? linhas() : [], ordenado = asc(L);
  for (let t = 0; t < 2 && L.length > 1 && !ordenado; t++) {
    [...document.querySelectorAll('thead th')].find(t => /Desde/.test(t.innerText)).querySelector('.th-elemento-class, div').click();
    await sleep(4000); L = linhas(); ordenado = asc(L);
  }
  return { oj: ojAtual(), total: total ?? (zero ? 0 : null), antigos: L.slice(0, 20), ordenado, trocou: await trocar(proxima) };
};
// Guarda cada resultado no localStorage (chave acv_analise_<UNIDADE>) para ler tudo no fim, sem truncar:
//   const r = await ana('<PRÓXIMA>'); salvar(r);
//   no fim: JSON.parse(localStorage.getItem('acv_analise'))
const salvar = r => { const u = (r.oj || '').split(' ')[0]; const all = JSON.parse(localStorage.getItem('acv_analise') || '{}');
  all[u] = { total: r.total, antigos: (r.antigos || []).map(a => a.processo + '|' + a.desde), ordenado: r.ordenado };
  localStorage.setItem('acv_analise', JSON.stringify(all)); return u + ' total=' + r.total + ' n=' + (r.antigos || []).length + ' ordenado=' + r.ordenado + ' mais_antigo=' + ((r.antigos || [])[0] || {}).desde + ' trocou=' + r.trocou + (r.erro ? ' ERRO=' + r.erro : ''); };
