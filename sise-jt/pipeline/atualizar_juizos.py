"""Atualiza sise-jt/juizos.json conforme os afastamentos dos magistrados publicados no site
(index.html, aba Férias > Magistrados).

Regras:
- base_escala.json = distribuição normal dos finais (todos os juízes presentes).
- Juiz da base afastado na data: seus finais passam ao(s) colega(s) presente(s) da mesma vara
  (um colega: todos; mais de um: alternados, na ordem da base). Todos afastados: mantém a base e avisa.
- Quando o afastamento termina, a vara volta à base (só as varas que esta rotina ajustou — estado.json).
- Vara com nome que não está na base (substituto lançado à mão) não é tocada; só avisa.
Uso: python3 atualizar_juizos.py [AAAA-MM-DD]   (padrão: hoje em America/Sao_Paulo)
Saída: resumo em JSON no stdout. Código 0 = ok (com ou sem mudança)."""
import json, sys, os
from datetime import date, datetime, timedelta, timezone
import ler_site

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
JUIZOS = os.path.join(RAIZ, 'sise-jt', 'juizos.json')
BASE = os.path.join(AQUI, 'base_escala.json')
ESTADO = os.path.join(AQUI, 'estado.json')
COBERTURA = os.path.join(AQUI, 'cobertura.json')  # vara -> {afastado: colega que assume todos os finais}
POSTOS = 'Postos Avançados'


def hoje_sp():
    return (datetime.now(timezone.utc) - timedelta(hours=3)).date()


def fmt(d):
    """Grava no mesmo estilo (tabs) do juizos.json mantido à mão."""
    blocos = []
    for vara, v in d.items():
        if isinstance(v, list):
            itens = ',\n'.join(f'\t\t{json.dumps(x, ensure_ascii=False)}' for x in v)
            blocos.append(f'\t{json.dumps(vara, ensure_ascii=False)}:[\n{itens}\n\t]')
        else:
            js = ',\n'.join(f'\t\t{json.dumps(n, ensure_ascii=False)}:\n\t\t\t[{",".join(map(str, f))}]' for n, f in v.items())
            blocos.append(f'\t{json.dumps(vara, ensure_ascii=False)}: {{\n{js}\n\t}}')
    return '{\n' + ',\n\n'.join(blocos) + '\n\n}\n'


def br(d): return d.strftime('%d/%m/%Y')


def main():
    ref = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else hoje_sp()
    html = open(os.path.join(RAIZ, 'index.html'), encoding='utf-8').read()
    mags, atualizado = ler_site.ler(html)
    base = json.load(open(BASE, encoding='utf-8'))
    atual = json.load(open(JUIZOS, encoding='utf-8'))
    estado = json.load(open(ESTADO, encoding='utf-8')) if os.path.exists(ESTADO) else {}
    cobertura = json.load(open(COBERTURA, encoding='utf-8')) if os.path.exists(COBERTURA) else {}
    nm = lambda n: (mags.get(ler_site.norm(n)) or {}).get('nome') or n.title()
    novo = dict(atual); mud = []; avisos = []; afastados_hoje = []

    for vara, juizes in base.items():
        if vara == POSTOS: continue
        cur = atual.get(vara, {})
        estranhos = [n for n in cur if n not in juizes]
        afast = {}
        for n in juizes:
            m = mags.get(ler_site.norm(n))
            if m is None:
                avisos.append(f'{vara}: {n} não aparece na tabela de magistrados do site')
                continue
            p = next((p for p in m['periodos'] if p['de'] <= ref <= p['ate']), None)
            if p: afast[n] = p
        for n, p in afast.items():
            afastados_hoje.append(f'{nm(n)} ({vara}) — {p["tipo"]} {br(p["de"])} a {br(p["ate"])}')
        if estranhos:
            avisos.append(f'{vara}: há nome fora da escala base ({", ".join(estranhos)}) — substituição lançada à mão, vara não alterada')
            continue
        if afast:
            pres = [n for n in juizes if n not in afast]
            if not pres:
                avisos.append(f'{vara}: todos os juízes afastados — mantida a escala base; verificar substituto')
                alvo = {n: list(f) for n, f in juizes.items()}
            else:
                alvo = {n: list(juizes[n]) for n in pres}
                regra = cobertura.get(vara, {})
                livres = []
                for n in afast:
                    sub = regra.get(n)
                    if sub in alvo: alvo[sub] += juizes[n]
                    else: livres += juizes[n]
                for i, f in enumerate(sorted(livres)):
                    alvo[pres[i % len(pres)]].append(f)
                for n in alvo: alvo[n] = sorted(alvo[n])
                if len(pres) > 1 and livres:
                    avisos.append(f'{vara}: finais do(a) afastado(a) divididos entre {len(pres)} colegas — conferir')
            motivo = 'afastamento de ' + ', '.join(nm(n) for n in afast)
            estado[vara] = {'desde': estado.get(vara, {}).get('desde', ref.isoformat()), 'motivo': motivo}
        elif vara in estado:
            alvo = {n: list(f) for n, f in juizes.items()}
            motivo = 'retorno — volta à escala base'
            del estado[vara]
        else:
            if cur and cur != juizes:
                avisos.append(f'{vara}: difere da escala base sem afastamento no site — mantida como está (se a escala mudou, atualize base_escala.json)')
            continue
        if alvo != cur:
            novo[vara] = alvo
            mud.append({'vara': vara, 'motivo': motivo,
                        'antes': {nm(n): f for n, f in cur.items()},
                        'depois': {nm(n): f for n, f in alvo.items()}})

    if atualizado:
        d_at = datetime.strptime(atualizado, '%d/%m/%Y').date()
        if (ref - d_at).days > 7:
            avisos.append(f'A tabela de magistrados do site está com data de {atualizado} (mais de 7 dias)')

    if mud:
        open(JUIZOS, 'w', encoding='utf-8').write(fmt(novo))
        json.loads(open(JUIZOS, encoding='utf-8').read())  # valida
    json.dump(estado, open(ESTADO, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({'data': ref.isoformat(), 'tabela_site_atualizada_em': atualizado,
                      'mudancas': mud, 'afastados_hoje': afastados_hoje, 'avisos': avisos},
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
