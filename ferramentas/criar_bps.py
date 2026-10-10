"""Cria um patch BPS (formato beat) entre a ROM original e a ROM traduzida, e verifica-o.

Uso: python criar_bps.py <rom original> <rom traduzida> <saída.bps>

Codificador linear simples: SourceRead onde os bytes são iguais, TargetCopy para sequências
repetidas (ex.: zeros da expansão), TargetRead para o resto. Depois aplica o patch à ROM
original e confirma que o resultado é igual à ROM traduzida.
"""
import sys, zlib, pathlib

SOURCE_READ, TARGET_READ, SOURCE_COPY, TARGET_COPY = range(4)


def num(n):
    out = bytearray()
    while True:
        x = n & 0x7F
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            return out
        out.append(x)
        n -= 1


def create(src, dst, meta=b''):
    out = bytearray(b'BPS1') + num(len(src)) + num(len(dst)) + num(len(meta)) + meta
    i, n, trel = 0, len(dst), 0
    lit = bytearray()

    def flush():
        nonlocal lit
        if lit:
            out.extend(num(((len(lit) - 1) << 2) | TARGET_READ) + lit)
            lit = bytearray()

    while i < n:
        # bytes iguais à origem na mesma posição
        k = i
        while k < n and k < len(src) and dst[k] == src[k]:
            k += 1
        if k - i >= 4:
            flush()
            out.extend(num(((k - i - 1) << 2) | SOURCE_READ))
            i = k
            continue
        # sequência de bytes repetidos: 1 literal + TargetCopy sobre si próprio
        k = i + 1
        while k < n and dst[k] == dst[i]:
            k += 1
        if k - i >= 16:
            lit.append(dst[i])
            flush()
            off = i - trel
            out.extend(num(((k - i - 2) << 2) | TARGET_COPY) + num((abs(off) << 1) | (off < 0)))
            trel = k - 1
            i = k
            continue
        lit.append(dst[i])
        i += 1
    flush()
    out += zlib.crc32(src).to_bytes(4, 'little') + zlib.crc32(dst).to_bytes(4, 'little')
    out += zlib.crc32(out).to_bytes(4, 'little')
    return bytes(out)


def apply(src, patch):
    p = 4
    assert patch[:4] == b'BPS1'

    def rd():
        nonlocal p
        data, shift = 0, 1
        while True:
            x = patch[p]; p += 1
            data += (x & 0x7F) * shift
            if x & 0x80:
                return data
            shift <<= 7
            data += shift
    ssize, tsize, msize = rd(), rd(), rd()
    p += msize
    out = bytearray()
    srel = trel = 0
    end = len(patch) - 12
    while p < end:
        d = rd()
        cmd, length = d & 3, (d >> 2) + 1
        if cmd == SOURCE_READ:
            out += src[len(out):len(out) + length]
        elif cmd == TARGET_READ:
            out += patch[p:p + length]; p += length
        else:
            d = rd()
            off = -(d >> 1) if d & 1 else d >> 1
            if cmd == SOURCE_COPY:
                srel += off
                out += src[srel:srel + length]; srel += length
            else:
                trel += off
                for _ in range(length):
                    out.append(out[trel]); trel += 1
    assert len(out) == tsize and zlib.crc32(out) == int.from_bytes(patch[-8:-4], 'little')
    return bytes(out)


def main(src_path, dst_path, out_path):
    src = pathlib.Path(src_path).read_bytes()
    if len(src) % 0x8000 == 512:
        src = src[512:]
    dst = pathlib.Path(dst_path).read_bytes()
    patch = create(src, dst)
    assert apply(src, patch) == dst, 'o patch não reproduz a ROM traduzida'
    pathlib.Path(out_path).write_bytes(patch)
    print(f'{out_path}: {len(patch)} bytes; origem CRC32 {zlib.crc32(src):08X}, '
          f'resultado CRC32 {zlib.crc32(dst):08X} (verificado)')


if __name__ == '__main__':
    main(*sys.argv[1:4])
