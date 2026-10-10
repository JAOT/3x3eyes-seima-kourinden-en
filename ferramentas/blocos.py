"""Gera gerado/blocos.asm a partir de blocos_en.txt.

Cada bloco substitui o texto entre dois endereços (fim exclusivo) por texto novo, sem limite
de tamanho: no início do bloco original fica um salto (FF 2E + endereço) para o texto novo,
escrito no banco $21, que termina com um salto de volta para o fim do bloco original.

Formato de blocos_en.txt:
    @ 0F:9906 0F:991A
    　Weapon{n}
    　Body{n}
    ...
As quebras de linha do ficheiro são ignoradas; usar {n} para mudar de linha no jogo.
O bloco original tem de ter pelo menos 5 bytes (tamanho do salto).

Uso: python blocos.py <rom japonesa> <blocos_en.txt> <pasta de saída>
"""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from inserir_texto import encode

BASE = 0x219000        # zona livre no banco $21 (a fonte ocupa $21:8000-$21:8BE0)


def parse_addr(s):
    bank, off = s.split(':')
    return int(bank, 16) << 16 | int(off, 16)


def main(rom_path, src, outdir):
    blocks, cur = [], None
    for line in pathlib.Path(src).read_text(encoding='utf-8').splitlines():
        if line.startswith(';') or not line.strip() and cur is None:
            continue
        m = re.match(r'^@\s+(\S+)\s+(\S+)', line)
        if m:
            cur = [parse_addr(m.group(1)), parse_addr(m.group(2)), []]
            blocks.append(cur)
        elif cur is not None:
            cur[2].append(line)
    lines = ['; gerado por blocos.py a partir de blocos_en.txt - não editar']
    data_lines = [f'org ${BASE:06X}']
    for k, (start, end, text) in enumerate(blocks):
        assert end - start >= 5, f'bloco em ${start:06X}: precisa de pelo menos 5 bytes'
        assert start >> 16 == end >> 16, 'o bloco não pode atravessar bancos'
        warn = []
        data = encode(''.join(text), k, warn)[:-1]          # sem o 00 final
        lines.append(f'org ${start:06X} : db $FF,$2E : dl Bloco{k}')
        data_lines.append(f'Bloco{k}:   ; ${start:06X}-${end:06X}')
        data_lines.append('    db ' + ','.join(f'${b:02X}' for b in data) + f',$FF,$2E : dl ${end:06X}')
    data_lines.append('assert pc() <= $21FFFF')
    out = pathlib.Path(outdir) / 'blocos.asm'
    out.write_text('\n'.join(lines + data_lines) + '\n', encoding='utf-8')
    print(f'{len(blocks)} blocos -> {out}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
