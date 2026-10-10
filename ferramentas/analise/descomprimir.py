"""Descompressores dos dados gráficos do jogo (reproduzidos a partir de $00:8650-$00:89xx).

Tabela de descritores em $02:8000: entradas de 6 bytes
    [origem lo, hi, banco] [destino lo, hi, banco/flags]
  - banco de destino sem o bit 7 -> LZSS para a RAM (ex.: mapa de tiles em $7E:3000)
  - bit 7 ligado -> gráficos para a VRAM (endereço de palavra = destino)

Uso:
  python descomprimir.py <rom> lista <idx> [idx...]      mostra os descritores
  python descomprimir.py <rom> extrair <idx> <ficheiro>   grava os bytes descomprimidos
"""
import sys

def lorom(bank, addr):
    return (bank & 0x7F) * 0x8000 + (addr & 0x7FFF)


def descriptor(rom, idx):
    o = lorom(0x02, 0x8000) + idx * 6
    e = rom[o:o + 6]
    src = (e[2] << 16) | (e[1] << 8) | e[0]
    dst = (e[5] << 16) | (e[4] << 8) | e[3]
    return src, dst


def lzss(rom, off):
    """$00:8A11: byte 0 ignorado; palavra = nº de operações (grupos de 8 = w>>3, resto = w&7)."""
    w = rom[off + 1] | rom[off + 2] << 8
    groups, rest = w >> 3, w & 7
    p, out = off + 3, bytearray()
    def run(nops):
        nonlocal p
        flags = rom[p]; p += 1
        for _ in range(nops):
            bit = flags & 1; flags >>= 1
            if bit:
                out.append(rom[p]); p += 1
            else:
                b0, b1 = rom[p], rom[p + 1]; p += 1          # o 2.º byte é partilhado
                dist = ((b1 << 8 | b0) & 0x0FFF) + 1
                hi = rom[p] & 0xF0; p += 1
                if hi:
                    count = (hi >> 4) + 2
                else:
                    count = rom[p] + 0x12; p += 1
                for _ in range(count):
                    out.append(out[-dist])
    for _ in range(groups):
        run(8)
    if rest:
        run(rest)
    return bytes(out)


MASK_BYTES = (2, 4, 8)
TILE_SIZE = (0x10, 0x20, 0x40)
RAW_WORDS = (8, 0x10, 0x20)


def gfx(rom, off):
    """$00:86F2: gráficos por tile, com modo de 2 bits (ou 1 bit) num fluxo à parte."""
    mode = rom[off]
    if mode & 0x80:
        raise NotImplementedError('formato alternativo ($00:89B8)')
    ntiles = rom[off + 1] | rom[off + 2] << 8
    modes_ptr = off + (rom[off + 3] | rom[off + 4] << 8)
    p = off + 5
    kind = mode & 0x0F
    size, nmask = TILE_SIZE[kind], MASK_BYTES[kind]
    out = bytearray()
    state = {'ptr': modes_ptr, 'n': 0}

    def next_mode():
        if kind:
            if state['n'] == 4:
                state['ptr'] += 1; state['n'] = 0
            v = (rom[state['ptr']] >> (2 * state['n'])) & 3
            state['n'] += 1
            return v
        if state['n'] == 8:
            state['ptr'] += 1; state['n'] = 0
        v = (rom[state['ptr']] >> state['n']) & 1
        state['n'] += 1
        return (2, 1)[v]

    def masked():
        nonlocal p
        mask = int.from_bytes(rom[p:p + nmask], 'little'); p += nmask
        buf = bytearray(size)
        for i in range(size):
            if (mask >> i) & 1:
                buf[i] = rom[p]; p += 1
        return buf

    for _ in range(ntiles):
        m = next_mode()
        if m == 0:
            out += bytes(size)
        elif m == 1:
            out += masked()
        elif m == 2:
            buf = masked()
            planes = (0, 0x10) if kind == 1 else ((0, 0x10, 0x20, 0x30) if kind == 2 else (0,))
            for base in planes:
                for row in range(7):
                    x = base + row * 2
                    buf[x + 2] ^= buf[x]; buf[x + 3] ^= buf[x + 1]
            out += buf
        else:
            if mode < 0x10:
                n = RAW_WORDS[kind] * 2
                out += rom[p:p + n]; p += n
            else:
                buf = masked()
                n = {0: 0x0F, 1: 0x1F}.get(kind, 0x3F) if not (mode & 2) else 0xFF
                for i in range(min(n, size - 1)):
                    buf[i + 1] ^= buf[i]
                out += buf
    return bytes(out)


def decode(rom, idx):
    """O formato é escolhido pelo 1.º byte dos dados (bit 7 = LZSS, $00:89B8).
    Destino: banco com bit 7 -> VRAM, base = uma das cópias $D0-$DE (nibble baixo) + endereço."""
    src, dst = descriptor(rom, idx)
    off = lorom(src >> 16, src & 0xFFFF)
    if rom[off] & 0x80:
        return 'lzss', src, dst, lzss(rom, off)
    return 'gfx', src, dst, gfx(rom, off)


if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    if sys.argv[2] == 'lista':
        for a in sys.argv[3:]:
            idx = int(a, 16)
            kind, src, dst, data = decode(rom, idx)
            print(f'{idx:03X}: {kind:4} src ${src:06X} dst ${dst:06X} -> {len(data)} bytes')
    elif sys.argv[2] == 'extrair':
        kind, src, dst, data = decode(rom, int(sys.argv[3], 16))
        open(sys.argv[4], 'wb').write(data)
        print(kind, len(data))
