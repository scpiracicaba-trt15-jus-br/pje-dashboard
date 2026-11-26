"""Lê do index.html do site da SC a tabela #ferias-mag-table (aba Férias > Magistrados)
e devolve, por magistrado, os períodos de afastamento — mesma lógica do painel
"Magistrados afastados hoje" do próprio site (feriasMagAgora)."""
import re, unicodedata
from datetime import date
from html.parser import HTMLParser


def norm(nome):
    s = unicodedata.normalize('NFD', nome)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s).strip().upper()


class _P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.on = False; self.depth = 0
        self.rows = []; self.row = None; self.td = None
        self.grupo = None; self.legenda = ''
        self.cur_el = None  # elemento filho direto da 4ª coluna

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == 'table' and a.get('id') == 'ferias-mag-table':
            self.on = True; return
        if not self.on: return
        if tag == 'tr':
            self._fecha_row()
            self.row = {'cls': a.get('class', ''), 'tds': []}
        elif tag == 'td' and self.row is not None:
            self.td = {'txt': '', 'els': [], 'badge': None}
            self.row['tds'].append(self.td)
        elif self.td is not None and tag == 'span':
            cls = a.get('class', '')
            el = {'cls': cls, 'title': a.get('title'), 'txt': ''}
            if 'afast-badge' in cls and a.get('data-de'):
                self.td['badge'] = {'de': a['data-de'], 'ate': a.get('data-ate') or a['data-de'], 'txt': ''}
                el['badge'] = True
            self.td['els'].append(el); self.cur_el = el

    def handle_endtag(self, tag):
        if not self.on: return
        if tag == 'span': self.cur_el = None
        elif tag == 'td': self.td = None; self.cur_el = None
        elif tag == 'tr': self._fecha_row()
        elif tag == 'table': self._fecha_row(); self.on = False

    def handle_data(self, d):
        if self.td is not None:
            self.td['txt'] += d
            if self.cur_el is not None:
                self.cur_el['txt'] += d
                if self.cur_el.get('badge'): self.td['badge']['txt'] += d

    def _fecha_row(self):
        if self.row is not None:
            self.rows.append(self.row)
        self.row = None; self.td = None


def ler(html):
    p = _P(); p.feed(html); p._fecha_row()
    m = re.search(r'id="ferias-mag-table".*?</table>', html, re.S)
    leg = re.search(r'Atualizado em (\d{2}/\d{2}/\d{4})[^<]*satelites', html)
    mags = {}; grupo = None
    for r in p.rows:
        tds = r['tds']
        if 'mag-group' in r['cls']:
            grupo = tds[0]['txt'].strip() if tds else None; continue
        if len(tds) < 4: continue
        nome = tds[0]['txt'].strip(); vara = re.sub(r'\s+', ' ', tds[1]['txt']).strip()
        per = []; ano = None
        for el in tds[3]['els']:
            t = el['txt'].strip()
            m1 = re.match(r'^(\d{4}):', t)
            if m1: ano = int(m1.group(1)); continue
            if 'ferias-badge' not in el['cls'] or not ano: continue
            mm = re.search(r'(\d{2})/(\d{2})(?:\s*[–-]\s*(\d{2})/(\d{2}))?', t)
            if not mm: continue
            d1, m1_, d2, m2 = mm.groups()
            if not d2: d2, m2 = d1, m1_
            de = date(ano, int(m1_), int(d1)); ate = date(ano, int(m2), int(d2))
            if ate < de: ate = date(ano + 1, int(m2), int(d2))
            per.append({'de': de, 'ate': ate, 'tipo': el['title'] or 'Férias'})
        b = tds[2]['badge']
        if b:
            de = date.fromisoformat(b['de']); ate = date.fromisoformat(b['ate'])
            if not any(x['de'] == de and x['ate'] == ate for x in per):
                per.append({'de': de, 'ate': ate, 'tipo': (b['txt'].split('·')[0] or 'Férias').strip()})
        k = norm(nome)
        e = mags.setdefault(k, {'nome': nome, 'varas': [], 'grupos': [], 'periodos': []})
        e['varas'].append(vara); e['grupos'].append(grupo)
        for x in per:
            if not any(y['de'] == x['de'] and y['ate'] == x['ate'] for y in e['periodos']):
                e['periodos'].append(x)
    return mags, (leg.group(1) if leg else None)
