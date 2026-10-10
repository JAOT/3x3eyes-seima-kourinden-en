"""Lista as transferências DMA (e escritas diretas na VRAM) de um trace log do Mesen.

Uso: python dma_trace.py <trace.txt>

Segue as escritas nos registos $2115-$2117 e $43x0-$43x6 e, a cada escrita em $420B,
mostra para cada canal ativo: destino (registo B), endereço VRAM, origem e tamanho.
"""
import re, sys, collections

LINE = re.compile(r'^([0-9A-F]{6})  (ST[AXYZ]) [^\[]*\[\$([0-9A-F]{6})\].*?A:([0-9A-F]{4}) X:([0-9A-F]{4}) Y:([0-9A-F]{4}).*?P:(\S+)')


def main(path):
    regs = {}
    seen = collections.OrderedDict()
    frame = re.compile(r'Fr:(\d+)')
    with open(path, encoding='latin-1') as f:
        for line in f:
            if line[6:8] != '  ':
                continue
            m = LINE.match(line)
            if not m:
                continue
            pc, op, ea, a, x, y, p = m.groups()
            ea = int(ea, 16) & 0xFFFF
            if not (0x2115 <= ea <= 0x2117 or 0x4300 <= ea <= 0x437F or ea == 0x420B):
                continue
            wide = (p[2] == 'm') if op == 'STA' else (p[3] == 'x')   # flags "nvmxdizc"
            val = {'STA': int(a, 16), 'STX': int(x, 16), 'STY': int(y, 16), 'STZ': 0}[op]
            if not wide:
                val &= 0xFF
                regs[ea] = val
            else:
                regs[ea] = val & 0xFF
                regs[ea + 1] = val >> 8
            if ea == 0x420B:
                fr = frame.search(line)
                for ch in range(8):
                    if not (val >> ch) & 1:
                        continue
                    b = 0x4300 + ch * 16
                    dest = regs.get(b + 1, 0)
                    src = regs.get(b + 2, 0) | regs.get(b + 3, 0) << 8 | regs.get(b + 4, 0) << 16
                    size = regs.get(b + 5, 0) | regs.get(b + 6, 0) << 8
                    vram = regs.get(0x2116, 0) | regs.get(0x2117, 0) << 8
                    key = (dest, vram if dest in (0x18, 0x19) else None, src, size)
                    if key not in seen:
                        seen[key] = (pc, fr.group(1) if fr else '?', 1)
                    else:
                        p0, f0, n = seen[key]
                        seen[key] = (p0, f0, n + 1)
    for (dest, vram, src, size), (pc, fr, n) in seen.items():
        v = f'VRAM ${vram:04X}' if vram is not None else '         '
        print(f'fr {fr:>6} pc {pc}  $21{dest:02X} {v}  src ${src:06X}  size ${size:04X}  x{n}')


if __name__ == '__main__':
    main(sys.argv[1])
