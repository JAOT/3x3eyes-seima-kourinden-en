"""Junta linhas partidas a meio de uma frase quando o resultado cabe na caixa (não muda o texto).

Uso: python juntar_linhas.py <traducao_en.txt> <guiao_jp.txt> [--aplicar]

Regras:
  - só mexe em quebras {n} a meio de frase (a linha anterior não acaba em . ! ? … ” " ) ] ou ~);
  - um "grupo" é uma sequência de linhas ligadas por essas quebras; o grupo é reescrito de forma gulosa
    e só é alterado se ficar com MENOS linhas;
  - não junta através de {w}, {clr}, {0B} nem linhas em branco/centradas;
  - largura máxima = a mesma do validar.py (21, 26 no combate, ou a largura do japonês, se maior);
    {08:xx} conta 8, {07:xx} conta 5, os outros códigos contam 0.
"""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import validar

END = tuple('.!?…"”)]~:;-')
TAG = re.compile(r'\{([^}]*)\}')


def width(s):
    w = 0
    for tag, text in re.findall(r'\{([^}]*)\}|([^{]+)', s):
        if tag:
            if tag.startswith(('08:', '1A:', '2A:')):
                w += 8
            elif tag.startswith('07:'):
                w += 5
        else:
            w += sum(2 if c == '　' else 1 for c in text)
    return w


def jp_width(jp):
    """Largura da linha japonesa mais comprida, ignorando linhas só de espaços (enchimento)."""
    best = 0
    for line in re.split(r'\{(?:n|clr|w|0B)\}', jp.replace('\n', '')):
        if not TAG.sub('', line).strip(' 　'):
            continue
        best = max(best, validar.jp_max_width(line))
    return best


def plain_end(s):
    return TAG.sub('', s).rstrip()


def reflow(lines, limit):
    """lines: textos das linhas de um grupo (sem {n}). Devolve as novas linhas (gulosa)."""
    words = ' '.join(lines).split(' ')
    out, cur = [], ''
    for w in words:
        cand = w if not cur else cur + ' ' + w
        if width(cand) <= limit:
            cur = cand
        else:
            out.append(cur)
            cur = w
    out.append(cur)
    return out


def process(body, limit):
    # separa o corpo em segmentos: texto entre quebras {n}; os separadores fortes ficam no fim dos segmentos
    raw = body.replace('\n', '')
    parts = raw.split('{n}')
    # parts[i] seguido de {n} (exceto o último)
    changed = 0
    i, res = 0, []
    while i < len(parts):
        j = i
        # alarga o grupo enquanto a quebra entre parts[j] e parts[j+1] é a meio de frase
        while j + 1 < len(parts):
            a, b = parts[j], parts[j + 1]
            core_a = plain_end(a)
            if (not core_a or core_a.endswith(END) or re.search(r'\{(w|clr|0B)\}\s*$', a)
                    or '{w}' in a[:-0 or None] and False):
                break
            if not TAG.sub('', b).strip() or b.startswith((' ', '　')) or '　' in b:
                break
            if re.search(r'\{(w|clr|0B)\}', a.split('{')[0] if False else ''):
                break
            j += 1
        group = parts[i:j + 1]
        if j > i:
            # o 1.º segmento pode ter códigos/texto antes do último {w}/{clr}: só reflui a parte final
            head, first = '', group[0]
            m = list(re.finditer(r'\{(w|clr|0B)\}', first))
            if m:
                head, first = first[:m[-1].end()], first[m[-1].end():]
            pre = re.match(r'((?:\{05:[^}]*\})*)', first).group(1)   # código de velocidade no início (ex.: {05:03})
            first = first[len(pre):]
            last = group[-1]
            # o último segmento pode continuar com {w}/{clr}: só a parte até ao 1.º desses entra no grupo
            m2 = re.search(r'\{(w|clr|0B)\}', last)
            tail = ''
            if m2:
                last, tail = last[:m2.start()], last[m2.start():]
            body_lines = [first] + group[1:-1] + [last]
            # grupos com nomes/números ({08}, {07}, ...) ficam como estão: os nomes podem ter até 16 letras
            if not any(TAG.search(l) for l in body_lines):
                new = reflow(body_lines, limit)
                if len(new) < len(body_lines) and all(width(l) <= limit for l in new):
                    changed += len(body_lines) - len(new)
                    new[0] = head + pre + new[0]
                    new[-1] = new[-1] + tail
                    res.extend(new)
                    i = j + 1
                    continue
        res.extend(parts[i:j + 1])
        i = j + 1
    return '{n}'.join(res), changed


def main(tr_path, jp_path, *flags):
    jp = validar.parse(jp_path)
    text = pathlib.Path(tr_path).read_text(encoding='utf-8')
    out, total, msgs = [], 0, []
    blocks = re.split(r'(^#### [0-9A-Fa-f]+.*$)', text, flags=re.M)
    for k in range(len(blocks)):
        b = blocks[k]
        if k % 2 == 0 and k > 0:
            mid = int(re.match(r'#### ([0-9A-Fa-f]+)', blocks[k - 1]).group(1), 16)
            limit = max(validar.BATTLE_LINE if mid in validar.BATTLE_MSGS else validar.MAX_LINE,
                        jp_width(jp.get(mid, '')))
            body, trail = b.rstrip('\n'), b[len(b.rstrip('\n')):]
            new, ch = process(body, limit)
            if ch:
                total += ch
                msgs.append((mid, body, new))
                # volta a pôr uma linha física por {n}
                # uma linha física por {n} e depois de cada {w} (como no resto do ficheiro)
                new = re.sub(r'\{w\}(?!\{n\}|$)', '{w}\n', new.lstrip('\n'))
                b = '\n' + new.replace('{n}', '{n}\n') + trail
        out.append(b)
    for mid, old, new in msgs[:15]:
        print(f'--- {mid:04X}\n  antes: {old.replace(chr(10), "")}\n  depois: {new}')
    print(f'{len(msgs)} mensagens, {total} linhas a menos')
    if '--aplicar' in flags:
        pathlib.Path(tr_path).write_text(''.join(out), encoding='utf-8')
        print('aplicado')


if __name__ == '__main__':
    main(*sys.argv[1:])
