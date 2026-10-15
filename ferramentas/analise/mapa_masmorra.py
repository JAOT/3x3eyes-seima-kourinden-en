"""Desenha o mapa da masmorra atual a partir da WRAM de um save state (extraída com mss.ps1).

Uso: python mapa_masmorra.py <rom> <wram.bin> <saída.png> [escala]

O mapa está em $7F:8000-FFFF: 8x8 ecrãs de 16x16 células (uma palavra por célula = nº do bloco);
o endereço de cada ecrã vem das tabelas $00:A28D (linhas) e $00:A1F5 (colunas), como em $00:A562.
O atributo de cada bloco está em $7E:8000 + (bloco & $FF): 0 = transitável, 1 = parede.
Cores: cinzento claro = chão; cinzento escuro = parede; preto = vazio; azul = jogador ($1070/$1072);
amarelo = blocos raros (aparecem poucas vezes: escadas, cofres, estátuas...). Imprime a lista dos raros.
"""
import sys, zlib, struct, collections

N = 128


def main(rom_path, wram_path, out, scale='4'):
    r = open(rom_path, 'rb').read()
    w = open(wram_path, 'rb').read()
    S = int(scale)
    rd = lambda a: r[a - 0x8000] | r[a - 0x8000 + 1] << 8
    rowtab = [rd(0xA28D + 2 * i) for i in range(8)]
    coltab = [rd(0xA1F5 + 2 * i) for i in range(8)]

    def cell(cx, cy):
        a = (0x8000 + rowtab[cy >> 4] + coltab[cx >> 4] + (cy & 15) * 0x20 + (cx & 15) * 2) & 0xFFFF
        return w[0x10000 + a] | w[0x10000 + a + 1] << 8

    grid = [[cell(x, y) for x in range(N)] for y in range(N)]
    wall = lambda v: w[0x8000 + (v & 0xFF)] != 0
    cnt = collections.Counter(v for row in grid for v in row if v)
    rare = {v for v, n in cnt.items() if n <= 6}
    px, py = (w[0x1070] | w[0x1071] << 8) >> 4, (w[0x1072] | w[0x1073] << 8) >> 4
    print(f'mapa nº ${w[0x910] | w[0x911] << 8:02X}; jogador na célula ({px}, {py}), ecrã ({px >> 4}, {py >> 4})')
    img = [[(0, 0, 0)] * (N * S) for _ in range(N * S)]
    for y in range(N):
        for x in range(N):
            v = grid[y][x]
            c = (0, 0, 0) if v == 0 else ((90, 90, 90) if wall(v) else (200, 200, 200))
            if v in rare:
                c = (240, 200, 40)
            for yy in range(S):
                for xx in range(S):
                    img[y * S + yy][x * S + xx] = c
    for y in range(N * S):
        for x in range(N * S):
            if (x % (16 * S) == 0 or y % (16 * S) == 0) and img[y][x] == (0, 0, 0):
                img[y][x] = (60, 60, 90)
    for yy in range(-S, 2 * S):
        for xx in range(-S, 2 * S):
            X, Y = px * S + xx, py * S + yy
            if 0 <= X < N * S and 0 <= Y < N * S:
                img[Y][X] = (40, 120, 255)
    raw = b''.join(b'\x00' + bytes(c for p in row for c in p) for row in img)
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', N * S, N * S, 8, 2, 0, 0, 0))
                          + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b''))
    for v in sorted(rare):
        cells = [(x, y) for y in range(N) for x in range(N) if grid[y][x] == v]
        print(f'bloco ${v:03X} ({"parede" if wall(v) else "chão"}): {cells[:8]}')


if __name__ == '__main__':
    main(*sys.argv[1:])
