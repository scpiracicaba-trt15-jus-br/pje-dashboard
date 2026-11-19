// Coleta do acervo no PJe 1º grau (Painel Global > "Exibir todos"), uma unidade por vez.
// Uso (Claude no Chrome, javascript_tool), em loop:
//   1. navegar para https://pje.trt15.jus.br/pjekz/painel/global/todos/lista-processos
//   2. rodar este arquivo terminando com: await acv('<PRÓXIMA UNIDADE>')
//      -> devolve {oj, total, trocou}: lê o total da unidade ATUAL ("1 - 20 de N")
//         e troca o perfil para a próxima unidade (Diretor de Secretaria).
// Ordem usada: (perfil atual) -> CON2 -> LIQ1 -> LIQ2 -> EXE1 -> EXE2 -> EXE3 -> EXE4 -> DAM -> DIVEX -> volta ao perfil inicial.
// Só confie no total se "oj" for a unidade esperada. Só leitura: nada é movimentado.
const acv = async (proxima) => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  let m = null;
  for (let i = 0; i < 60 && !m; i++) { m = document.body.innerText.match(/\d+ - \d+ de (\d+)/); if (!m) await sleep(500); }
  const oj = document.body.innerText.match(/(?:CON\d|LIQ\d|EXE\d|DAM|DIVEX) - Piracicaba/)?.[0];
  let trocou = null;
  if (proxima) {
    if (!document.querySelector('[role="menuitem"]')) { document.querySelector('[aria-label="Trocar Órgão Julgador ou Perfil"]').click(); await sleep(1200); }
    const items = [...document.querySelectorAll('[role="menuitem"]')];
    const k = items.findIndex(e => e.textContent.trim() === proxima + ' - Piracicaba');
    const alvo = k >= 0 ? items.slice(k + 1).find(e => e.getAttribute('aria-disabled') !== 'true' && /Diretor de Secretaria/.test(e.textContent)) : null;
    if (alvo) { alvo.click(); trocou = proxima; }
  }
  return { oj, total: m ? +m[1] : null, trocou };
};
