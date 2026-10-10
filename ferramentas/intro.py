"""Gera os ecrãs gráficos de texto em inglês (intro_en.txt -> gerado/intro.asm + intro.bin).

Ecrãs como a introdução, o monólogo inicial do Yakumo e as falas das cenas animadas são
desenhados com glifos próprios (um descritor de gráficos) + um mapa de tiles por página,
comprimidos nos formatos do jogo (ver analise/descomprimir.py). Os dados novos são gravados
em formatos que o descompressor original aceita sem alterações de código:
  - glifos: formato "por tile" 2bpp, todos os tiles em modo máscara cheia (bytes literais);
  - mapas: LZSS só com literais, ou formato "por tile", conforme o formato do mapa original.
Os glifos vão para os tiles $0A2-$12A da base de carateres (fora dos segmentos da fonte de diálogo).

Formato de intro_en.txt:
    @ <mapa> [glifos] [centro|orig]
    linhas...
  glifos: descritor dos glifos dessa página (por omissão 1C8)
  centro: texto centrado (por omissão); orig: começa no canto superior esquerdo do texto original

Uso: python intro.py <rom japonesa> <intro_en.txt> <pasta de saída>
"""
import re, sys, pathlib, collections
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent / 'analise'))
from fonte_en import G, glyph_rows
from descomprimir import descriptor, decode, lorom

FIRST_TILE = 0x0A2           # primeiro tile usado (tile vazio); os glifos vêm a seguir
LAST_TILE = 0x12A
DATA_ROM = 0x1C0000          # offset na ROM ($38:8000), zona livre; bancos LoROM de 32 KB
BOLD = True                  # engrossar os traços um píxel para a direita
MAX_ROWS = 12


def parse(path):
    pages = []
    for blk in re.split(r'^@ ', pathlib.Path(path).read_text(encoding='utf-8'), flags=re.M)[1:]:
        head, _, body = blk.partition('\n')
        words = head.split()
        opts = {k: int(v, 0) for k, v in (w.split('=') for w in words if '=' in w)}
        args = [w for w in words if '=' not in w]
        idx = int(args[0], 16)
        gidx = int(args[1], 16) if len(args) > 1 else 0x1C8
        mode = args[2] if len(args) > 2 else 'centro'
        lines = [l for l in body.rstrip('\n').split('\n') if not l.startswith(';')]
        while lines and not lines[-1].strip():
            lines.pop()
        pages.append((idx, gidx, mode, lines, opts))
    return pages


def colours(rom, gidx):
    """Cor da letra = a que os glifos originais usam; sombra preta (3) só na paleta conhecida (cor 2 = branco)."""
    ch = decode(rom, gidx)[3]
    h = collections.Counter()
    for t in range(len(ch) // 16):
        for y in range(8):
            a, b = ch[t * 16 + y * 2], ch[t * 16 + y * 2 + 1]
            for x in range(8):
                v = ((a >> x) & 1) | (((b >> x) & 1) << 1)
                if v:
                    h[v] += 1
    ink = h.most_common(1)[0][0]
    return ink, (3 if ink == 2 else 0)


def glyph_pixels(ch, ink, shadow):
    rows = glyph_rows(ch)
    px = [[0] * 10 for _ in range(17)]
    # negrito "inteligente": engrossa para a direita, mas não fecha os espaços de 1 píxel que
    # continuam na linha de cima ou de baixo (as "calhas" verticais do m, w, M, W).
    # Os espaços isolados (junção da haste com a barriga do b, h, p, K) são preenchidos.
    ink_at = lambda y, x: 0 <= y < 16 and 0 <= x < 8 and rows[y][x] == '#'
    gap = lambda y, x: not ink_at(y, x) and ink_at(y, x - 1) and ink_at(y, x + 1)
    keep_gap = lambda y, x: gap(y, x) and (gap(y - 1, x) or gap(y + 1, x))
    on = [[ink_at(y, x) or (BOLD and ink_at(y, x - 1) and not keep_gap(y, x)) for x in range(8)]
          for y in range(16)]
    for y in range(16):
        for x in range(8):
            if on[y][x]:
                if shadow and px[y + 1][x + 1] == 0:
                    px[y + 1][x + 1] = shadow
                px[y][x] = ink
    return [r[:8] for r in px[:16]]


def tile_2bpp(px8):
    out = bytearray()
    for r in px8:
        out.append(sum(((v & 1) << (7 - x)) for x, v in enumerate(r)))
        out.append(sum((((v >> 1) & 1) << (7 - x)) for x, v in enumerate(r)))
    return bytes(out)


def enc_gfx(units):
    """Formato por tile (modo 0, unidades de 16 bytes), todas com máscara cheia."""
    n = len(units)
    body = bytearray()
    for t in units:
        body += b'\xff\xff' + t
    modes = bytes([0xFF] * ((n + 7) // 8))          # bit 1 -> modo 1 (máscara)
    return bytes([0x00]) + n.to_bytes(2, 'little') + (5 + len(body)).to_bytes(2, 'little') + bytes(body) + modes


def enc_lzss(data, first_byte):
    out = bytearray([first_byte]) + len(data).to_bytes(2, 'little')
    for i in range(0, len(data), 8):
        chunk = data[i:i + 8]
        out.append((1 << len(chunk)) - 1)
        out += chunk
    return bytes(out)


def main(rom_path, src, outdir):
    rom = open(rom_path, 'rb').read()
    pages = parse(src)
    data = bytearray()
    asm = ['; gerado por intro.py a partir de intro_en.txt - não editar']
    ptrs = {}

    def place(blob, idx):
        nonlocal data
        off = DATA_ROM + len(data)
        if off // 0x8000 != (off + len(blob) - 1) // 0x8000:   # não atravessar bancos (32 KB)
            data += bytes(0x8000 - off % 0x8000)
            off = DATA_ROM + len(data)
        ptrs[idx] = ((off // 0x8000) << 16) | (0x8000 + off % 0x8000)
        data += blob

    by_set = collections.defaultdict(list)
    for p in pages:
        by_set[p[1]].append(p)
    total_chars = 0
    for gidx, plist in by_set.items():
        sopts = {k: v for p in plist for k, v in p[4].items()}
        ink, shadow = colours(rom, gidx)
        if 'tinta' in sopts:
            ink, shadow = sopts['tinta'], sopts.get('sombra', 0)
        first = sopts.get('base', FIRST_TILE)
        chars = sorted({c for p in plist for l in p[3] for c in l if c != ' '})
        for c in chars:
            assert c in G, f'carácter sem glifo: {c!r}'
        last = sopts.get('fim', LAST_TILE)
        assert first + 2 * len(chars) <= last, f'#{gidx:X}: demasiados carateres diferentes ({len(chars)})'
        tile_of = {c: first + 1 + 2 * k for k, c in enumerate(chars)}
        tiles = [bytes(16)]
        for c in chars:
            px = glyph_pixels(c, ink, shadow)
            tiles += [tile_2bpp(px[0:8]), tile_2bpp(px[8:16])]
        place(enc_gfx(tiles), gidx)
        _, gdst = descriptor(rom, gidx)
        asm.append(f'org ${0x028000 + gidx * 6 + 3:06X} : dl ${(gdst & 0xFF0000) | (first * 8):06X}')
        total_chars += len(chars)

        for idx, _, mode, lines, opts in plist:
            kind, src_ptr, dst, orig = decode(rom, idx)
            assert len(orig) == 2048, f'#{idx:X} não é um mapa 32x32'
            e = [orig[i] | orig[i + 1] << 8 for i in range(0, 2048, 2)]
            used = [i for i, v in enumerate(e) if v & 0x3FF]
            attr = collections.Counter(e[i] & 0xFC00 for i in used).most_common(1)[0][0]
            attr = opts.get('attr', attr)
            assert len(lines) <= MAX_ROWS, f'#{idx:X}: mais de {MAX_ROWS} linhas'
            tmap = [attr | first] * 1024
            if mode == 'orig':
                x0 = min(i % 32 for i in used)
                y0 = min(i // 32 for i in used)
                step = 3 if y0 + len(lines) * 3 <= 28 else 2
            else:
                step = 2
                y0 = (28 - len(lines) * 2) // 2
            y0 = opts.get('y', y0)
            step = opts.get('passo', step)
            for i, line in enumerate(lines):
                x = opts['x'] if 'x' in opts else x0 if mode == 'orig' else (32 - len(line)) // 2
                assert x + len(line) <= 31, f'#{idx:X}: linha demasiado comprida: {line!r}'
                for j, c in enumerate(line):
                    if c == ' ':
                        continue
                    t = tile_of[c]
                    tmap[(y0 + i * step) * 32 + x + j] = attr | t
                    tmap[(y0 + i * step + 1) * 32 + x + j] = attr | (t + 1)
            raw = b''.join(v.to_bytes(2, 'little') for v in tmap)
            if kind == 'lzss':
                blob = enc_lzss(raw, rom[lorom(src_ptr >> 16, src_ptr & 0xFFFF)])
            else:
                blob = enc_gfx([raw[k:k + 16] for k in range(0, 2048, 16)])
            place(blob, idx)

    out = pathlib.Path(outdir)
    for k in range(0, len(data), 0x8000):                      # um ficheiro por banco
        bank = (DATA_ROM + k) // 0x8000
        name = f'intro_{bank:02X}.bin'
        (out / name).write_bytes(data[k:k + 0x8000])
        asm.insert(1, f'org ${bank:02X}8000 : incbin "{name}"')
    for idx, ptr in ptrs.items():
        asm.append(f'org ${0x028000 + idx * 6:06X} : dl ${ptr:06X}')
    (out / 'intro.asm').write_text('\n'.join(asm) + '\n', encoding='utf-8')
    print(f'ecrãs gráficos: {len(pages)} páginas, {len(by_set)} conjuntos de glifos, {len(data)} bytes')


if __name__ == '__main__':
    main(*sys.argv[1:4])
