"""Grava a fonte inglesa dentro da fonte de diálogo comprimida do jogo (descritores #000 e #001).

A fonte de diálogo (512 tiles 2bpp do BG3) é carregada pelo jogo a partir dos descritores #000 e #001.
Com as letras inglesas já nesses dados, elas estão na VRAM desde o início e não aparecem kana durante
os primeiros frames de cada mensagem (antes, só o NMI as enviava, um segmento por frame).
O NMI continua a enviar a fonte, como salvaguarda para outros carregamentos.

Uso: python fonte_rom.py <rom japonesa> <pasta gerado>   (depois de fonte_en.py)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent / 'analise'))
from fonte_en import SEGMENTS
from descomprimir import decode
from intro import enc_gfx

FONT_DESCS = (0x000, 0x001)
DATA_ROM = 0x188000            # $31:8000; um banco de 32 KB por descritor


def main(rom_path, outdir):
    rom = pathlib.Path(rom_path).read_bytes()
    out = pathlib.Path(outdir)
    font = (out / 'font_en.bin').read_bytes()
    asm = ['; gerado por fonte_rom.py - não editar']
    for k, idx in enumerate(FONT_DESCS):
        chars = bytearray(decode(rom, idx)[3])
        assert len(chars) == 512 * 16, f'#{idx:03X}: esperava 512 tiles'
        pos = 0
        for first, n in SEGMENTS:                      # font_en.bin está pela ordem dos segmentos
            chars[first * 16:(first + n) * 16] = font[pos:pos + n * 16]
            pos += n * 16
        assert pos == len(font)
        blob = enc_gfx([bytes(chars[t * 16:t * 16 + 16]) for t in range(512)])
        assert decode_blob_ok(blob, chars)
        off = DATA_ROM + k * 0x8000
        assert len(blob) <= 0x8000
        name = f'fonte_{idx:03X}.bin'
        (out / name).write_bytes(blob)
        snes = ((off // 0x8000) << 16) | 0x8000
        asm.append(f'org ${snes:06X} : incbin "{name}"')
        asm.append(f'org ${0x028000 + idx * 6:06X} : dl ${snes:06X}')
    (out / 'fonte_rom.asm').write_text('\n'.join(asm) + '\n', encoding='utf-8')
    print(f'fonte de diálogo com letras inglesas: descritores {", ".join(f"#{i:03X}" for i in FONT_DESCS)}')


def decode_blob_ok(blob, expected):
    """Confere com o descompressor de análise, gravando o blob numa ROM fictícia."""
    from descomprimir import gfx
    fake = bytearray(0x10000)
    fake[0x8000:0x8000 + len(blob)] = blob
    return bytes(gfx(bytes(fake), 0x8000)) == bytes(expected)


if __name__ == '__main__':
    main(*sys.argv[1:3])
