"""Consolida as férias e afastamentos dos servidores da SC Piracicaba e gera ../ferias.json
(lido pela aba "Férias 2026 e 2027" do portal).

Entradas:
  base/escala_2026_portal.json  escala de 2026 digitada no portal (ponto de partida)
  base/solicitacoes.json        solicitações do ROL lidas dos e-mails "Solicitação de afastamento"
  ../../index.html              organograma (ojData) — define a unidade de cada servidor

Regras, em ordem cronológica das solicitações:
  férias / saldo interrompido  -> acrescenta os períodos
  alteração de férias          -> remove os períodos da "Fruição Original" e acrescenta os "Novos"
  cancelamento                 -> remove o período
  folga compensatória / outros -> lista à parte (afastamentos de curta duração)

Teletrabalho (base/teletrabalho.json, e-mails de indicação/deferimento/indeferimento do ROL):
  cada indicação abre um registro (nº do requerimento, modalidade, meses); o deferimento ou indeferimento
  seguinte do mesmo servidor fecha o registro. Sai em "teletrabalho" (registro mais recente) e
  "teletrabalho_historico" de cada servidor.
"""
import json, os, re, unicodedata, datetime, hashlib

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
UNIT_SHORT = {'gestao': 'Direção', 'daa': 'DAA', 'cejusc': 'CEJUSC', 'dam': 'DAM', 'con-eq1': 'CON 01', 'con-eq2': 'CON 02',
              'con-eq3': 'CON 03', 'con2': 'CON2', 'liq1': 'LIQ1', 'liq2': 'LIQ2', 'exe1': 'EXE1', 'exe2': 'EXE2', 'exe3': 'EXE3',
              'exe4': 'EXE4', 'divex': 'DIVEX', 'ojs': 'Oficiais de Justiça'}
ORDEM = list(UNIT_SHORT.values())


def norm(x):
    x = unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode().upper()
    return ' '.join(re.sub(r'[^A-Z ]', ' ', x).split())


def carregar_organograma():
    s = open(os.path.join(RAIZ, 'index.html'), encoding='utf-8').read()
    i = s.index('const ojData = ') + len('const ojData = ')
    depth = 0
    for j, ch in enumerate(s[i:], i):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                break
    d = json.loads(s[i:j + 1])
    pessoas = []
    for k, v in d.items():
        if k == 'gestao':
            lista = v.get('equipe', [])          # na gestão, "chefes" são os juízes coordenadores
        else:
            lista = v.get('chefes', []) + v.get('equipe', [])
        for p in lista:
            nome = re.sub(r'\s*\(.*?\)', '', p['name']).strip()
            pessoas.append({'nome': nome, 'unidade': k, 'setor': UNIT_SHORT.get(k, k), 'cargo': p.get('cargo', '')})
    return pessoas


class Indice:
    """Localiza a pessoa pelo nome, tolerando sobrenome a mais/a menos e acentos."""
    def __init__(self):
        self.pessoas = {}

    def achar(self, nome):
        n = norm(nome)
        if n in self.pessoas:
            return n
        tk = set(n.split())
        cand = [k for k in self.pessoas if k.split()[0] == n.split()[0] and (tk <= set(k.split()) or set(k.split()) <= tk)]
        if len(cand) == 1:
            return cand[0]
        # mesmo primeiro nome (único no cadastro) e ao menos dois sobrenomes em comum
        mesmo = [k for k in self.pessoas if k.split()[0] == n.split()[0]]
        if len(mesmo) == 1 and len((tk & set(mesmo[0].split())) - {'DE', 'DA', 'DO', 'DOS', 'DAS', 'E'}) >= 3:
            return mesmo[0]
        return None

    def obter(self, nome, **extra):
        k = self.achar(nome)
        if not k:
            k = norm(nome)
            self.pessoas[k] = {'nome': nome, 'setor': None, 'unidade': None, 'cargo': '', 'matricula': None,
                               'ferias': set(), 'base': set(), 'folgas': [], 'eventos': [], 'fonte_base': False,
                               'tele': []}
        p = self.pessoas[k]
        for a, b in extra.items():
            if b and not p.get(a):
                p[a] = b
        return p


def main():
    idx = Indice()
    for o in carregar_organograma():
        p = idx.obter(o['nome'])
        p.update(nome=o['nome'], unidade=o['unidade'], setor=o['setor'], cargo=o['cargo'])
    for e in json.load(open(os.path.join(AQUI, 'base', 'escala_2026_portal.json'), encoding='utf-8')):
        p = idx.obter(e['nome'])          # o setor vem só do organograma atual
        for a, b in e['periodos']:
            p['base'].add((a, b))
        p['fonte_base'] = True
    sol = json.load(open(os.path.join(AQUI, 'base', 'solicitacoes.json'), encoding='utf-8'))
    # servidores que deixaram o quadro: guardados só como hash do nome normalizado (base/excluidos.json)
    exc_f = os.path.join(AQUI, 'base', 'excluidos.json')
    exc = set(json.load(open(exc_f))) if os.path.exists(exc_f) else set()
    fora = lambda nome: hashlib.sha256(norm(nome).encode()).hexdigest() in exc
    sol = [e for e in sol if not fora(e['nome'])]
    for e in sorted(sol, key=lambda e: e['data']):
        p = idx.obter(e['nome'].title())
        p['matricula'] = p['matricula'] or e['matricula']
        c = e['categoria']
        if c == 'ferias':
            for a, b in e['periodos']:
                p['ferias'].add((a, b))
        elif c == 'alteracao':
            for a, b in e['orig']:
                p['ferias'].discard((a, b)); p['base'].discard((a, b))
            for a, b in e['novo']:
                p['ferias'].add((a, b))
        elif c == 'cancelamento':
            for a, b in e['periodos']:
                p['ferias'].discard((a, b)); p['base'].discard((a, b))
        else:
            for a, b in e.get('periodos', []):
                p['folgas'].append({'de': a, 'ate': b, 'tipo': e['tipo']})
        p['eventos'].append({'data': e['data'], 'tipo': e['tipo'],
                             'periodos': e.get('periodos') or e.get('novo'), 'orig': e.get('orig')})

    def mais_meses(d, n):
        d = datetime.date.fromisoformat(d)
        a, m = divmod(d.month - 1 + n, 12)
        ano, mes = d.year + a, m + 1
        ult = (datetime.date(ano + (mes == 12), mes % 12 + 1, 1) - datetime.timedelta(days=1)).day
        return (datetime.date(ano, mes, min(d.day, ult)) - datetime.timedelta(days=1)).isoformat()

    tel_f = os.path.join(AQUI, 'base', 'teletrabalho.json')
    tel = json.load(open(tel_f, encoding='utf-8')) if os.path.exists(tel_f) else []
    tele_fora = set()
    for e in sorted(tel, key=lambda e: e.get('data_hora') or e['data']):
        if fora(e['nome']):
            continue
        k = idx.achar(e['nome'].title())
        if not k:
            tele_fora.add(e['nome'].title()); continue
        regs = idx.pessoas[k]['tele']
        if e['evento'] == 'indicacao':
            regs.append({'requerimento': e.get('requerimento'), 'modalidade': e['modalidade'], 'meses': e['meses'],
                         'indicado_em': e['data'], 'situacao': 'em análise'})
            continue
        aberto = next((r for r in reversed(regs) if r['situacao'] == 'em análise' and r['meses'] == e['meses']), None)
        if aberto is None:          # decisão sem a indicação correspondente (ex.: indicação feita por outro gestor)
            aberto = {'requerimento': None, 'modalidade': e['modalidade'], 'meses': e['meses'], 'indicado_em': None}
            regs.append(aberto)
        aberto['situacao'] = 'deferido' if e['evento'] == 'deferimento' else 'indeferido'
        aberto['decidido_em'] = e['data']
        if e['evento'] == 'deferimento':
            aberto['ate_previsto'] = mais_meses(e['data'], e['meses'])

    def dias(a, b):
        return (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days + 1

    saida = []
    for p in idx.pessoas.values():
        # a escala digitada no portal só vale para quem não tem nenhum período de 2026 vindo dos e-mails
        tem_2026 = any(a <= '2026-12-31' and b >= '2026-01-01' for a, b in p['ferias'])
        fer = sorted(p['ferias'] | (set() if tem_2026 else p['base']))
        uni = []                      # une períodos sobrepostos (não conta dias em dobro) e marca para conferência
        for a, b in fer:
            if uni and a <= uni[-1]['ate']:
                uni[-1]['ate'] = max(uni[-1]['ate'], b); uni[-1]['obs'] = 'Solicitações com períodos sobrepostos — conferir no ROL'
            else:
                uni.append({'de': a, 'ate': b})
        fer = [dict(u, dias=dias(u['de'], u['ate'])) for u in uni if u['ate'] >= '2026-01-01']
        fol = [f for f in p['folgas'] if f['ate'] >= '2026-01-01']
        if not fer and not fol and p['unidade'] is None:
            continue
        hist = sorted(p['tele'], key=lambda r: r.get('indicado_em') or r.get('decidido_em'))
        saida.append({'nome': p['nome'], 'matricula': p['matricula'], 'setor': p['setor'] or 'Não localizado no organograma',
                      'cargo': p['cargo'], 'ferias': fer, 'folgas': sorted(fol, key=lambda f: f['de']),
                      'ultima_solicitacao': max((ev['data'] for ev in p['eventos']), default=None),
                      'teletrabalho': hist[-1] if hist else None, 'teletrabalho_historico': hist})
    ordem = {s: i for i, s in enumerate(ORDEM)}
    saida.sort(key=lambda x: (ordem.get(x['setor'], 99), x['nome']))
    ult = max((e['data'] for e in sol), default=None)
    ult_tel = max((e['data'] for e in tel), default=None)
    dados = {'atualizado_em': datetime.date.today().isoformat(), 'ultimo_email': ult, 'ultimo_email_teletrabalho': ult_tel,
             'total_solicitacoes': len(sol), 'setores': [s for s in ORDEM if any(x['setor'] == s for x in saida)] +
             sorted({x['setor'] for x in saida} - set(ORDEM)), 'servidores': saida}
    json.dump(dados, open(os.path.join(AQUI, '..', 'ferias.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    sem = [x['nome'] for x in saida if x['setor'] == 'Não localizado no organograma']
    print(f"OK: {len(saida)} servidores; {sum(len(x['ferias']) for x in saida)} períodos de férias; "
          f"{sum(len(x['folgas']) for x in saida)} folgas; último e-mail {ult}.")
    if sem:
        print('Não localizados no organograma:', ', '.join(sem))
    print(f"Teletrabalho: {sum(1 for x in saida if x['teletrabalho'])} servidores com registro; "
          f"último e-mail {ult_tel}.")
    if tele_fora:
        print('Teletrabalho de servidores fora do organograma (não exibidos):', ', '.join(sorted(tele_fora)))


if __name__ == '__main__':
    main()
