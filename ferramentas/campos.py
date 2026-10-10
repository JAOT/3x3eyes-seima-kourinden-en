"""Campos de texto de largura fixa (locais, sim/não...).

  python campos.py modelo <rom japonesa> <saída.tsv>        -> lista os campos das tabelas de locais
  python campos.py gerar  <rom japonesa> <campos_en.tsv> <pasta>   -> gera gerado/campos.asm

Formato do TSV: endereço SNES <TAB> tamanho (bytes) <TAB> japonês <TAB> inglês
O japonês (sem os espaços das pontas) serve de verificação contra a ROM.
O inglês é escrito em ASCII (meia largura) e centrado com espaços de largura inteira,
por isso cabe sempre: no máximo tantas letras como bytes do campo.
"""
import sys, pathlib

MAIN = ("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミ"
        "ムメモヤユヨワンラリルレロッャュョァィゥェォガギグゲゴザジズゼゾ"
        "ダヂヅデドバビブベボパピプペポヴあいうえおかきくけこさしすせそた"
        "ちつてとなにぬねのはひふへほまみむめもやゆよわをんらりるれろっゃ"
        "ゅょぁぃぅぇぉがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
        "精神体力三只眼鍵書殿像港魔術　ー／＋・")
HALF = "0123456789MFB_「」、。！？″"          # $B4.. ('_' = espaço de meia largura $C1)
FULL_SPACE, HALF_SPACE = 0xAF, 0xC1
# listas de locais no banco $0C: (início SNES, tamanho do campo)
LISTS = [(0x0CCD9E, 12), (0x0CCF1B, 12)]
# Locais com nome mais comprido do que o campo: o campo fica com FF 2E ll hh bb ("saltar para",
# ver hack.asm) e o nome, centrado com espaços ASCII, vai para LONG_BASE. Só para as listas de locais,
# que são lidas pelo motor de texto (/E6AE).
LONG_BASE = 0x30C000
LONG_MAX = 20


def lorom(snes):
    return (snes >> 16 & 0x7F) * 0x8000 + (snes & 0xFFFF) - 0x8000


def decode(b):
    out = ''
    for c in b:
        if 1 <= c <= len(MAIN):
            out += MAIN[c - 1]
        elif 0xB4 <= c < 0xB4 + len(HALF):
            out += HALF[c - 0xB4]
        else:
            out += f'[{c:02X}]'
    return out


def trimmed(b):
    b = bytes(b)
    while b and b[0] in (FULL_SPACE, HALF_SPACE):
        b = b[1:]
    while b and b[-1] in (FULL_SPACE, HALF_SPACE):
        b = b[:-1]
    return decode(b)


def modelo(rom_path, out):
    rom = pathlib.Path(rom_path).read_bytes()
    lines = ['# endereço\ttamanho\tjaponês\tinglês']
    for start, size in LISTS:
        a = start
        while True:
            f = rom[lorom(a):lorom(a) + size]
            if 0 in f or any(c > 0xCC for c in f):
                break
            lines.append(f'{a >> 16:02X}:{a & 0xFFFF:04X}\t{size}\t{trimmed(f)}\t')
            a += size
    pathlib.Path(out).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{len(lines) - 1} campos -> {out}')


def centred(en, size):
    """ASCII centrado num campo de 'size' bytes cuja largura original é 16*size px."""
    k = len(en)
    left = max(0, min(size - k, round(size / 2 - k / 4)))
    return bytes([FULL_SPACE] * left) + en.encode('ascii') + bytes([FULL_SPACE] * (size - k - left))


def gerar(rom_path, tsv, outdir):
    rom = pathlib.Path(rom_path).read_bytes()
    lines = ['; gerado por campos.py a partir de campos_en.tsv - não editar']
    longs = bytearray()
    n = 0
    for line in pathlib.Path(tsv).read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        addr, size, jp, en, align = (line.split('\t') + ['', ''])[:5]
        if not en:
            continue                                   # ainda por traduzir
        bank, off = addr.split(':')
        snes = int(bank, 16) << 16 | int(off, 16)
        size = int(size)
        field = rom[lorom(snes):lorom(snes) + size]
        assert trimmed(field) == jp, f'{addr}: a ROM tem "{trimmed(field)}", não "{jp}"'
        is_loc = any(s <= snes < s + 0x900 for s, _ in LISTS)
        limit = LONG_MAX if is_loc else size
        assert len(en) <= limit and all(0x20 <= ord(c) <= 0x7E for c in en), f'{addr}: "{en}" (máx. {limit} letras ASCII)'
        if len(en) > size:
            ptr = LONG_BASE + len(longs)
            longs += (' ' * max(0, round(size - len(en) / 2)) + en).encode('ascii') + b'\x00'
            data = bytes([0xFF, 0x2E, ptr & 0xFF, ptr >> 8 & 0xFF, ptr >> 16])
        elif align.strip() == 'esq':
            data = en.encode('ascii') + bytes([HALF_SPACE] * (size - len(en)))
        else:
            data = centred(en, size)
        lines.append(f'org ${snes:06X} : db ' + ','.join(f'${b:02X}' for b in data) + f'   ; {jp} -> {en}')
        n += 1
    if longs:
        assert len(longs) <= 0x4000, 'locais longos: mais de 16 KB'
        lines.append(f'org ${LONG_BASE:06X}')
        for k in range(0, len(longs), 32):
            lines.append('    db ' + ','.join(f'${b:02X}' for b in longs[k:k + 32]))
    out = pathlib.Path(outdir) / 'campos.asm'
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{n} campos -> {out}')


if __name__ == '__main__':
    {'modelo': modelo, 'gerar': gerar}[sys.argv[1]](*sys.argv[2:])
