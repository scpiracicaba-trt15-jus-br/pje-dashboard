"""Gera, a partir de base/serie.json e base/recebidos_anuais.json:
  - ../dados.json            (lido pelo painel estatisticas/index.html)
  - build/*.png, build/*.json (insumos do documento Word, montado por build_docx.js)

Uso:  python3 gerar.py
"""
import json, os, sys, datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from scmap import SC, c2sc  # noqa: E402

BUILD = os.path.join(AQUI, 'build')
os.makedirs(BUILD, exist_ok=True)
FOCO = 'Piracicaba'
K = ['rec', 'sol', 'pend', 'liq', 'exf']
TIT = {'rec': 'Processos recebidos', 'sol': 'Processos solucionados', 'pend': 'Pendentes de baixa',
       'liq': 'Extinções na etapa de liquidação', 'exf': 'Extinções na etapa de execução forçada'}
CURTO = {'rec': 'recebidos', 'sol': 'solucionados', 'pend': 'pendentes de baixa',
         'liq': 'extinções na liquidação', 'exf': 'extinções na execução forçada'}
MESES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
MESES_LONGOS = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto',
                'setembro', 'outubro', 'novembro', 'dezembro']
ULT_DIA = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

serie = json.load(open(os.path.join(AQUI, 'base', 'serie.json')))
anuais = json.load(open(os.path.join(AQUI, 'base', 'recebidos_anuais.json')))
ano = max(m[:4] for m in serie)
MS = sorted(m for m in serie if m.startswith(ano))          # meses do ano corrente
NM = len(MS)
mlab = [MESES[int(m[5:]) - 1] for m in MS]
ult = int(MS[-1][5:])
nome_ult = MESES_LONGOS[ult - 1]
periodo = f'janeiro a {nome_ult} de {ano}' if NM > 1 else f'{nome_ult} de {ano}'
ab_per = f"jan–{MESES[ult - 1].lower()}"
data_corte = f'{ULT_DIA[ult - 1] + (1 if ult == 2 and int(ano) % 4 == 0 else 0):02d}/{ult:02d}'
varas = list(serie[MS[-1]])
scs = list(SC)

f = lambda x: f"{x:,}".replace(',', '.')
sg = lambda x: ("+" if x >= 0 else "−") + f(abs(x))
pc = lambda x: (f"{x:+.1f}".replace('.', ',') + "%").replace('-', '−')
pp = lambda x: f"{x:.1f}".replace('.', ',') + "%"
city = lambda v: v.rsplit(' - ', 1)[0]


def vname(k):
    c, n = k.rsplit(' - ', 1)
    return f"{int(n[:2])}ª VT de {c}"


def ranks(vals):
    s = sorted(vals.items(), key=lambda z: -z[1]); r = {}; prev = None; pos = 0
    for i, (k, v) in enumerate(s, 1):
        if v != prev:
            pos = i; prev = v
        r[k] = pos
    return r, [k for k, _ in s]


# ---------- agregação por SC ----------
agg = {m: {s: {k: 0 for k in K} for s in scs} for m in MS}
for m in MS:
    for v, r in serie[m].items():
        s = c2sc[city(v)]
        for k in K:
            agg[m][s][k] += r.get(k, 0)
nv = {s: sum(1 for v in varas if c2sc[city(v)] == s) for s in scs}
NV = len(varas)


def acum_sc(k):
    return {s: (agg[MS[-1]][s][k] if k == 'pend' else sum(agg[m][s][k] for m in MS)) for s in scs}


def acum_vt(k):
    return {v: (serie[MS[-1]][v][k] if k == 'pend' else sum(serie[m][v][k] for m in MS)) for v in varas}


rep = {'sc': {}, 'vt': {}}
for k in K:
    acc = acum_sc(k); tot = sum(acc.values()); r, order = ranks(acc); rows = []
    for s in order:
        mv = [agg[m][s][k] for m in MS]
        last = [sg(mv[-1] - mv[0])] if k == 'pend' else [f(acc[s])]
        rows.append([f"{r[s]}º", f"{s} ({nv[s]})"] + [f(x) for x in mv] + last + [pp(acc[s] / tot * 100), f(round(acc[s] / nv[s]))])
    T = [sum(agg[m][s][k] for s in scs) for m in MS]
    last = [sg(T[-1] - T[0])] if k == 'pend' else [f(tot)]
    rows.append(['', f'Total TRT-15 ({NV})'] + [f(x) for x in T] + last + ['100,0%', f(round(tot / NV))])
    mr = {m: ranks({s: agg[m][s][k] for s in scs})[0] for m in MS}
    rep['sc'][k] = {'rows': rows, 'mat': [[s] + [f"{mr[m][s]}º" for m in MS] for s in order]}
    vacc = acum_vt(k); vr, vorder = ranks(vacc); vrows = []
    for v in vorder:
        mv = [serie[m][v][k] for m in MS]
        last = [sg(mv[-1] - mv[0])] if k == 'pend' else [f(vacc[v])]
        vrows.append([f"{vr[v]}º", vname(v), c2sc[city(v)]] + [f(x) for x in mv] + last)
    rep['vt'][k] = vrows

# ---------- comparativo anual de recebidos ----------
anos_cheios = sorted({a for v in anuais.values() for a in v})
for a in sorted({m[:4] for m in serie}):           # anos completos da própria série
    if a != ano and all(f'{a}-{i:02d}' in serie for i in range(1, 13)) and a not in anos_cheios:
        anos_cheios.append(a)
        for v in varas:
            anuais.setdefault(v, {})[a] = sum(serie[f'{a}-{i:02d}'][v]['rec'] for i in range(1, 13))
A3 = anos_cheios[-3:]
y_cur = {v: sum(serie[m][v]['rec'] for m in MS) for v in varas}


def linha_anual(a, b, c, z):
    return [f(a), f(b), f(c), sg(c - b), pc((c - b) / b * 100) if b else '–', sg(c - a), pc((c - a) / a * 100) if a else '–',
            f(z), f(round(c / 12)), f(round(z / NM)), pc(((z / NM) / (c / 12) - 1) * 100) if c else '–']


scA = {s: [0, 0, 0, 0] for s in scs}
for v in varas:
    s = c2sc[city(v)]
    for i, a in enumerate(A3):
        scA[s][i] += anuais.get(v, {}).get(a, 0)
    scA[s][3] += y_cur[v]
ordA = sorted(scs, key=lambda s: -scA[s][2])
TA = [sum(scA[s][i] for s in scs) for i in range(4)]
rep3 = {'anos': A3,
        'sc': [[f"{i}º", f"{s} ({nv[s]})"] + linha_anual(*scA[s]) for i, s in enumerate(ordA, 1)] + [['', f'Total TRT-15 ({NV})'] + linha_anual(*TA)],
        'vt': []}
vord = sorted(varas, key=lambda v: -anuais.get(v, {}).get(A3[2], 0)); pos = 0; prev = None
for i, v in enumerate(vord, 1):
    y = [anuais.get(v, {}).get(a, 0) for a in A3]
    if y[2] != prev:
        pos = i; prev = y[2]
    rep3['vt'].append([f"{pos}º", vname(v), c2sc[city(v)]] + linha_anual(*y, y_cur[v]))

# ---------- textos automáticos ----------
def maior(n):
    return 'o maior' if n == 1 else f'o {n}º maior'


def ord_(n):
    return f"{n}ª"


def legenda(k):
    acc = acum_sc(k); r, order = ranks(acc)
    mes = {s: agg[MS[-1]][s][k] for s in scs}; rm, om = ranks(mes)
    if k == 'pend':
        serie_f = [agg[m][FOCO][k] for m in MS]
        pico = max(serie_f); mpico = MESES_LONGOS[int(MS[serie_f.index(pico)][5:]) - 1]
        t = (f"Em {data_corte}, o acervo da SC {FOCO} é de {f(serie_f[-1])} processos, {maior(r[FOCO])} do TRT. ")
        if NM > 1:
            dm = serie_f[-1] - serie_f[-2]
            t += f"Variação em {nome_ult}: {sg(dm)}; desde janeiro: {sg(serie_f[-1] - serie_f[0])}. "
            t += f"Maior valor do ano: {f(pico)} ({mpico}). "
            red = [s for s in scs if agg[MS[-1]][s][k] < agg[MS[-2]][s][k]]
            t += (f"Em {nome_ult}, reduziram o acervo: " + ', '.join(f"{s} ({sg(agg[MS[-1]][s][k] - agg[MS[-2]][s][k])})" for s in red) + '.') if red else f"Em {nome_ult}, nenhuma SC reduziu o acervo."
        return t
    t = f"No acumulado de {periodo}, a SC {FOCO} é a {ord_(r[FOCO])} do TRT ({f(acc[FOCO])})"
    if r[FOCO] == 1:
        seg = order[1]; t += f", {f(acc[FOCO] - acc[seg])} à frente de {seg}. "
    else:
        t += f"; lidera {order[0]} ({f(acc[order[0]])}). "
    t += f"Em {nome_ult}, ficou em {rm[FOCO]}º lugar ({f(mes[FOCO])})"
    lideres = [s for s in scs if rm[s] == 1 and s != FOCO]
    if rm[FOCO] == 1 and lideres:
        t += f", empatada com {', '.join(lideres)}"
    elif rm[FOCO] > 1:
        t += f"; a 1ª do mês foi {om[0]} ({f(mes[om[0]])})"
    return t + '.'


CAP = {k: legenda(k) for k in K}


def resumo_sc():
    partes = []
    for k in ['liq', 'exf', 'rec', 'sol']:
        acc = acum_sc(k); r, _ = ranks(acc); tot = sum(acc.values())
        mes = {s: agg[MS[-1]][s][k] for s in scs}; rm, _ = ranks(mes)
        partes.append(f"{CURTO[k]}: {r[FOCO]}º no acumulado ({f(acc[FOCO])}; {pp(acc[FOCO] / tot * 100)} do TRT) e {rm[FOCO]}º em {nome_ult} ({f(mes[FOCO])})")
    pend = acum_sc('pend'); rp, _ = ranks(pend)
    txt = f"SC {FOCO} — " + '; '.join(partes) + '. '
    txt += f"Acervo pendente em {data_corte}: {f(pend[FOCO])} ({maior(rp[FOCO])} do TRT"
    if NM > 1:
        txt += f"; {sg(agg[MS[-1]][FOCO]['pend'] - agg[MS[-2]][FOCO]['pend'])} em {nome_ult}"
    return txt + ').'


def resumo_vt():
    partes = []
    for k in ['exf', 'liq', 'rec', 'sol']:
        vacc = acum_vt(k); vr, _ = ranks(vacc)
        top = sorted((v for v in varas if c2sc[city(v)] == FOCO), key=lambda v: vr[v])[:3]
        partes.append(f"em {CURTO[k]}, " + ', '.join(f"{vname(v)} ({vr[v]}º, {f(vacc[v])})" for v in top))
    pend = acum_vt('pend'); vr, vo = ranks(pend)
    maior = sorted((v for v in varas if c2sc[city(v)] == FOCO), key=lambda v: vr[v])[0]
    return ("Mais bem posicionadas no TRT, no acumulado — " + '; '.join(partes) +
            f". Maior acervo da SC: {vname(maior)} ({f(pend[maior])}, {vr[maior]}º do TRT).")


def texto_anual():
    a1, a2, a3 = A3
    t1 = (f"O TRT-15 recebeu {f(TA[0])} processos em {a1}, {f(TA[1])} em {a2} ({sg(TA[1] - TA[0])}) e {f(TA[2])} em {a3} ({sg(TA[2] - TA[1])}): "
          f"{sg(TA[2] - TA[0])} processos em dois anos ({pc((TA[2] - TA[0]) / TA[0] * 100)}). De {periodo} foram {f(TA[3])} processos, média mensal de "
          f"{f(round(TA[3] / NM))}, contra {f(round(TA[2] / 12))} em {a3} ({pc(((TA[3] / NM) / (TA[2] / 12) - 1) * 100)}).")
    p = scA[FOCO]
    cres = sorted(scs, key=lambda s: -(scA[s][2] - scA[s][0]) / scA[s][0]); posc = cres.index(FOCO) + 1
    t2 = (f"Passou de {f(p[0])} processos em {a1} para {f(p[1])} em {a2} ({sg(p[1] - p[0])}) e {f(p[2])} em {a3} ({sg(p[2] - p[1])}): "
          f"{sg(p[2] - p[0])} processos em dois anos ({pc((p[2] - p[0]) / p[0] * 100)}), {maior(posc).replace('maior', 'maior crescimento percentual')} entre as 10 SCs. "
          f"De {periodo} recebeu {f(p[3])} processos, média mensal de {f(round(p[3] / NM))}, contra {f(round(p[2] / 12))} em {a3} "
          f"({pc(((p[3] / NM) / (p[2] / 12) - 1) * 100)}).")
    return t1, t2


t1, t2 = texto_anual()
conf = []
for m in MS:
    fn = os.path.join(AQUI, 'base', f'conferencia_{m}.json')
    if os.path.exists(fn):
        c = json.load(open(fn))
        conf.append(f"{MESES_LONGOS[int(m[5:]) - 1].capitalize()}: pendentes ({f(c['pend'])}), liquidação ({f(c['liq'])}) e execução forçada ({f(c['exf'])}) conferem com a linha \"Total\" do relatório.")
textos = {'ano': ano, 'meses': mlab, 'periodo': periodo, 'ab': ab_per, 'corte': data_corte, 'NM': NM,
          'cap': CAP, 'resumo_sc': resumo_sc(), 'resumo_vt': resumo_vt(), 'anual1': t1, 'anual2': t2,
          'anos': A3, 'conferencias': conf, 'gerado': datetime.date.today().strftime('%d/%m/%Y')}
json.dump(rep, open(os.path.join(BUILD, 'report2.json'), 'w'), ensure_ascii=False)
json.dump(rep3, open(os.path.join(BUILD, 'report3.json'), 'w'), ensure_ascii=False)
json.dump(textos, open(os.path.join(BUILD, 'textos.json'), 'w'), ensure_ascii=False)

# ---------- gráficos do documento ----------
cols = plt.cm.tab10.colors
for k in K:
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=160)
    for i, s in enumerate(sorted(scs, key=lambda s: -agg[MS[-1]][s][k])):
        v = [agg[m][s][k] for m in MS]
        if s == FOCO:
            ax.plot(mlab, v, color='#1F3864', lw=3.2, marker='o', label=s, zorder=5)
        else:
            ax.plot(mlab, v, color=cols[i % 10], lw=1.4, alpha=.75, label=s)
    ax.set_title(f'{TIT[k]} por Secretaria Conjunta – {ano}', fontsize=12, fontweight='bold', color='#1F3864')
    ax.grid(alpha=.3); ax.spines[['top', 'right']].set_visible(False)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{x:,.0f}'.replace(',', '.')))
    ax.legend(fontsize=7.5, loc='center left', bbox_to_anchor=(1.01, .5), frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(BUILD, f'chart_{k}.png')); plt.close(fig)

cA = ['#9DB4D8', '#5B7DB1', '#1F3864', '#E07B39']
lab = [s.replace('São José dos Campos', 'SJ Campos').replace('São José do Rio Preto', 'SJ Rio Preto').replace('Presidente Prudente', 'Pres. Prudente') for s in ordA]
x = np.arange(len(ordA))


def fmt(ax):
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f'{v:,.0f}'.replace(',', '.')))
    ax.grid(axis='y', alpha=.3); ax.spines[['top', 'right']].set_visible(False)
    ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=8.5); ax.get_xticklabels()[ordA.index(FOCO)].set_fontweight('bold')


fig, ax = plt.subplots(figsize=(11, 4.6), dpi=160)
series = [(a, [scA[s][i] / 12 for s in ordA]) for i, a in enumerate(A3)] + [(f'{ano} ({ab_per})', [scA[s][3] / NM for s in ordA])]
for j, (nm, vals) in enumerate(series):
    ax.bar(x + (j - 1.5) * .2, vals, .2, label=nm, color=cA[j])
fmt(ax); ax.set_title('Média mensal de processos recebidos por Secretaria Conjunta', fontsize=12, fontweight='bold', color='#1F3864')
ax.legend(frameon=False, fontsize=9, ncol=4, loc='upper right')
fig.tight_layout(); fig.savefig(os.path.join(BUILD, 'chart_anual_media.png')); plt.close(fig)
fig, ax = plt.subplots(figsize=(11, 4.6), dpi=160)
for j, a in enumerate(A3):
    ax.bar(x + (j - 1) * .26, [scA[s][j] for s in ordA], .26, label=a, color=cA[j])
fmt(ax); ax.set_title(f'Processos recebidos por ano e Secretaria Conjunta ({A3[0]}–{A3[2]})', fontsize=12, fontweight='bold', color='#1F3864')
ax.legend(frameon=False, fontsize=9, ncol=3, loc='upper right')
fig.tight_layout(); fig.savefig(os.path.join(BUILD, 'chart_anual_total.png')); plt.close(fig)

# ---------- dados do painel ----------
dados = {
    'gerado_em': datetime.datetime.now().strftime('%d/%m/%Y'),
    'foco': FOCO,
    'ano': ano, 'meses': MS, 'periodo': periodo,
    'scs': scs,
    'varas': [{'id': v, 'nome': vname(v), 'cidade': city(v), 'sc': c2sc[city(v)]} for v in varas],
    'serie': {k: {v: [serie[m][v][k] for m in MS] for v in varas} for k in K},
    'anuais': {'anos': A3, 'valores': {v: [anuais.get(v, {}).get(a, 0) for a in A3] for v in varas}},
    'textos': {'cap': CAP},
}
json.dump(dados, open(os.path.join(AQUI, '..', 'dados.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print(f'OK: {periodo} — {NV} varas, {NM} meses.')
