"""Extrai um mês dos relatórios do e-Gestão (anexos do e-mail "Estatística do 1º Grau")
e grava em base/serie.json — somente se os números conferirem com a linha "Total".

Uso:
  python3 extrair_mes.py AAAA-MM  <pdf_conhecimento>  <pdf_execucao>

Anexos usados: "MM_AAAA_VT_Conhecimento..." e "MM_AAAA_VT_Execucao..." (às vezes
"VT_Extincoes"). Os anexos "Juizes_*" não são usados.

Sai com código 0 se gravou, 2 se a conferência falhou (nada é gravado).
"""
import json, os, re, subprocess, sys
import pdfplumber

AQUI = os.path.dirname(os.path.abspath(__file__))
SERIE = os.path.join(AQUI, 'base', 'serie.json')
sys.path.insert(0, AQUI)
from scmap import c2sc  # noqa: E402


def num(x):
    return 0 if x in ('-', '–') else int(x.replace('.', ''))


def ler_conhecimento(pdf):
    txt = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
    periodo = next((l.strip() for l in txt.splitlines() if 'Período' in l), '')
    dados, erros, total_pend = {}, [], None
    for ln in txt.splitlines():
        if re.match(r'^\s*Total\s', ln):
            t = ln.split()
            total_pend = num(t[-1])
            continue
        r = re.match(r'^\s*(.+?)\s+-\s+(\d\da)(?: Vara)?\s+([\d\.\-–].*)$', ln)
        if not r:
            continue
        t = r.group(3).split()
        nome = r.group(1).strip() + ' - ' + r.group(2)
        if len(t) != 11:
            erros.append(f'linha com {len(t)} colunas: {ln.strip()}')
            continue
        v = [num(x) for x in t]
        if not (v[0] + v[1] + v[2] == v[3] and v[4] + v[5] == v[6] and v[8] + v[9] == v[10]):
            erros.append(f'soma interna não confere: {ln.strip()}')
        dados[nome] = {'rec': v[3], 'sol': v[6], 'pend': v[10]}
    return dados, total_pend, periodo, erros


def ler_execucao(pdf):
    dados, totais = {}, None
    with pdfplumber.open(pdf) as doc:
        for pg in doc.pages:
            w = pg.extract_words()
            hx = {}
            for x in w:
                mm = re.search(r'(9\d{4})\)?', x['text'])
                if mm and mm.group(1) in ('90493', '90093', '90492'):
                    hx[mm.group(1)] = (x['x0'] + x['x1']) / 2
            if len(hx) < 3:
                continue
            linhas = {}
            for x in w:
                linhas.setdefault(round(x['top']), []).append(x)
            for _, ws in sorted(linhas.items()):
                ws = sorted(ws, key=lambda z: z['x0'])
                s = ' '.join(z['text'] for z in ws)
                nums = [z for z in ws if re.fullmatch(r'[\d\.]+', z['text']) and z['x0'] > ws[0]['x0'] + 60]

                def col(item):
                    c = hx[item]
                    b = [z for z in nums if abs((z['x0'] + z['x1']) / 2 - c) < 18]
                    return int(b[0]['text'].replace('.', '')) if b else 0
                if re.match(r'^Total\b', s) and not s.startswith('Total -'):
                    totais = {'liq': col('90493'), 'exf': col('90093'), 'tot': col('90492')}
                    continue
                r = re.match(r'^(.+?)\s+-\s+(\d\da)\b', s)
                if not r:
                    continue
                nome = r.group(1).strip() + ' - ' + r.group(2)
                dados[nome] = {'liq': col('90493'), 'exf': col('90093'), 'tot': col('90492')}
    return dados, totais


def main():
    if len(sys.argv) != 4 or not re.fullmatch(r'\d{4}-\d{2}', sys.argv[1]):
        print(__doc__)
        sys.exit(1)
    mes, fc, fe = sys.argv[1:]
    con, total_pend, periodo, erros = ler_conhecimento(fc)
    exe, tot_exe = ler_execucao(fe)
    for d in (con, exe):
        d.pop('Rancharia - 01a', None)

    serie = json.load(open(SERIE))
    ref = serie[sorted(serie)[-1]]  # varas do último mês já validado
    faltam = [k for k in ref if k not in con or k not in exe]
    novas = [k for k in set(con) | set(exe) if k not in ref]
    sem_sc = [k for k in novas if k.rsplit(' - ', 1)[0] not in c2sc]

    soma = {k: sum(v[k] for v in con.values()) for k in ('rec', 'sol', 'pend')}
    soma.update({k: sum(v[k] for v in exe.values()) for k in ('liq', 'exf', 'tot')})
    problemas = list(erros)
    if faltam:
        problemas.append(f'{len(faltam)} varas ausentes: ' + ', '.join(faltam[:10]) + (' ...' if len(faltam) > 10 else ''))
    if sem_sc:
        problemas.append('varas novas sem Secretaria Conjunta definida (atualizar scmap.py): ' + ', '.join(sem_sc))
    if total_pend is None or soma['pend'] != total_pend:
        problemas.append(f'pendentes: soma {soma["pend"]} x Total {total_pend}')
    if not tot_exe:
        problemas.append('linha Total da execução não encontrada')
    else:
        for k in ('liq', 'exf', 'tot'):
            if soma[k] != tot_exe[k]:
                problemas.append(f'{k}: soma {soma[k]} x Total {tot_exe[k]}')

    print('Período:', periodo)
    print('Somas:', soma, '| Totais do relatório: pend', total_pend, tot_exe)
    if problemas:
        print('CONFERÊNCIA FALHOU — nada foi gravado:')
        for p in problemas:
            print(' -', p)
        sys.exit(2)

    serie[mes] = {k: {**con[k], 'liq': exe[k]['liq'], 'exf': exe[k]['exf']} for k in sorted(set(con) & set(exe))}
    serie = {k: serie[k] for k in sorted(serie)}
    json.dump(serie, open(SERIE, 'w'), ensure_ascii=False, separators=(',', ':'))
    json.dump({'mes': mes, 'periodo': periodo, 'pend': total_pend, **tot_exe},
              open(os.path.join(AQUI, 'base', f'conferencia_{mes}.json'), 'w'), ensure_ascii=False)
    print(f'OK: {mes} gravado ({len(serie[mes])} varas).')


if __name__ == '__main__':
    main()
