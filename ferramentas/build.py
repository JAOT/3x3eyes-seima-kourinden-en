"""Gera a ROM em inglês a partir da ROM japonesa original.

Uso: python ferramentas/build.py "<rom original .sfc>" [saida.sfc]

Passos: copiar e expandir para 2 MB -> gerar fonte -> aplicar hack.asm (Asar) -> inserir texto.
"""
import subprocess, sys, pathlib, zlib

TOOLS = pathlib.Path(__file__).resolve().parent
ROOT = TOOLS.parent
ORIGINAL_CRC = 0xFBF3C0FF   # CRC32 da ROM japonesa (sem cabeçalho de copiadora)


def main():
    src = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / '3x3Eyes_EN.sfc'
    rom = bytearray(src.read_bytes())
    if len(rom) % 0x8000 == 512:
        rom = rom[512:]                       # remove cabeçalho de copiadora
    crc = zlib.crc32(rom)
    if crc != ORIGINAL_CRC:
        print(f'AVISO: CRC32 {crc:08X} diferente do esperado {ORIGINAL_CRC:08X}')
    assert len(rom) == 0x100000, 'esperava uma ROM de 1 MB'
    rom += bytes(0x100000)                    # expandir para 2 MB
    rom[0x7FD7] = 0x0B                        # tamanho da ROM no cabeçalho: 2 MB
    out.write_bytes(rom)

    gen = TOOLS / 'gerado'
    gen.mkdir(exist_ok=True)
    subprocess.run([sys.executable, str(TOOLS / 'fonte_en.py'), str(gen)], check=True)
    subprocess.run([sys.executable, str(TOOLS / 'fonte_rom.py'), str(src), str(gen)], check=True)
    subprocess.run([sys.executable, str(TOOLS / 'menus.py'), str(src), str(ROOT / 'menus_en.tsv'), str(gen)], check=True)
    subprocess.run([sys.executable, str(TOOLS / 'nomes.py'), str(src), str(ROOT / 'nomes_en.tsv'), str(gen)], check=True)
    subprocess.run([sys.executable, str(TOOLS / 'campos.py'), 'gerar', str(src), str(ROOT / 'campos_en.tsv'), str(gen)], check=True)
    subprocess.run([sys.executable, str(TOOLS / 'blocos.py'), str(src), str(ROOT / 'blocos_en.txt'), str(gen)], check=True)
    subprocess.run([sys.executable, str(TOOLS / 'intro.py'), str(src), str(ROOT / 'intro_en.txt'), str(gen)], check=True)
    subprocess.run([str(TOOLS / 'asar' / 'asar.exe'), '--fix-checksum=on', str(TOOLS / 'hack.asm'), str(out)], check=True)
    subprocess.run([sys.executable, str(TOOLS / 'inserir_texto.py'), str(out), str(ROOT / 'traducao_en.txt')], check=True)
    # o reinseridor muda bytes depois do Asar: voltar a corrigir o checksum
    fix_checksum(out)
    print(f'ROM gerada: {out}')


def fix_checksum(path):
    rom = bytearray(path.read_bytes())
    rom[0x7FDC:0x7FE0] = b'\xFF\xFF\x00\x00'
    s = sum(rom) & 0xFFFF
    rom[0x7FDC:0x7FE0] = bytes([~s & 0xFF, (~s >> 8) & 0xFF, s & 0xFF, s >> 8])
    path.write_bytes(rom)


if __name__ == '__main__':
    main()
