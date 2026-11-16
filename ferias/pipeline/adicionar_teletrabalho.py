"""Acrescenta e-mails de teletrabalho do ROL (indicação, deferimento, indeferimento) à base e reconsolida.

Uso:
  python3 adicionar_teletrabalho.py <message_id> <data do e-mail> <arquivo> [...mais trios]

Cada arquivo tem na 1ª linha "Assunto: <assunto do e-mail>" e, nas linhas seguintes, o corpo
(texto puro ou HTML). A data pode ser AAAA-MM-DD ou o carimbo completo do Gmail
(ex.: 2026-11-13T16:15:04Z), que ordena avisos do mesmo dia. Mensagens já processadas (base/ids_processados.json) são ignoradas, assim como
cópias idênticas do mesmo aviso enviadas a outro destinatário.
Ao final roda consolidar.py. Sai com código 2 se algum e-mail não puder ser lido.
"""
import json, os, sys, subprocess
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from teletrabalho import parse_teletrabalho  # noqa: E402

TEL = os.path.join(AQUI, 'base', 'teletrabalho.json')
IDS = os.path.join(AQUI, 'base', 'ids_processados.json')


def main(args):
    if not args or len(args) % 3:
        print(__doc__); sys.exit(1)
    tel = json.load(open(TEL, encoding='utf-8')) if os.path.exists(TEL) else []
    ids = set(json.load(open(IDS)))
    chave = lambda e: (e['evento'], e['nome'], e['data'], e['meses'], e.get('requerimento'))
    vistos = {chave(e) for e in tel}
    novos, repetidos, falhas = 0, 0, []
    for i in range(0, len(args), 3):
        mid, data, arq = args[i:i + 3]
        if mid in ids:
            continue
        linhas = open(arq, encoding='utf-8').read().split('\n', 1)
        assunto = linhas[0][len('Assunto:'):].strip() if linhas[0].startswith('Assunto:') else ''
        corpo = linhas[1] if assunto else '\n'.join(linhas)
        e = parse_teletrabalho(assunto, corpo)
        if e is None:
            falhas.append(mid); continue
        e.update(id=mid, data=data[:10], data_hora=data)
        ids.add(mid)
        if chave(e) in vistos:
            repetidos += 1; continue
        vistos.add(chave(e)); tel.append(e); novos += 1
        print(f"+ {data} {e['nome']} — teletrabalho {e['evento']}: {e['modalidade']}, {e['meses']} mês(es)"
              f"{', req. ' + e['requerimento'] if e.get('requerimento') else ''}")
    tel.sort(key=lambda e: (e.get('data_hora') or e['data'], e['id']))
    json.dump(tel, open(TEL, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(sorted(ids), open(IDS, 'w'))
    print(f'{novos} evento(s) de teletrabalho novo(s); {repetidos} cópia(s) repetida(s) ignorada(s).')
    subprocess.run([sys.executable, os.path.join(AQUI, 'consolidar.py')], check=True)
    if falhas:
        print('NÃO LIDOS (conferir manualmente):', ', '.join(falhas)); sys.exit(2)


if __name__ == '__main__':
    main(sys.argv[1:])
