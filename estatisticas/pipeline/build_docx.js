// Monta o documento Word a partir de build/*.json e build/*.png (gerados por gerar.py).
// Uso: node build_docx.js   ->  ../Estatisticas_SC_e_VT_TRT15.docx
const fs = require('fs');
const path = require('path');
const {Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType,
  HeadingLevel, ImageRun, BorderStyle, LevelFormat, Footer, PageNumber, PageOrientation} = require('docx');
const B = path.join(__dirname, 'build');
const R = JSON.parse(fs.readFileSync(path.join(B, 'report2.json'), 'utf8'));
const R3 = JSON.parse(fs.readFileSync(path.join(B, 'report3.json'), 'utf8'));
const T = JSON.parse(fs.readFileSync(path.join(B, 'textos.json'), 'utf8'));
const OUT = path.join(__dirname, '..', 'Estatisticas_SC_e_VT_TRT15.docx');

const NAVY = '1F3864', LIGHT = 'D9E1F2', GREY = 'EDEDED', FONT = 'Arial', W = 14570;
const border = {style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF'};
const borders = {top: border, bottom: border, left: border, right: border};
const tr = (t, o = {}) => new TextRun({text: t, font: FONT, size: 20, ...o});
const p = (t, o = {}) => new Paragraph({spacing: {after: 120}, ...o, children: [tr(t, o.run || {})]});
const runs = (parts, o = {}) => new Paragraph({spacing: {after: 120}, ...o, children: parts.map(x => typeof x === 'string' ? tr(x) : tr(x.text, x))});
const H = (lvl, t, pb) => new Paragraph({pageBreakBefore: !!pb, heading: lvl, children: [new TextRun({text: t, font: FONT})]});
const bullet = t => new Paragraph({numbering: {reference: 'b', level: 0}, spacing: {after: 80}, children: [tr(t)]});
const MES = T.meses, NM = MES.length, AB = T.ab;

function table(header, rows, widths, opt = {}) {
  const fs_ = opt.size || 17, leftCols = opt.left || [1];
  const mk = (txt, i, type) => new TableCell({borders, width: {size: widths[i], type: WidthType.DXA},
    shading: type === 'h' ? {fill: NAVY, type: ShadingType.CLEAR, color: 'auto'} : type === 'hl' ? {fill: LIGHT, type: ShadingType.CLEAR, color: 'auto'} : type === 't' ? {fill: GREY, type: ShadingType.CLEAR, color: 'auto'} : undefined,
    margins: {top: 15, bottom: 15, left: 60, right: 60},
    children: [new Paragraph({alignment: leftCols.includes(i) ? AlignmentType.LEFT : AlignmentType.CENTER,
      children: [new TextRun({text: txt, font: FONT, size: type === 'h' ? fs_ - 1 : fs_, bold: type !== 'n', color: type === 'h' ? 'FFFFFF' : '000000'})]})]});
  return new Table({width: {size: W, type: WidthType.DXA}, columnWidths: widths,
    rows: [new TableRow({tableHeader: true, cantSplit: true, children: header.map((h, i) => mk(h, i, 'h'))}),
      ...rows.map(r => {
        const t = r.some(c => String(c).startsWith('Total TRT')) ? 't' : (opt.hl && opt.hl(r)) ? 'hl' : 'n';
        return new TableRow({cantSplit: true, children: r.map((c, i) => mk(c, i, t))});
      })]});
}
// distribui larguras: colunas fixas + colunas mensais que ocupam o resto
function widths(fixedLeft, fixedRight, n) {
  const rest = W - fixedLeft.reduce((a, b) => a + b, 0) - fixedRight.reduce((a, b) => a + b, 0);
  const each = Math.floor(rest / n), extra = rest - each * n;
  const m = Array(n).fill(each); m[n - 1] += extra;
  return fixedLeft.concat(m).concat(fixedRight);
}
const scHL = r => String(r[1]).startsWith('Piracicaba') || r[0] === 'Piracicaba';
const vtHL = r => r[2] === 'Piracicaba';
const imgF = (f, wd, ht) => new Paragraph({alignment: AlignmentType.CENTER, spacing: {before: 80, after: 80},
  children: [new ImageRun({type: 'png', data: fs.readFileSync(path.join(B, f)), transformation: {width: wd, height: ht}, altText: {title: f, description: 'Gráfico', name: f}})]});
const img = k => imgF(`chart_${k}.png`, 720, 368);
const scW = widths([600, 2770], [1200, 950, 950], NM);
const matW = widths([3370], [], NM);
const vtW = widths([560, 2700, 1960], [1000], NM);
const TIT = {rec: 'Processos recebidos', sol: 'Processos solucionados', pend: 'Pendentes de baixa', liq: 'Extinções na etapa de liquidação', exf: 'Extinções na etapa de execução forçada'};
const FASE = {rec: 'Conhecimento', sol: 'Conhecimento', pend: 'Conhecimento', liq: 'Execução', exf: 'Execução'};
const K = ['rec', 'sol', 'pend', 'liq', 'exf'];

const scPart = K.flatMap((k, i) => {
  const last = k === 'pend' ? [`Variação ${AB}`, `% do TRT (${MES[NM - 1].toLowerCase()})`, `Média/vara (${MES[NM - 1].toLowerCase()})`] : [`Total ${AB}`, '% do TRT', 'Média/vara'];
  const out = [H(HeadingLevel.HEADING_2, `${i + 1}. ${TIT[k]} (${FASE[k]})`, i > 0),
    H(HeadingLevel.HEADING_3, k === 'pend' ? `Estoque mensal e posição em ${T.corte}` : 'Valores mensais e acumulado'),
    table(['Pos.', 'Secretaria Conjunta (varas)', ...MES, ...last], R.sc[k].rows, scW, {hl: scHL})];
  if (k !== 'pend') out.push(H(HeadingLevel.HEADING_3, 'Posição mês a mês'), table(['Secretaria Conjunta', ...MES], R.sc[k].mat, matW, {left: [0], hl: scHL}));
  out.push(p(T.cap[k], {keepNext: true, spacing: {before: 140, after: 60}}), img(k));
  return out;
});
const vtPart = K.flatMap((k, i) => {
  const last = k === 'pend' ? `Var. ${AB}` : `Total ${AB}`;
  const intro = k === 'pend' ? `Estoque de processos pendentes de baixa ao fim de cada mês. A posição considera o acervo em ${T.corte} (1º = maior acervo).` : `Valores mensais e total acumulado de ${T.periodo}, em ordem decrescente do total.`;
  return [H(HeadingLevel.HEADING_2, `${i + 1}. ${TIT[k]} (${FASE[k]})`, i > 0), p(intro, {run: {size: 19}}),
    table(['Pos.', 'Vara do Trabalho', 'Secretaria Conjunta', ...MES, last], R.vt[k], vtW, {left: [1, 2], hl: vtHL, size: 16})];
});
const [a1, a2, a3] = R3.anos;
const anH = [a1, a2, a3, `Var. ${a2.slice(2)}→${a3.slice(2)}`, `% ${a2.slice(2)}→${a3.slice(2)}`, `Var. ${a1.slice(2)}→${a3.slice(2)}`, `% ${a1.slice(2)}→${a3.slice(2)}`, `${T.ano} ${AB}`, `Média/mês ${a3}`, `Média/mês ${T.ano}`, '% média mensal'];
const anSC = [550, 2420, 1000, 1000, 1000, 1100, 900, 1100, 900, 1150, 1100, 1100, 1250];
const anVT = [500, 3000, 1700, 850, 850, 850, 850, 750, 850, 750, 950, 850, 850, 970];
const part3 = [
  H(HeadingLevel.HEADING_1, `Parte III – Comparativo anual de processos recebidos (${a1}–${T.ano})`, true),
  bullet(`Fonte de ${a1}, ${a2} e ${a3}: e-Gestão (estatística "Recebidos", 15ª Região), total de cada ano completo por Vara do Trabalho. ${T.ano}: soma dos relatórios mensais de ${T.periodo} usados nas Partes I e II.`),
  bullet('As colunas "Var." mostram o aumento real em número de processos; as colunas "%" mostram o mesmo aumento em percentual.'),
  bullet(`Como ${T.ano} ainda não tem os 12 meses, a comparação com os anos anteriores é feita pela média mensal (total de ${a3} ÷ 12 e total de ${T.ano} ÷ ${NM}). A média de ${a3} inclui dezembro e janeiro, meses de recesso e menor movimento, o que tende a deixar a média de ${T.ano} um pouco mais alta.`),
  runs([{text: 'Visão geral. ', bold: true}, T.anual1]),
  runs([{text: 'SC Piracicaba. ', bold: true}, T.anual2]),
  H(HeadingLevel.HEADING_2, '1. Por Secretaria Conjunta'),
  table([`Pos. ${a3}`, 'Secretaria Conjunta (varas)', ...anH], R3.sc, anSC, {hl: scHL, size: 16}),
  imgF('chart_anual_total.png', 760, 318),
  imgF('chart_anual_media.png', 760, 318),
  H(HeadingLevel.HEADING_2, '2. Por Vara do Trabalho', true),
  p(`As ${R3.vt.length} Varas do Trabalho em ordem decrescente de processos recebidos em ${a3}. As varas da SC Piracicaba estão destacadas.`, {run: {size: 19}}),
  table([`Pos. ${a3}`, 'Vara do Trabalho', 'Secretaria Conjunta', ...anH], R3.vt, anVT, {left: [1, 2], hl: vtHL, size: 15}),
];
const children = [
  new Paragraph({spacing: {after: 60}, children: [new TextRun({text: 'Estatísticas das Secretarias Conjuntas e Varas do Trabalho do TRT-15', font: FONT, size: 38, bold: true, color: NAVY})]}),
  new Paragraph({spacing: {after: 60}, children: [tr(`Fases de conhecimento e execução – ${T.periodo}, com comparativo anual de recebidos ${a1}–${T.ano}`, {size: 26, color: '404040'})]}),
  new Paragraph({border: {bottom: {style: BorderStyle.SINGLE, size: 12, color: NAVY, space: 4}}, spacing: {after: 240},
    children: [tr(`Fonte: Relatórios do Sistema e-Gestão – TST. Atualizado automaticamente em ${T.gerado}. Linhas destacadas: SC Piracicaba e suas varas.`, {size: 18, color: '595959'})]}),
  H(HeadingLevel.HEADING_1, 'Notas sobre os dados'),
  bullet(`Período: ${T.periodo}, com os relatórios mensais de conhecimento e de execução (cumprimento de sentença) das ${R.vt.rec.length} Varas do Trabalho, recebidos no e-mail "Estatística do 1º Grau".`),
  bullet('Estrutura: a Parte I traz as estatísticas por Secretaria Conjunta, a Parte II por Vara do Trabalho, sempre mês a mês e no acumulado, e a Parte III o comparativo anual de processos recebidos.'),
  bullet('Conferência: os números de cada mês só entram no documento se a soma das varas bater com a linha "Total" do relatório (pendentes de baixa, extinções na liquidação e na execução forçada). Os relatórios de maio/2026 eram imagens escaneadas e foram transcritos e conferidos manualmente.'),
  ...T.conferencias.map(bullet),
  bullet('Os dados são enviados pela Coordenadoria de Estatística "para ciência antes da publicação" e podem receber ressalvas na versão publicada.'),
  bullet('Extinções na liquidação: item 90493 do e-Gestão. Execução forçada: item 90093.'),
  bullet('Recebidos e solucionados somam os totais de cada vara, o que difere da linha "Total" do relatório, que não inclui redistribuições.'),
  bullet(`Pendentes de baixa são um estoque, não uma produção mensal: não são somados. O acumulado usa a posição em ${T.corte}, e a coluna de variação mostra a diferença, em número de processos, desde janeiro.`),
  bullet('SC Bauru: composta por eliminação (Avaré, Bauru, Botucatu, Garça, Itápolis, Jaú, Lençóis Paulista, Marília, Ourinhos, Pederneiras e Santa Cruz do Rio Pardo). Rancharia, zerada em todos os meses, foi excluída.'),
  bullet('Empates recebem a mesma posição.'),
  H(HeadingLevel.HEADING_1, 'Resumo'),
  runs([{text: 'Secretarias Conjuntas. ', bold: true}, T.resumo_sc]),
  runs([{text: 'Varas da SC Piracicaba. ', bold: true}, T.resumo_vt]),
  H(HeadingLevel.HEADING_1, 'Parte I – Estatísticas por Secretaria Conjunta', true),
  ...scPart,
  H(HeadingLevel.HEADING_1, 'Parte II – Estatísticas por Vara do Trabalho', true),
  p(`Cada tabela traz as ${R.vt.rec.length} Varas do Trabalho do TRT-15, com os valores de ${T.periodo} e o total acumulado. As varas da SC Piracicaba estão destacadas.`),
  ...vtPart,
  ...part3,
];
const doc = new Document({
  styles: {default: {document: {run: {font: FONT, size: 20}}},
    paragraphStyles: [
      {id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: {size: 30, bold: true, font: FONT, color: NAVY}, paragraph: {spacing: {before: 240, after: 140}, outlineLevel: 0}},
      {id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: {size: 25, bold: true, font: FONT, color: NAVY}, paragraph: {spacing: {before: 200, after: 100}, outlineLevel: 1}},
      {id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: {size: 20, bold: true, font: FONT, color: '404040'}, paragraph: {spacing: {before: 140, after: 70}, outlineLevel: 2}}]},
  numbering: {config: [{reference: 'b', levels: [{level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: {paragraph: {indent: {left: 540, hanging: 270}}}}]}]},
  sections: [{properties: {page: {size: {width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE}, margin: {top: 1000, bottom: 1000, left: 1134, right: 1134}}},
    footers: {default: new Footer({children: [new Paragraph({alignment: AlignmentType.RIGHT, children: [tr('Estatísticas SC e VT – TRT-15  |  Página ', {size: 16, color: '808080'}), new TextRun({children: [PageNumber.CURRENT], font: FONT, size: 16, color: '808080'})]})]})},
    children}]});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUT, b); console.log('OK:', OUT); });
