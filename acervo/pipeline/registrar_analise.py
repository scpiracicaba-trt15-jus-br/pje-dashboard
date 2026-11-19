"""Registra a coleta da tarefa "Análise" (PJe 1º grau) em ../acervo.json.

Uso:
  python3 registrar_analise.py coleta_analise.json

Formato do arquivo (gerado pela coleta no Chrome):
  {"data": "AAAA-MM-DD", "hora": "HH:MM",
   "unidades": {"CON1": {"total": 1030, "antigos": [{"processo": "0010001-00.2025.5.15.0012", "desde": "2025-03-04"}, ...]}, ...}}

- "total": quantidade de processos na tarefa Análise da unidade.
- "antigos": os 20 processos há mais tempo na tarefa (data de entrada na tarefa, coluna "Desde"),
  do mais antigo para o mais novo. Datas em AAAA-MM-DD (aceita também DD/MM/AAAA).
Grava o total no histórico do dia (historico[].analise) e substitui a lista "analise_antigos"
pela mais recente. Se o dia ainda não tiver coleta do acervo, a entrada é criada só com a análise.
"""
import json, os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ARQ = os.path.join(AQUI, '..', 'acervo.json')
UNIDS = ['CON1', 'CON2', 'LIQ1', 'LIQ2', 'EXE1', 'EXE2', 'EXE3', 'EXE4', 'DAM', 'DIVEX']


def iso(d):
    d = d.strip()
    m = re.match(r'(\d{2})/(\d{2})/(\d{4})', d)
    if m:
        return f'{m.group(3)}-{m.group(2)}-{m.group(1)}'
    if re.match(r'\d{4}-\d{2}-\d{2}', d):
        return d[:10]
    raise ValueError('data inválida: ' + d)


def main(argv):
    if len(argv) != 1:
        print(__doc__); sys.exit(1)
    c = json.load(open(argv[0], encoding='utf-8'))
    data, hora = c['data'], c.get('hora', '')
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', data), 'data deve ser AAAA-MM-DD'
    db = json.load(open(ARQ, encoding='utf-8'))
    hist = db.setdefault('historico', [])
    ent = next((x for x in hist if x['data'] == data), None)
    if ent is None:
        ent = {'data': data, 'hora': hora, 'valores': {}}
        hist.append(ent)
    totais, antigos = ent.get('analise', {}), {}
    for u, v in c['unidades'].items():
        u = u.upper()
        if u not in UNIDS:
            print('Unidade inválida:', u); sys.exit(1)
        if v.get('total') is not None:
            totais[u] = int(v['total'])
        lst = [{'processo': a['processo'].strip(), 'desde': iso(a['desde'])} for a in v.get('antigos', [])]
        antigos[u] = sorted(lst, key=lambda a: a['desde'])[:20]
    ent['analise'] = {u: totais[u] for u in UNIDS if u in totais}
    hist.sort(key=lambda x: x['data'])
    prev = db.get('analise_antigos', {}).get('unidades', {})
    db['analise_antigos'] = {'data': data, 'hora': hora, 'unidades': {u: antigos.get(u, prev.get(u, [])) for u in UNIDS if u in antigos or u in prev}}
    with open(ARQ, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=1); f.write('\n')
    print(f'Tarefa Análise de {data} gravada.')
    for u in UNIDS:
        t = ent['analise'].get(u)
        a = antigos.get(u) or []
        print(f'  {u:6} {("—" if t is None else t):>6}   mais antigo: {a[0]["desde"] if a else "—"}  ({len(a)} listados)')
    faltam = [u for u in UNIDS if u not in ent['analise']]
    if faltam:
        print('Atenção: faltam', ', '.join(faltam))


if __name__ == '__main__':
    main(sys.argv[1:])
