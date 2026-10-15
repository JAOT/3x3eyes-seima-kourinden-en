"""Caminho mais curto na masmorra atual (save state) e desenho do mapa com o caminho.

Uso: python caminho_masmorra.py <rom> <wram.bin> <saída.png> <x,y destino> [x,y origem] [escala] [largura em células]
A origem por omissão é a posição do jogador. Imprime o caminho em segmentos (direção, nº de células).
"""
import sys, zlib, struct, collections

def main(rom_path, wram_path, out, goal, start=None, scale='8', size='64'):
    r = open(rom_path, 'rb').read(); w = open(wram_path, 'rb').read()
    S, N = int(scale), int(size)
    rd = lambda a: r[a - 0x8000] | r[a - 0x8000 + 1] << 8
    rowtab = [rd(0xA28D + 2 * i) for i in range(8)]; coltab = [rd(0xA1F5 + 2 * i) for i in range(8)]
    def cell(cx, cy):
        a = (0x8000 + rowtab[cy >> 4] + coltab[cx >> 4] + (cy & 15) * 0x20 + (cx & 15) * 2) & 0xFFFF
        return w[0x10000 + a] | w[0x10000 + a + 1] << 8
    floor = lambda x, y: 0 <= x < N and 0 <= y < N and cell(x, y) != 0 and w[0x8000 + (cell(x, y) & 0xFF)] == 0
    if start in (None, '-'):
        start = ((w[0x1070] | w[0x1071] << 8) >> 4, (w[0x1072] | w[0x1073] << 8) >> 4)
    else:
        start = tuple(int(v) for v in start.split(','))
    goal = tuple(int(v) for v in goal.split(','))
    prev = {start: None}; q = collections.deque([start])
    while q:
        p = q.popleft()
        if p == goal: break
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            n = (p[0] + dx, p[1] + dy)
            if n not in prev and floor(*n):
                prev[n] = p; q.append(n)
    if goal not in prev:
        print('destino inalcançável'); return
    path = []; p = goal
    while p: path.append(p); p = prev[p]
    path.reverse()
    names = {(1, 0): 'direita', (-1, 0): 'esquerda', (0, 1): 'baixo', (0, -1): 'cima'}
    segs = []
    for a, b in zip(path, path[1:]):
        d = names[(b[0] - a[0], b[1] - a[1])]
        if segs and segs[-1][0] == d: segs[-1][1] += 1
        else: segs.append([d, 1])
    print(f'{len(path) - 1} passos:', ', '.join(f'{d} {n}' for d, n in segs))
    img = [[(0, 0, 0)] * (N * S) for _ in range(N * S)]
    for y in range(N):
        for x in range(N):
            v = cell(x, y)
            c = (0, 0, 0) if v == 0 else ((200, 200, 200) if floor(x, y) else (90, 90, 90))
            if (x, y) in set(path): c = (230, 60, 40)
            if (x, y) == start: c = (40, 120, 255)
            if (x, y) == goal: c = (40, 200, 60)
            for yy in range(S):
                for xx in range(S): img[y * S + yy][x * S + xx] = c
    for y in range(N * S):
        for x in range(N * S):
            if x % (16 * S) == 0 or y % (16 * S) == 0: img[y][x] = (60, 60, 140)
    raw = b''.join(b'\x00' + bytes(c for p in row for c in p) for row in img)
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', N * S, N * S, 8, 2, 0, 0, 0))
                          + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b''))

if __name__ == '__main__':
    main(*sys.argv[1:])
