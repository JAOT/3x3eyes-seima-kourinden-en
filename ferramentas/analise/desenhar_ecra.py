"""Desenha um mapa de tiles (32x32, 2bpp) com um conjunto de gráficos, para pré-visualizar ecrãs.

Uso: python desenhar_ecra.py <rom> <idx_mapa> <idx_graficos> <saida.png>
(sem dependências: escreve PNG à mão)
"""
import sys, zlib, struct
sys.path.insert(0, __import__('os').path.dirname(__file__))
from descomprimir import decode


def png(path, w, h, rows):
    raw = b''.join(b'\x00' + bytes(r) for r in rows)
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    data = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 0, 0, 0, 0))
    data += chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
    open(path, 'wb').write(data)


def render(tmap, chars, scale=1):
    W = H = 256
    img = [[0] * W for _ in range(H)]
    shade = (0, 90, 170, 255)
    for ty in range(32):
        for tx in range(32):
            e = tmap[(ty * 32 + tx) * 2] | tmap[(ty * 32 + tx) * 2 + 1] << 8
            t, hf, vf = e & 0x3FF, e & 0x4000, e & 0x8000
            o = t * 16
            if o + 16 > len(chars):
                continue
            for y in range(8):
                sy = 7 - y if vf else y
                for x in range(8):
                    sx = 7 - x if hf else x
                    b = 7 - sx
                    v = ((chars[o + sy * 2] >> b) & 1) | (((chars[o + sy * 2 + 1] >> b) & 1) << 1)
                    img[ty * 8 + y][tx * 8 + x] = shade[v]
    return [[p for p in row for _ in range(scale)] for row in img for _ in range(scale)]


if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    tmap = decode(rom, int(sys.argv[2], 16))[3]
    chars = decode(rom, int(sys.argv[3], 16))[3]
    rows = render(tmap, chars)
    png(sys.argv[4], 256, 256, rows)
    print('ok')
