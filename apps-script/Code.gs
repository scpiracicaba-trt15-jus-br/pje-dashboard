/**
 * Portal SC Piracicaba — acesso restrito ao login do TRT-15 (Google Apps Script).
 *
 * O site continua no repositório do GitHub (que fica PRIVADO). Este app da web:
 *   - só abre para quem está logado com conta @trt15.jus.br (definido na implantação);
 *   - busca no GitHub a página pedida, os .json que ela carrega e as imagens, e monta tudo numa página só;
 *   - publica os PDF/DOCX do repositório numa pasta do Drive visível só para o domínio do TRT-15.
 * As atualizações automáticas (férias, teletrabalho, estatísticas) continuam gravando no GitHub e aparecem aqui
 * sozinhas (com até 5 minutos de cache).
 *
 * Propriedade do script obrigatória: GITHUB_TOKEN (token "fine-grained" só-leitura em Contents deste repositório).
 * Instalação: veja apps-script/README.md.
 */
var REPO = 'scpiracicaba-trt15-jus-br/pje-dashboard';
var RAMO = 'main';
var PASTA_DRIVE = 'Portal SC Piracicaba — arquivos';
var CACHE_SEG = 300;
var IMAGENS = { png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', gif: 'image/gif', svg: 'image/svg+xml', webp: 'image/webp', ico: 'image/x-icon' };
var ARQUIVOS = /\.(pdf|docx?|xlsx?|pptx?|odt|ods|csv|zip)$/i;

/* ======================= App da web ======================= */

function doGet(e) {
  var p = (e && e.parameter && e.parameter.p) || 'index.html';
  var pagina = resolver('', p);
  if (!/\.html?$/i.test(pagina)) pagina = (pagina ? pagina.replace(/\/$/, '') + '/' : '') + 'index.html';
  var gh = github_();
  var html;
  try {
    html = montarPagina(pagina, gh, ScriptApp.getService().getUrl(), linksDrive_());
  } catch (err) {
    html = '<p style="font-family:sans-serif;padding:24px">Página não encontrada ou indisponível: ' +
      String(pagina).replace(/[<>&]/g, '') + '<br><small>' + String(err).replace(/[<>&]/g, '') + '</small></p>';
  }
  var t = /<title>([^<]*)<\/title>/i.exec(html);
  return HtmlService.createHtmlOutput(html)
    .setTitle(t ? t[1] : 'SC Piracicaba')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.DEFAULT);
}

/* ======================= Montagem da página (sem dependências do Apps Script — testável) ======================= */

/** Resolve um caminho relativo (rel) a partir do diretório da página (base). Devolve caminho sem "/" inicial. */
function resolver(base, rel) {
  rel = String(rel).split('#')[0].split('?')[0];
  var partes = rel.charAt(0) === '/' ? [] : String(base).split('/').slice(0, -1);
  rel.split('/').forEach(function (s, i, arr) {
    if (s === '..') partes.pop();
    else if (s !== '.' && s !== '') partes.push(s);
    else if (s === '' && i === arr.length - 1 && arr.length > 1) partes.push('');   // termina em "/"
  });
  return partes.join('/');
}

function _externo(v) {
  return /^(https?:|mailto:|tel:|data:|blob:|javascript:|#|\/\/)/i.test(v) || v.indexOf('${') >= 0 || v.indexOf('{{') >= 0 || v === '';
}

/**
 * gh: { texto(caminho) -> string, base64(caminho) -> string }  (lançam erro se não existir)
 * urlApp: URL do app da web; drive: { caminho: url } para PDF/DOCX.
 */
function montarPagina(pagina, gh, urlApp, drive) {
  var html = gh.texto(pagina);
  var dataUri = {};
  function imagem(c) {
    var ext = (c.split('.').pop() || '').toLowerCase();
    if (!IMAGENS[ext]) return null;
    if (!(c in dataUri)) {
      try { dataUri[c] = 'data:' + IMAGENS[ext] + ';base64,' + gh.base64(c); } catch (e) { dataUri[c] = null; }
    }
    return dataUri[c];
  }
  function linkPagina(c, hash) {
    var alvo = /\.html?$/i.test(c) ? c : (c ? c.replace(/\/$/, '') + '/' : '') + 'index.html';
    return urlApp + (alvo === 'index.html' ? '' : '?p=' + encodeURIComponent(alvo)) + (hash || '');
  }

  // 1) href/src relativos
  html = html.replace(/\b(href|src)=(["'])([^"']*)\2/g, function (m, at, q, v) {
    if (_externo(v)) return m;
    var hash = v.indexOf('#') >= 0 ? v.slice(v.indexOf('#')) : '';
    var c = resolver(pagina, v);
    var img = imagem(c);
    if (img) return at + '=' + q + img + q;
    if (ARQUIVOS.test(c)) return drive && drive[c] ? 'target="_blank" ' + at + '=' + q + drive[c] + q : m;
    if (at === 'href' && (/\.html?$/i.test(c) || /\/$/.test(v) || v === '..' || v === '.' || c === '')) {
      return 'target="_top" href=' + q + linkPagina(c, hash) + q;
    }
    return m;
  });
  // 2) url(...) no CSS
  html = html.replace(/url\((["']?)([^"')]+)\1\)/g, function (m, q, v) {
    if (_externo(v)) return m;
    var img = imagem(resolver(pagina, v));
    return img ? 'url(' + q + img + q + ')' : m;
  });
  // 3) .json carregados com fetch('...') -> embutidos na página
  var dados = {}, re = /fetch\(\s*(["'])([^"']+\.json)\1/g, r;
  while ((r = re.exec(html))) {
    if (_externo(r[2])) continue;
    try { dados[r[2]] = gh.texto(resolver(pagina, r[2])); } catch (e) { /* deixa o fetch falhar normalmente */ }
  }
  var shim = '<script>(function(){var D=' + JSON.stringify(dados).replace(/<\//g, '<\\/').replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029') +
    ';var f=window.fetch;window.fetch=function(u,o){var k=String(u&&u.url||u).split("?")[0].split("#")[0];' +
    'if(Object.prototype.hasOwnProperty.call(D,k))return Promise.resolve(new Response(D[k],{status:200,headers:{"Content-Type":"application/json"}}));' +
    'return f.apply(this,arguments);};' +
    // links externos abrem em nova aba (dentro do app da web não podem abrir no próprio quadro)
    'document.addEventListener("click",function(e){var a=e.target&&e.target.closest&&e.target.closest("a[href]");' +
    'if(a&&!a.target&&/^https?:/i.test(a.getAttribute("href")||""))a.target="_blank";},true);})();<\/script>';
  html = /<head[^>]*>/i.test(html) ? html.replace(/<head[^>]*>/i, function (h) { return h + shim; }) : shim + html;
  return html;
}

/* ======================= GitHub ======================= */

function github_() {
  var token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  if (!token) throw new Error('Defina a propriedade do script GITHUB_TOKEN (veja o README).');
  function baixar(c) {
    var url = 'https://api.github.com/repos/' + REPO + '/contents/' + c.split('/').map(encodeURIComponent).join('/') + '?ref=' + RAMO;
    var resp = UrlFetchApp.fetch(url, {
      headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github.raw', 'X-GitHub-Api-Version': '2022-11-28' },
      muteHttpExceptions: true
    });
    if (resp.getResponseCode() !== 200) throw new Error('GitHub ' + resp.getResponseCode() + ' em ' + c);
    return resp;
  }
  return {
    texto: function (c) { return comCache_('t:' + c, function () { return baixar(c).getContentText('UTF-8'); }); },
    base64: function (c) { return comCache_('b:' + c, function () { return Utilities.base64Encode(baixar(c).getBlob().getBytes()); }); },
    blob: function (c) { return baixar(c).getBlob(); }
  };
}

/** Cache de até CACHE_SEG segundos, dividido em pedaços (limite de 100 KB por chave). */
function comCache_(chave, fn) {
  var cache = CacheService.getScriptCache();
  var k = Utilities.base64EncodeWebSafe(Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, chave)).slice(0, 22);
  var n = cache.get(k + ':n');
  if (n) {
    var chaves = [];
    for (var i = 0; i < +n; i++) chaves.push(k + ':' + i);
    var partes = cache.getAll(chaves);
    if (chaves.every(function (c) { return c in partes; })) return chaves.map(function (c) { return partes[c]; }).join('');
  }
  var v = fn(), TAM = 90000, obj = {}, qt = Math.ceil(v.length / TAM) || 1;
  for (var j = 0; j < qt; j++) obj[k + ':' + j] = v.substr(j * TAM, TAM);
  obj[k + ':n'] = String(qt);
  try { cache.putAll(obj, CACHE_SEG); } catch (e) { /* cache cheio: segue sem cache */ }
  return v;
}

/* ======================= PDF / DOCX no Drive ======================= */

function linksDrive_() {
  var m = JSON.parse(PropertiesService.getScriptProperties().getProperty('ARQUIVOS') || '{}');
  var out = {};
  Object.keys(m).forEach(function (c) { out[c] = 'https://drive.google.com/file/d/' + m[c].id + '/view'; });
  return out;
}

/** Copia para o Drive (pasta restrita ao TRT-15) os PDF/DOCX do repositório que mudaram. Roda todo dia. */
function sincronizarArquivos() {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty('GITHUB_TOKEN');
  var resp = UrlFetchApp.fetch('https://api.github.com/repos/' + REPO + '/git/trees/' + RAMO + '?recursive=1', {
    headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' }
  });
  var arvore = JSON.parse(resp.getContentText()).tree.filter(function (x) { return x.type === 'blob' && ARQUIVOS.test(x.path); });
  var mapa = JSON.parse(props.getProperty('ARQUIVOS') || '{}');
  var pastas = DriveApp.getFoldersByName(PASTA_DRIVE);
  var pasta = pastas.hasNext() ? pastas.next() : DriveApp.createFolder(PASTA_DRIVE);
  var gh = github_(), mudou = [];
  arvore.forEach(function (x) {
    var atual = mapa[x.path];
    if (atual && atual.sha === x.sha) return;
    var blob = gh.blob(x.path).setName(x.path.split('/').pop());
    var arq = pasta.createFile(blob);
    compartilharComDominio_(arq);
    if (atual) { try { DriveApp.getFileById(atual.id).setTrashed(true); } catch (e) { /* já removido */ } }
    mapa[x.path] = { id: arq.getId(), sha: x.sha };
    mudou.push(x.path);
  });
  Object.keys(mapa).forEach(function (c) {          // arquivo apagado do repositório -> lixeira
    if (!arvore.some(function (x) { return x.path === c; })) {
      try { DriveApp.getFileById(mapa[c].id).setTrashed(true); } catch (e) { }
      delete mapa[c]; mudou.push(c + ' (removido)');
    }
  });
  props.setProperty('ARQUIVOS', JSON.stringify(mapa));
  Logger.log(mudou.length ? 'Atualizados: ' + mudou.join(', ') : 'Nenhum arquivo mudou.');
}

function compartilharComDominio_(arq) {
  try {
    arq.setSharing(DriveApp.Access.DOMAIN_WITH_LINK, DriveApp.Permission.VIEW);
  } catch (e) {
    Logger.log('Não consegui compartilhar "' + arq.getName() + '" com o domínio (política do Drive): ' + e);
  }
}

/* ======================= Instalação ======================= */

/** Rode UMA vez depois de colar o código e definir GITHUB_TOKEN: testa o acesso, copia os arquivos e agenda a cópia diária. */
function configurar() {
  var gh = github_();
  var tam = gh.texto('index.html').length;
  Logger.log('GitHub OK (index.html com ' + tam + ' caracteres).');
  sincronizarArquivos();
  var existe = ScriptApp.getProjectTriggers().some(function (t) { return t.getHandlerFunction() === 'sincronizarArquivos'; });
  if (!existe) ScriptApp.newTrigger('sincronizarArquivos').timeBased().everyDays(1).atHour(21).inTimezone('America/Sao_Paulo').create();
  Logger.log('Pronto. Agora: Implantar > Nova implantação > App da Web (Executar como: eu; Quem pode acessar: qualquer pessoa do TRT-15).');
}

if (typeof module !== 'undefined') module.exports = { montarPagina: montarPagina, resolver: resolver };
