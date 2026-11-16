"""Leitura dos e-mails de teletrabalho do sistema ROL (remetente requerimentosfrequencia_naoresponder@trt15.jus.br):

  "Indicação para atuação em teletrabalho - Requerimento nº 13208/2026-AA - <requerente>"  -> evento 'indicacao'
  "Deferimento de indicação para atuação em teletrabalho"                                    -> evento 'deferimento'
  "Indeferimento de indicação para atuação em teletrabalho"                                  -> evento 'indeferimento'

parse_teletrabalho(assunto, texto) -> dict com evento, nome (servidor indicado), meses, modalidade
e, na indicação, requerimento (ex.: "13208/2026-AA"). Retorna None se o e-mail não for desse tipo.
"""
import re


def _conserta(s):
    """Alguns e-mails chegam com acentos quebrados ("cÃ³digo", "perÃ­odo"); desfaz o erro de codificação
    só nesses trechos (o resto do texto pode estar correto, como "TÉCNICO")."""
    def um(m):
        try:
            return m.group().encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return m.group()
    return re.sub('[\u00c2\u00c3][\u0080-\u00bf]', um, s)


def parse_teletrabalho(assunto, texto):
    a = _conserta(assunto or '')
    s = _conserta(texto or '')
    s = ' '.join(re.sub(r'<[^>]+>', ' ', s).split())
    al = a.lower()
    if 'teletrabalho' not in al and 'teletrabalho' not in s.lower():
        return None
    m = re.search(r'servidora/servidor\s+(.+?),\s*pelo per[ií]odo de\s*(\d+)\s*m[eê]s\(es\)\s*para atua[çc][ãa]o em\s+(Teletrabalho\s+\w+)', s, re.I)
    if not m:
        return None
    if al.startswith('indeferimento') or re.search(r'foi indeferido', s, re.I):
        ev = 'indeferimento'
    elif al.startswith('deferimento') or re.search(r'foi deferido', s, re.I):
        ev = 'deferimento'
    elif al.startswith('indicação') or al.startswith('indicacao'):
        ev = 'indicacao'
    else:
        return None
    e = {'evento': ev, 'nome': m.group(1).strip(), 'meses': int(m.group(2)),
         'modalidade': ' '.join(m.group(3).split()).title()}
    r = re.search(r'Requerimento\s*n[º°o.]*\s*([\d./-]+-?[A-Z]*)', a, re.I)
    if r:
        e['requerimento'] = r.group(1).strip('-')
    return e
