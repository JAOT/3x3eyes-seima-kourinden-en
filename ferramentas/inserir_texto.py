"""Insere o guião traduzido na ROM (já expandida e com hack.asm aplicado).

Formato de entrada (igual a guiao_jp.txt):
    #### 0240 ...            <- número da mensagem (hex); o resto da linha é ignorado
    {clr}{05:03}Ah! Yakumo?{w}
    {n}
    ...

- ASCII $20-$7E é escrito tal como está (fonte inglesa de meia largura).
- Etiquetas: {n} {w} {clr} {fim} {XX} {XX:YY} {XX:YY:ZZ} -> FF XX [parâmetros]
- [XX] -> byte literal; carateres japoneses -> código original (tabela do extrator).
- Quebras de linha no ficheiro são ignoradas (só as etiquetas contam).
Só as mensagens presentes no ficheiro são reapontadas; as outras ficam como estão.
"""
import re, sys, pathlib

PTR_TABLE = 0x68000
MSG_COUNT = 0x1078
TEXT_START = 0x110000          # $22:8000
TEXT_END = 0x200000
MAX_LINE = 21                  # caracteres por linha (confirmado no Mesen: ~21-22)

MAIN = ("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミ"
        "ムメモヤユヨワンラリルレロッャュョァィゥェォガギグゲゴザジズゼゾ"
        "ダヂヅデドバビブベボパピプペポヴあいうえおかきくけこさしすせそた"
        "ちつてとなにぬねのはひふへほまみむめもやゆよわをんらりるれろっゃ"
        "ゅょぁぃぅぇぉがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
        "精神体力三只眼鍵書殿像港魔術　ー／＋・")
HALF = "0123456789MFB 「」、。！？″◀▶◁▷"
JP = {ch: i + 1 for i, ch in enumerate(MAIN)}
JP.update({ch: 0xB4 + i for i, ch in enumerate(HALF) if ch not in '0123456789MFB '})
NAMED = {'n': [0xFF, 0x02], 'w': [0xFF, 0x04], 'clr': [0xFF, 0x01], 'fim': [0xFF, 0x00]}
TOKEN = re.compile(r'\{([^}]*)\}|\[([0-9A-Fa-f]{2})\]|(.)', re.S)


def encode(text, msg_id, warn):
    out = bytearray()
    line = 0
    for tag, raw, ch in TOKEN.findall(text):
        if tag:
            if tag in NAMED:
                out += bytes(NAMED[tag])
                if tag in ('n', 'w', 'clr'):
                    line = 0
            else:
                parts = tag.split(':')
                out += bytes([0xFF] + [int(p, 16) for p in parts])
        elif raw:
            out.append(int(raw, 16))
        elif ch in '\r\n':
            continue
        elif 0x20 <= ord(ch) <= 0x7E:
            out.append(ord(ch))
            line += 1
            if line == MAX_LINE + 1:
                warn.append(f'{msg_id:04X}: linha com mais de {MAX_LINE} carateres')
        elif ch in JP:
            out.append(JP[ch])
            line += 2
        else:
            raise ValueError(f'{msg_id:04X}: carácter sem código: {ch!r}')
    out.append(0x00)
    return bytes(out)


def parse(path):
    msgs, cur, buf = {}, None, []
    for line in pathlib.Path(path).read_text(encoding='utf-8').splitlines():
        m = re.match(r'^####\s+([0-9A-Fa-f]+)', line)
        if m:
            if cur is not None:
                msgs[cur] = '\n'.join(buf).strip('\n')
            cur, buf = int(m.group(1), 16), []
        elif cur is not None and not line.startswith(';'):
            buf.append(line)
    if cur is not None:
        msgs[cur] = '\n'.join(buf).strip('\n')
    return msgs


def lorom_addr(off):
    return ((off // 0x8000) << 16) | (0x8000 + off % 0x8000)


def insert(rom_path, script_path):
    rom = bytearray(pathlib.Path(rom_path).read_bytes())
    assert len(rom) >= TEXT_END, 'a ROM tem de estar expandida para 2 MB'
    msgs = parse(script_path)
    warn = []
    pos = TEXT_START
    for msg_id in sorted(msgs):
        assert 0 <= msg_id < MSG_COUNT, f'mensagem fora do intervalo: {msg_id:04X}'
        data = encode(msgs[msg_id], msg_id, warn)
        # o ponteiro de leitura é de 16 bits: uma mensagem não pode atravessar bancos
        if pos // 0x8000 != (pos + len(data) - 1) // 0x8000:
            pos = (pos // 0x8000 + 1) * 0x8000
        assert pos + len(data) <= TEXT_END, 'sem espaço para o texto'
        rom[pos:pos + len(data)] = data
        a = lorom_addr(pos)
        p = PTR_TABLE + msg_id * 3
        rom[p:p + 3] = bytes([a & 0xFF, (a >> 8) & 0xFF, a >> 16])
        pos += len(data)
    pathlib.Path(rom_path).write_bytes(rom)
    for w in warn:
        print('AVISO', w)
    print(f'{len(msgs)} mensagens inseridas; {pos - TEXT_START} bytes de texto')


if __name__ == '__main__':
    insert(sys.argv[1], sys.argv[2])
