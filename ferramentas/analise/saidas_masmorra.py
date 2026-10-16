"""Mapa da masmorra com as saídas coloridas: azul-claro = escadas que sobem, laranja = escadas que descem.

Uso: python saidas_masmorra.py <rom> <wram.bin> <saída.png>
Só conta como escadas os blocos de escada raros (aparecem <= 6 vezes no mapa). Zona alcançável a partir do
jogador em cinzento claro; zonas separadas em cinzento médio. Estátuas de Nauthiz: rosa (estátua) e verde (onde ficar).
"""
import sys, zlib, struct, collections

UP = {0x066, 0x076}
DOWN = {0x01B, 0x02B, 0x010, 0x011, 0x053, 0x054, 0x05B}
ESTATUAS = {0x94: [(23, 73), (55, 89)], 0x95: [(7, 8), (7, 89)], 0x97: [(8, 55), (40, 39)],
            0x98: [(56, 10), (8, 71)], 0x99: [(119, 8)]}


def main(rom_path, wram_path, out):
    r = open(rom_path, 'rb').read(); w = open(wram_path, 'rb').read()
    rd = lambda a: r[a - 0x8000] | r[a - 0x8000 + 1] << 8
    rowtab = [rd(0xA28D + 2 * i) for i in range(8)]; coltab = [rd(0xA1F5 + 2 * i) for i in range(8)]
    def cell(cx, cy):
        a = (0x8000 + rowtab[cy >> 4] + coltab[cx >> 4] + (cy & 15) * 0x20 + (cx & 15) * 2) & 0xFFFF
        return w[0x10000 + a] | w[0x10000 + a + 1] << 8
    N = 128; grid = [[cell(x, y) for x in range(N)] for y in range(N)]
    floor = lambda x, y: 0 <= x < N and 0 <= y < N and grid[y][x] != 0 and w[0x8000 + (grid[y][x] & 0xFF)] == 0
    start = ((w[0x1070] | w[0x1071] << 8) >> 4, (w[0x1072] | w[0x1073] << 8) >> 4)
    mapa = w[0x910]
    seen = {start}; q = collections.deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and floor(*n): seen.add(n); q.append(n)
    cnt = collections.Counter(v for row in grid for v in row if v)
    stairs = [(x, y, 'sobe' if grid[y][x] in UP else 'desce') for y in range(N) for x in range(N)
              if grid[y][x] in UP | DOWN and cnt[grid[y][x]] <= 6]
    print(f'mapa ${mapa:02X}; tu: sala {start[0] // 16 + 1},{start[1] // 16 + 1}')
    for x, y, k in stairs:
        if grid[y][x] in (0x066, 0x01B, 0x010, 0x05B):
            near = any((x + dx, y + dy) in seen for dx in (-1, 0, 1) for dy in (-1, 0, 1, 2))
            print(f'  escadas que {k}m: sala {x // 16 + 1},{y // 16 + 1}', '' if near else '(noutra zona)')
    used = [(x, y) for y in range(N) for x in range(N) if grid[y][x]]
    X1 = (max(x for x, _ in used) // 16 + 1) * 16; Y1 = (max(y for _, y in used) // 16 + 1) * 16
    S = 8 if X1 <= 96 else 6
    img = [[(0, 0, 0)] * (X1 * S) for _ in range(Y1 * S)]
    def put(x, y, c, m=0):
        for yy in range(-m, S + m):
            for xx in range(-m, S + m):
                X, Y = x * S + xx, y * S + yy
                if 0 <= X < X1 * S and 0 <= Y < Y1 * S: img[Y][X] = c
    for y in range(Y1):
        for x in range(X1):
            v = grid[y][x]
            put(x, y, (0, 0, 0) if v == 0 else ((90, 90, 90) if w[0x8000 + (v & 0xFF)] else
                ((215, 215, 215) if (x, y) in seen else (150, 150, 150))))
    for y in range(Y1 * S):
        for x in range(X1 * S):
            if (x % (16 * S) == 0 or y % (16 * S) == 0) and img[y][x] == (0, 0, 0): img[y][x] = (60, 60, 140)
    for x, y, k in stairs: put(x, y, (40, 200, 230) if k == 'sobe' else (250, 140, 30), 2)
    for x, y in ESTATUAS.get(mapa, []): put(x, y - 1, (230, 40, 200), S); put(x, y, (40, 200, 60), 2)
    put(*start, (40, 120, 255), 4)
    raw = b''.join(b'\x00' + bytes(c for p in row for c in p) for row in img)
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', X1 * S, Y1 * S, 8, 2, 0, 0, 0))
                          + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b''))

if __name__ == '__main__':
    main(*sys.argv[1:])
