"""Leitura dos e-mails "Solicitação de afastamento" do sistema ROL (Requerimentos de Frequência On-line)
do TRT-15 (remetente requerimentosfrequencia_naoresponder@trt15.jus.br).

parse_texto(texto) -> dict com nome, matricula, tipo, e conforme o tipo:
  periodos (férias / folgas / saldo), orig + novo (alteração), periodos (cancelamento).
Retorna None para tipos que não são afastamento (ex.: averbação de trabalho em plantão).
"""
import re

DT = r'(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}/\d{2}/\d{4})'


def _iso(d):
    dd, mm, aa = d.split('/')
    return f'{aa}-{mm}-{dd}'


def _per(txt):
    return [[_iso(a), _iso(b)] for a, b in re.findall(DT, txt)]


def classificar(tipo):
    t = tipo.lower()
    if t.startswith('averbação') or t.startswith('averbacao'):
        return None
    if 'alteração de férias' in t or 'alteracao de ferias' in t:
        return 'alteracao'
    if t.startswith('cancelamento'):
        return 'cancelamento'
    if 'saldo interrompido' in t:
        return 'ferias'
    if t.startswith('férias') or t.startswith('ferias'):
        return 'ferias'
    if t.startswith('folga'):
        return 'folga'
    return 'outro'


def parse_texto(texto):
    s = re.sub(r'<[^>]+>', '\n', texto).replace('*', '')
    s = re.sub(r'[ \t]+', ' ', s)
    r = re.search(r'servidor\(a\)\s+(.+?),\s*(\d+),\s*requereu\s+(.+?)(?:\s+para os seguintes períodos:|\s+de (?=\d{2}/)|,\s*conforme|\s+originalmente|\.\s)', s, re.S)
    if not r:
        # formato "Ciência req. AA - Férias": "servidor(a) NOME, CARGO, código 123, lotado(a) no(a) ..., requereu e
        # teve deferido ou registrado o pedido de Férias para o(s) seguinte(s) período(s): ... referentes ao ano civil"
        r = re.search(r'servidor\(a\)\s+(.+?),[^,]*?,\s*código\s+(\d+),.*?pedido de\s+(.+?)\s+para o\(s\) seguinte\(s\) período\(s\):', s, re.S)
        if not r:
            return None
    nome, mat, tipo = ' '.join(r.group(1).split()), r.group(2), ' '.join(r.group(3).split())
    cat = classificar(tipo)
    if cat is None:
        return None
    e = {'nome': nome, 'matricula': mat, 'tipo': tipo, 'categoria': cat}
    corpo = s[r.end():]
    fim = re.search(r'O prazo|AVISO|Aviso|Para discordar|Para manifestar|Motivo:|referentes ao ano', corpo)
    if cat == 'alteracao':
        mo = re.search(r'Fruição Original:(.*?)Novo\(s\) Período\(s\) de Fruição:(.*?)(?:Motivo:|AVISO|O prazo|$)', s, re.S)
        if not mo:
            return None
        e['orig'], e['novo'] = _per(mo.group(1)), _per(mo.group(2))
    else:
        trecho = corpo[:fim.start()] if fim else corpo
        p = _per(trecho)
        e['periodos'] = p[:1] if cat in ('folga', 'cancelamento', 'outro') else p
    return e
