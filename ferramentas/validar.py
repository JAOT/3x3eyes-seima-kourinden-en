"""Valida um ficheiro de tradução contra o guião japonês.

Uso: python validar.py <traducao.txt> [guiao_jp.txt]

Verifica, para cada mensagem:
  - as etiquetas de controlo (tudo menos {n}, {w}, {clr}) são as mesmas e pela mesma ordem;
  - o texto é ASCII (os carateres japoneses só são aceites se forem espaços　);
  - cada linha tem no máximo 21 carateres ({08:xx} conta 8, {07:xx} conta 5);
  - cada caixa ({clr}) tem no máximo 4 linhas (aviso).
Sai com código 1 se houver erros.
"""
import re, sys, pathlib

MAX_LINE = 21
BATTLE_LINE = 26     # caixa de combate (mensagens 0000-0064): 28 colunas, com margem
BATTLE_MSGS = range(0x0000, 0x0065)
MAX_LINES = 4
LAYOUT = {'n', 'w', 'clr'}
TAG = re.compile(r'\{([^}]*)\}')


def parse(path):
    msgs, cur, buf = {}, None, []
    for line in pathlib.Path(path).read_text(encoding='utf-8').splitlines():
        m = re.match(r'^####\s+([0-9A-Fa-f]+)', line)
        if m:
            if cur is not None:
                msgs[cur] = '\n'.join(buf)
            cur, buf = int(m.group(1), 16), []
        elif cur is not None and not line.startswith(';'):
            buf.append(line)
    if cur is not None:
        msgs[cur] = '\n'.join(buf)
    return msgs


def control_tags(text):
    return [t for t in TAG.findall(text) if t not in LAYOUT]


HALF = set('0123456789MFB ')


def jp_max_width(jp):
    """Largura (em meias larguras) da linha mais comprida do japonês."""
    best = width = 0
    for tag, text in re.findall(r'\{([^}]*)\}|([^{]+)', jp.replace('\n', '')):
        if tag:
            if tag in ('n', 'clr'):
                width = 0
            elif tag.startswith(('08:', '1A:', '2A:')):
                width += 8
            elif tag.startswith('07:'):
                width += 5
        else:
            width += sum(1 if c in HALF else 2 for c in text)
        best = max(best, width)
    return best


def check(msg_id, en, jp):
    errs, warns = [], []
    max_line = max(BATTLE_LINE if msg_id in BATTLE_MSGS else MAX_LINE, jp_max_width(jp))   # janelas de narração podem ser mais largas
    if control_tags(en) != control_tags(jp):
        errs.append(f'etiquetas diferentes: jp={control_tags(jp)} en={control_tags(en)}')
    flat = en.replace('\n', '')
    plain = TAG.sub('', flat).replace('　', '')
    bad = sorted({c for c in plain if not (0x20 <= ord(c) <= 0x7E)})
    if bad:
        errs.append(f'carateres não ASCII: {"".join(bad)}')
    width, lines = 0, 1
    for tag, text in re.findall(r'\{([^}]*)\}|([^{]+)', flat):
        if tag:
            if tag == 'n':
                width, lines = 0, lines + 1
            elif tag == 'clr':
                width, lines = 0, 1
            elif tag.startswith('08:') or tag.startswith('1A:') or tag.startswith('2A:'):
                width += 8
            elif tag.startswith('07:'):
                width += 5
        else:
            width += sum(2 if c == '　' else 1 for c in text)
        if width > max_line:
            errs.append(f'linha com mais de {max_line} carateres perto de: {text or tag!r}')
            width = 0
        if lines > MAX_LINES + 2:
            warns.append('caixa com muitas linhas')
            lines = 1
    return errs, warns


def main(tr, jp_path=None):
    root = pathlib.Path(__file__).resolve().parent.parent
    jp = parse(jp_path or root / 'guiao_jp.txt')
    en = parse(tr)
    n_err = 0
    for msg_id in sorted(en):
        if msg_id not in jp:
            print(f'{msg_id:04X}: não existe no guião japonês'); n_err += 1; continue
        errs, warns = check(msg_id, en[msg_id], jp[msg_id])
        for e in errs:
            print(f'{msg_id:04X}: ERRO {e}'); n_err += 1
        for w in warns:
            print(f'{msg_id:04X}: aviso {w}')
    print(f'{len(en)} mensagens verificadas, {n_err} erros')
    sys.exit(1 if n_err else 0)


if __name__ == '__main__':
    main(*sys.argv[1:])
