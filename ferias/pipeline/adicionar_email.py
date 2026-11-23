"""Acrescenta um e-mail "Solicitação de afastamento" (ROL) à base e reconsolida a aba de férias.

Uso:
  python3 adicionar_email.py <message_id> <AAAA-MM-DD> <arquivo_com_o_texto_do_email> [...mais trios]

O texto pode ser o corpo em texto puro ou em HTML. Mensagens já processadas são ignoradas.
Averbações de trabalho (não são afastamento) são só marcadas como processadas.
Ao final roda consolidar.py. Sai com código 2 se algum e-mail não puder ser lido.
"""
import json, os, sys, subprocess
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from rol import parse_texto  # noqa: E402
from consolidar import norm  # noqa: E402
import hashlib
_EXC = os.path.join(AQUI, 'base', 'excluidos.json')
EXC = set(json.load(open(_EXC))) if os.path.exists(_EXC) else set()

SOL = os.path.join(AQUI, 'base', 'solicitacoes.json')
IDS = os.path.join(AQUI, 'base', 'ids_processados.json')


def main(args):
    if not args or len(args) % 3:
        print(__doc__); sys.exit(1)
    sol = json.load(open(SOL, encoding='utf-8'))
    ids = set(json.load(open(IDS)))
    novos, ignorados, falhas = 0, 0, []
    for i in range(0, len(args), 3):
        mid, data, arq = args[i:i + 3]
        if mid in ids:
            continue
        texto = open(arq, encoding='utf-8').read()
        e = parse_texto(texto)
        if e is None:
            if ('servidor(a)' in texto or 'usuário(a)' in texto) and 'requereu' in texto and 'verbação' not in texto:
                falhas.append(mid); continue
            ids.add(mid); ignorados += 1; continue
        if e['categoria'] == 'alteracao' and not e.get('novo'):
            falhas.append(mid); continue
        if e['categoria'] != 'alteracao' and not e.get('periodos'):
            falhas.append(mid); continue
        e.update(id=mid, data=data)
        if hashlib.sha256(norm(e['nome']).encode()).hexdigest() in EXC:
            ids.add(mid); ignorados += 1; continue          # servidor que deixou o quadro
        sol.append(e); ids.add(mid); novos += 1
        print(f"+ {data} {e['nome']} — {e['tipo']}: {e.get('periodos') or e.get('novo')}")
    json.dump(sol, open(SOL, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(sorted(ids), open(IDS, 'w'))
    print(f'{novos} solicitação(ões) nova(s); {ignorados} ignorada(s) (averbação ou servidor fora do quadro).')
    subprocess.run([sys.executable, os.path.join(AQUI, 'consolidar.py')], check=True)
    if falhas:
        print('NÃO LIDOS (conferir manualmente):', ', '.join(falhas)); sys.exit(2)


if __name__ == '__main__':
    main(sys.argv[1:])
