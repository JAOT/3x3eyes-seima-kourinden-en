"""Gera gerado/menus.asm a partir de menus_en.tsv.

Os menus do banco $0F têm posições fixas: cada carácter japonês ocupa 16 px.
Para não mudar o tamanho dos blocos, cada carácter é trocado por um código que
desenha DUAS letras inglesas (8 px cada), reutilizando os tiles da fonte inglesa.
Os códigos usados para os pares são katakana que deixam de ser necessários.

Uso: python menus.py <rom japonesa> <menus_en.tsv> <pasta de saída>
"""
import sys, pathlib

MAIN = ("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミ"
        "ムメモヤユヨワンラリルレロッャュョァィゥェォガギグゲゴザジズゼゾ"
        "ダヂヅデドバビブベボパピプペポヴあいうえおかきくけこさしすせそた"
        "ちつてとなにぬねのはひふへほまみむめもやゆよわをんらりるれろっゃ"
        "ゅょぁぃぅぇぉがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
        "精神体力三只眼鍵書殿像港魔術　ー／＋・")
CODE = {ch: i + 1 for i, ch in enumerate(MAIN)}
SPACE = CODE['　']                       # $AF: espaço de largura inteira
# katakana ア..ミ e hiragana ゅ..ぽ (os bytes $20-$7E já são ASCII; $A1-$A4 são Body/Mind)
PAIR_CODES = list(range(0x01, 0x20)) + list(range(0x80, 0xA0))
REGION = (0x78000, 0x80000)              # banco $0F


def load(tsv):
    rows = []
    for line in pathlib.Path(tsv).read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        jp, en, addr = (line.split('\t') + [''])[:3]
        if len(en) > 2 * len(jp):
            raise ValueError(f'"{en}" não cabe em "{jp}" (máx. {2 * len(jp)} letras)')
        rows.append((jp, en.ljust(2 * len(jp)), addr.strip()))
    return rows


def main(rom_path, tsv, outdir):
    rom = pathlib.Path(rom_path).read_bytes()
    pairs = {}                              # "Le" -> código
    patches = []                            # (offset, bytes)
    for jp, en, addr in load(tsv):
        src = bytes(CODE[c] for c in jp)
        dst = bytearray()
        for k in range(0, len(en), 2):
            pair = en[k:k + 2]
            if pair == '  ':
                dst.append(SPACE)
                continue
            if pair not in pairs:
                if len(pairs) >= len(PAIR_CODES):
                    raise RuntimeError('sem códigos livres para mais pares de letras')
                pairs[pair] = PAIR_CODES[len(pairs)]
            dst.append(pairs[pair])
        hits = 0
        if addr:                            # endereço fixo (ex.: "0C:CF0B"), fora do banco $0F
            bank, off = addr.split(':')
            i = int(bank, 16) * 0x8000 + int(off, 16) - 0x8000
            assert rom[i:i + len(src)] == src, f'{addr}: a ROM não tem "{jp}"'
            patches.append((i, bytes(dst)))
            hits = 1
        else:
            i = rom.find(src, *REGION)
            while i >= 0:
                patches.append((i, bytes(dst)))
                hits += 1
                i = rom.find(src, i + 1, REGION[1])
        print(f'{jp} -> {en.rstrip()!r}: {hits} ocorrência(s)')
    lines = ['; gerado por menus.py a partir de menus_en.tsv - não editar', '']
    for pair, code in sorted(pairs.items(), key=lambda kv: kv[1]):
        a, b = (f'{ord(ch):02X}' for ch in pair)
        lines.append(f'%wide(${code:02X}, {a}, {b})   ; {pair!r}')
    lines.append('')
    for off, data in patches:
        snes = ((off // 0x8000) << 16) | (0x8000 + off % 0x8000)
        lines.append(f'org ${snes:06X} : db ' + ','.join(f'${b:02X}' for b in data))
    out = pathlib.Path(outdir) / 'menus.asm'
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{len(pairs)} pares de letras, {len(patches)} rótulos substituídos -> {out}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
