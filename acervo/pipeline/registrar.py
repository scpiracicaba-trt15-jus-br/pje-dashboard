"""Registra uma coleta diária do acervo (PJe 1º grau, "Exibir todos") em ../acervo.json.

Uso:
  python3 registrar.py AAAA-MM-DD HH:MM CON1=12345 CON2=678 LIQ1=... [--forcar]

- Uma entrada por dia: se a data já existir, os valores informados substituem os daquele dia
  (unidades não informadas mantêm o valor que já estava gravado).
- Unidades aceitas: CON1 CON2 LIQ1 LIQ2 EXE1 EXE2 EXE3 EXE4 DAM DIVEX.
- Trava de segurança: se alguma unidade variar mais de 15% em relação à última coleta,
  o script NÃO grava e sai com código 3 (provável leitura errada / filtro esquecido).
  Use --forcar só depois de conferir o número na tela do PJe.
Imprime um resumo com a variação de cada unidade.
"""
import json, os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ARQ = os.path.join(AQUI, '..', 'acervo.json')
UNIDS = ['CON1', 'CON2', 'LIQ1', 'LIQ2', 'EXE1', 'EXE2', 'EXE3', 'EXE4', 'DAM', 'DIVEX']
LIMITE = 0.15


def main(argv):
    forcar = '--forcar' in argv
    args = [a for a in argv if a != '--forcar']
    if len(args) < 3 or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args[0]) or not re.fullmatch(r'\d{2}:\d{2}', args[1]):
        print(__doc__); sys.exit(1)
    data, hora = args[0], args[1]
    novos = {}
    for par in args[2:]:
        m = re.fullmatch(r'([A-Za-z0-9]+)=([\d.]+)', par)
        if not m or m.group(1).upper() not in UNIDS:
            print('Par inválido:', par); sys.exit(1)
        novos[m.group(1).upper()] = int(m.group(2).replace('.', ''))

    db = json.load(open(ARQ, encoding='utf-8'))
    hist = sorted(db.get('historico', []), key=lambda x: x['data'])
    anteriores = [x for x in hist if x['data'] < data]
    ref = anteriores[-1]['valores'] if anteriores else {}

    suspeitas = []
    for u, v in novos.items():
        p = ref.get(u)
        if p and abs(v - p) / p > LIMITE:
            suspeitas.append(f'{u}: {p} -> {v} ({(v - p) / p:+.1%})')
    if suspeitas and not forcar:
        print('NÃO GRAVADO — variação acima de 15% (confira no PJe e rode de novo com --forcar se estiver certo):')
        print('\n'.join('  ' + s for s in suspeitas))
        sys.exit(3)

    ent = next((x for x in hist if x['data'] == data), None)
    if ent is None:
        ent = {'data': data, 'hora': hora, 'valores': {}}
        hist.append(ent)
    ent['hora'] = hora
    ent['valores'].update(novos)
    ent['valores'] = {u: ent['valores'][u] for u in UNIDS if u in ent['valores']}
    hist.sort(key=lambda x: x['data'])
    db['historico'] = hist
    db['atualizado'] = f'{data} {hora}'
    with open(ARQ, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=1)
        f.write('\n')

    faltam = [u for u in UNIDS if u not in ent['valores']]
    print(f'Coleta de {data} {hora} gravada.')
    for u in UNIDS:
        v = ent['valores'].get(u)
        p = ref.get(u)
        dv = '' if v is None or p is None else f'  ({v - p:+,})'.replace(',', '.')
        print(f'  {u:6} {("—" if v is None else f"{v:,}".replace(",", ".")):>8}{dv}')
    tot = sum(ent['valores'].values())
    print(f'  TOTAL  {tot:,}'.replace(',', '.'))
    if faltam:
        print('Atenção: faltam', ', '.join(faltam))


if __name__ == '__main__':
    main(sys.argv[1:])
