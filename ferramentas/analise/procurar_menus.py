"""Procura texto japonês por traduzir no banco $0F (menus e janelas).

Uso: python procurar_menus.py <rom japonesa> <rom inglesa>

Lista sequências de texto (kana/kanji, espaços, {02}) na ROM original cujos bytes
ainda não foram alterados na ROM inglesa.
"""
import sys

MAIN = ("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミ"
        "ムメモヤユヨワンラリルレロッャュョァィゥェォガギグゲゴザジズゼゾ"
        "ダヂヅデドバビブベボパピプペポヴあいうえおかきくけこさしすせそた"
        "ちつてとなにぬねのはひふへほまみむめもやゆよわをんらりるれろっゃ"
        "ゅょぁぃぅぇぉがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
        "精神体力三只眼鍵書殿像港魔術　ー／＋・")
HALF = "0123456789MFB_「」、。！？″"
SPACES = (0xAF, 0xC1)


def ch(c):
    if 1 <= c <= len(MAIN):
        return MAIN[c - 1]
    if 0xB4 <= c < 0xB4 + len(HALF):
        return HALF[c - 0xB4]
    return None


def runs(rom, start, end):
    i = start
    while i < end:
        j, kana, text = i, 0, ''
        while j < end:
            c = rom[j]
            if c == 0xFF and j + 1 < end and rom[j + 1] == 0x02:
                text += '{n}'; j += 2; continue
            s = ch(c)
            if s is None:
                break
            if c not in SPACES and c <= 0xB3:
                kana += 1
            text += s; j += 1
        if kana >= 2 and j - i >= 3:
            yield i, j, text
            i = j
        else:
            i += 1


def main(jp_path, en_path):
    jp = open(jp_path, 'rb').read()
    en = open(en_path, 'rb').read()
    for a, b, text in runs(jp, 0x78000, 0x80000):
        if jp[a:b] != en[a:b]:
            continue                       # já alterado
        snes = 0x8000 + a % 0x8000
        print(f'0F:{snes:04X}-{0x8000 + b % 0x8000:04X} {text}')


if __name__ == '__main__':
    main(*sys.argv[1:3])
