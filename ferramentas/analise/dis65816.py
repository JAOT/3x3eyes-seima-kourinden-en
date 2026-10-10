"""Desmontador simples de 65816 (para análise). Uso: python dis65816.py <rom> <banco:endereço> [n] [m8] [x8]
m8/x8: 1 se A/índices estiverem em 8 bits no início (REP/SEP são seguidos automaticamente)."""
import sys

MN = ("BRK ORA COP ORA TSB ORA ASL ORA PHP ORA ASL PHD TSB ORA ASL ORA "
      "BPL ORA ORA ORA TRB ORA ASL ORA CLC ORA INC TCS TRB ORA ASL ORA "
      "JSR AND JSL AND BIT AND ROL AND PLP AND ROL PLD BIT AND ROL AND "
      "BMI AND AND AND BIT AND ROL AND SEC AND DEC TSC BIT AND ROL AND "
      "RTI EOR WDM EOR MVP EOR LSR EOR PHA EOR LSR PHK JMP EOR LSR EOR "
      "BVC EOR EOR EOR MVN EOR LSR EOR CLI EOR PHY TCD JML EOR LSR EOR "
      "RTS ADC PER ADC STZ ADC ROR ADC PLA ADC ROR RTL JMP ADC ROR ADC "
      "BVS ADC ADC ADC STZ ADC ROR ADC SEI ADC PLY TDC JMP ADC ROR ADC "
      "BRA STA BRL STA STY STA STX STA DEY BIT TXA PHB STY STA STX STA "
      "BCC STA STA STA STY STA STX STA TYA STA TXS TXY STZ STA STZ STA "
      "LDY LDA LDX LDA LDY LDA LDX LDA TAY LDA TAX PLB LDY LDA LDX LDA "
      "BCS LDA LDA LDA LDY LDA LDX LDA CLV LDA TSX TYX LDY LDA LDX LDA "
      "CPY CMP REP CMP CPY CMP DEC CMP INY CMP DEX WAI CPY CMP DEC CMP "
      "BNE CMP CMP CMP PEI CMP DEC CMP CLD CMP PHX STP JML CMP DEC CMP "
      "CPX SBC SEP SBC CPX SBC INC SBC INX SBC NOP XBA CPX SBC INC SBC "
      "BEQ SBC SBC SBC PEA SBC INC SBC SED SBC PLX XCE JSR SBC INC SBC").split()
# modos por coluna (o & 0x1F), com exceções
COLMODE = ['(d,x)', 'imp', '(d,x)', 'd,s', 'd', 'd', 'd', '[d]', 'imp', '#m', 'acc', 'imp', 'a', 'a', 'a', 'al',
           'r', '(d),y', '(d)', '(d,s),y', 'd,x', 'd,x', 'd,x', '[d],y', 'imp', 'a,y', 'acc', 'imp', 'a', 'a,x', 'a,x', 'al,x']
EXC = {0x40: 'imp', 0x60: 'imp', 0x00: '#8', 0x02: '#8', 0x20: 'a', 0x22: 'al', 0x44: 'mv', 0x54: 'mv', 0x4C: 'a', 0x5C: 'al', 0x6C: '(a)',
       0x7C: '(a,x)', 0xDC: '[a]', 0xFC: '(a,x)', 0x82: 'rl', 0x62: 'rl', 0xF4: 'a', 0xD4: 'd', 0xC2: '#8', 0xE2: '#8',
       0xA0: '#x', 0xA2: '#x', 0xC0: '#x', 0xE0: '#x', 0x96: 'd,y', 0xB6: 'd,y', 0xBE: 'a,y', 0x9E: 'a,x', 0x9C: 'a',
       0x64: 'd', 0x74: 'd,x', 0x14: 'd', 0x1C: 'a', 0x04: 'd', 0x0C: 'a', 0x89: '#m', 0x34: 'd,x', 0x3C: 'a,x',
       0x80: 'r', 0x10: 'r', 0x30: 'r', 0x50: 'r', 0x70: 'r', 0x90: 'r', 0xB0: 'r', 0xD0: 'r', 0xF0: 'r'}
for o in range(256):
    if o & 0x1F in (0x01, 0x03, 0x05, 0x07, 0x09, 0x0D, 0x0F, 0x11, 0x12, 0x13, 0x15, 0x17, 0x19, 0x1D, 0x1F):
        pass
SIZE = {'imp': 0, 'acc': 0, 'd': 1, 'd,x': 1, 'd,y': 1, 'd,s': 1, '(d,x)': 1, '(d)': 1, '(d),y': 1, '[d]': 1,
        '[d],y': 1, '(d,s),y': 1, 'a': 2, 'a,x': 2, 'a,y': 2, '(a)': 2, '(a,x)': 2, '[a]': 2, 'al': 3, 'al,x': 3,
        'r': 1, 'rl': 2, 'mv': 2, '#8': 1}


def mode(op):
    if op in EXC:
        return EXC[op]
    c = op & 0x1F
    m = COLMODE[c]
    if c in (0x0A,) and op >= 0x80:
        return 'imp'
    if c == 0x08 or c == 0x18 or c == 0x1B or c == 0x0B or c == 0x1A:
        return 'imp'
    if c in (0x04, 0x0C, 0x14, 0x1C, 0x00, 0x06, 0x0E, 0x16, 0x1E, 0x02):
        return {0x04: 'd', 0x0C: 'a', 0x14: 'd,x', 0x1C: 'a,x', 0x00: '#x', 0x06: 'd', 0x0E: 'a', 0x16: 'd,x',
                0x1E: 'a,x', 0x02: '#8'}[c]
    return m


def lorom(b, a):
    return (b & 0x7F) * 0x8000 + (a & 0x7FFF)


def main(rom_path, start, n='40', m8='0', x8='0'):
    rom = open(rom_path, 'rb').read()
    b, a = (int(v, 16) for v in start.split(':'))
    m8, x8 = m8 == '1', x8 == '1'
    for _ in range(int(n)):
        p = lorom(b, a)
        op = rom[p]
        md = mode(op)
        if md == '#m':
            sz = 1 if m8 else 2
        elif md == '#x':
            sz = 1 if x8 else 2
        else:
            sz = SIZE[md]
        arg = int.from_bytes(rom[p + 1:p + 1 + sz], 'little')
        if md == 'r':
            txt = f'${(a + 2 + (arg - 256 if arg > 127 else arg)) & 0xFFFF:04X}'
        elif md == 'rl':
            txt = f'${(a + 3 + (arg - 65536 if arg > 32767 else arg)) & 0xFFFF:04X}'
        elif md in ('imp', 'acc'):
            txt = ''
        elif md == 'mv':
            txt = f'${rom[p+1]:02X},${rom[p+2]:02X}'
        elif md.startswith('#'):
            txt = f'#${arg:0{sz*2}X}'
        else:
            txt = md.replace('al', f'${arg:06X}').replace('a', f'${arg:04X}').replace('d', f'${arg:02X}')
        print(f'{b:02X}:{a:04X}  {rom[p:p+1+sz].hex(" "):12} {MN[op]} {txt}')
        if op == 0xC2:
            m8 = m8 and not arg & 0x20; x8 = x8 and not arg & 0x10
        if op == 0xE2:
            m8 = m8 or bool(arg & 0x20); x8 = x8 or bool(arg & 0x10)
        a += 1 + sz


if __name__ == '__main__':
    main(*sys.argv[1:])
