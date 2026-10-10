"""Gera gerado/nomes.asm a partir de nomes_en.tsv.

Feitiços, inimigos e itens estão em tabelas de registos de tamanho fixo no banco $0C,
com o nome nos primeiros 8 bytes (até 7 carateres + 0). O inglês é escrito em ASCII.

Uso: python nomes.py <rom japonesa> <nomes_en.tsv> <pasta de saída>
"""
import sys, pathlib

MAIN = ("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミ"
        "ムメモヤユヨワンラリルレロッャュョァィゥェォガギグゲゴザジズゼゾ"
        "ダヂヅデドバビブベボパピプペポヴあいうえおかきくけこさしすせそた"
        "ちつてとなにぬねのはひふへほまみむめもやゆよわをんらりるれろっゃ"
        "ゅょぁぃぅぇぉがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
        "精神体力三只眼鍵書殿像港魔術　ー／＋・")
CODE = {ch: i + 1 for i, ch in enumerate(MAIN)}
# carateres de meia largura usados em alguns nomes (dígitos, M/F/B, pontuação)
HALF = {**{str(d): 0xB4 + d for d in range(10)}, 'M': 0xBE, 'F': 0xBF, 'B': 0xC0, '！': 0xC6, '？': 0xC7}
NAME_LEN = 8
# Nomes longos: o registo fica com FF 2E ll hh bb 00 (código "saltar para", ver hack.asm) e o nome
# completo vai para LONG_BASE. Os nomes são sempre lidos pelo motor de texto, que segue o salto.
# Limite em letras (8 px cada): o japonês tinha até 8 carateres de 16 px.
LONG_MAX = {'item': 16, 'feitico': 14}
LONG_BASE = 0x308000
# tabela: (offset na ROM do primeiro registo, tamanho do registo (None = offset de uma tabela de ponteiros no banco $0C), nº de registos, terminador obrigatório)
# Os ataques dos inimigos são lidos por {08:03}, que pára aos 8 carateres: o nome pode ocupar os 8 bytes.
TABLES = {
    'feitico': (0x60F13, 0x17, 117, True),   # $0C:8F13 (ponteiros em $0C:8E29: feitiços e objetos usados em combate)
    'inimigo': (0x61996, None, 67, True),    # ponteiros em $0C:9996 (o 1.º registo está 3 bytes antes do passo de 0x26)
    'item':    (0x62FE3, 0x1E, 152, False),  # $0C:AFE3 (ponteiros em $0C:AEB3; todos lidos com máx. 8 carateres)
    'ataque':  (0x60C4D, 0x0E, 24, False),   # $0C:8C4D (ataques especiais dos inimigos)
}


def main(rom_path, tsv, outdir):
    rom = pathlib.Path(rom_path).read_bytes()
    lines = ['; gerado por nomes.py a partir de nomes_en.tsv - não editar']
    longs = bytearray()
    n = 0
    for line in pathlib.Path(tsv).read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        table, idx, jp, en = line.split('\t')
        start, size, count, term = TABLES[table]
        idx = int(idx, 0)                       # decimal ou hexadecimal (0x..)
        assert 0 <= idx < count, f'{table} {idx}: índice fora da tabela'
        off = start + idx * size if size else 0x60000 + (rom[start + 2 * idx] | rom[start + 2 * idx + 1] << 8) - 0x8000
        expected = bytes(CODE.get(c) or HALF[c] for c in jp)
        if len(expected) < NAME_LEN:
            expected += b'\x00'
        assert rom[off:off + len(expected)] == expected, f'{table} {idx}: a ROM não tem "{jp}" nesta posição'
        max_len = NAME_LEN - 1 if term else NAME_LEN
        limit = max(max_len, LONG_MAX.get(table, 0))
        assert len(en) <= limit and all(0x20 <= ord(c) <= 0x7E for c in en), f'{table} {idx}: "{en}" (máx. {limit} letras ASCII)'
        if len(en) <= max_len:
            data = en.encode('ascii').ljust(NAME_LEN, b'\x00')
        else:
            ptr = LONG_BASE + len(longs)
            longs += en.encode('ascii') + b'\x00'
            data = bytes([0xFF, 0x2E, ptr & 0xFF, ptr >> 8 & 0xFF, ptr >> 16]).ljust(NAME_LEN, b'\x00')
        snes = ((off // 0x8000) << 16) | (0x8000 + off % 0x8000)
        lines.append(f'org ${snes:06X} : db ' + ','.join(f'${b:02X}' for b in data) + f'   ; {jp} -> {en}')
        n += 1
    assert len(longs) <= 0x4000, 'nomes longos: mais de 16 KB'
    lines.append(f'org ${LONG_BASE:06X}')
    for k in range(0, len(longs), 32):
        lines.append('    db ' + ','.join(f'${b:02X}' for b in longs[k:k + 32]))
    out = pathlib.Path(outdir) / 'nomes.asm'
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{n} nomes -> {out}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
