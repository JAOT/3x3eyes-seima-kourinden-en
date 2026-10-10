"""Livros e textos de objetos lidos no menu (Atlas, Pyramid Book, livros de talismãs...).

Não estão na tabela principal do guião: a rotina $00:CF79 lê o livro nº $060E da tabela $0E:8000
(10 ponteiros de 3 bytes). Cada livro: [nº de páginas] + ponteiros de 3 bytes para as páginas;
cada página é texto normal (passa pelo motor de texto) e acaba em FF 0B.

  python livros.py extrair <rom japonesa> <livros_jp.txt>      -> texto japonês, para referência (não vai para o git)
  python livros.py gerar   <rom japonesa> <livros_en.txt> <pasta gerado>   -> gerado/livros.asm + livros.bin

Formato: "@ livro N" e, dentro, "--- página" antes de cada página. Livros que não estejam no ficheiro
ficam em japonês. Linhas até 24 carateres, até 8 linhas por página.
"""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import inserir_texto

TABLE = 0x70000            # $0E:8000
BOOKS = 10
DATA_ROM = 0x198000        # $33:8000
MAX_LINE, MAX_LINES = 24, 8
PARAMS = [0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,
          0, 1, 1, 0, 0, 2, 2, 2, 3, 3, 3, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1]


def lorom(p):
    return (p >> 16 & 0x7F) * 0x8000 + (p & 0xFFFF) - 0x8000


def ptr3(rom, off):
    return rom[off] | rom[off + 1] << 8 | rom[off + 2] << 16


def pages(rom, book):
    head = lorom(ptr3(rom, TABLE + 3 * book))
    return [lorom(ptr3(rom, head + 1 + 3 * k)) for k in range(rom[head])]


def decode_page(rom, off):
    inv = {v: k for k, v in inserir_texto.JP.items()}
    out = ''
    while True:
        c = rom[off]; off += 1
        if c == 0xFF:
            x = rom[off]; off += 1
            if x == 0x0B:
                return out
            ps = rom[off:off + PARAMS[x]]; off += len(ps)
            out += {1: '{clr}', 2: '{n}\n', 4: '{w}'}.get(x) or '{%02X%s}' % (x, ''.join(':%02X' % p for p in ps))
        elif c in inv:
            out += inv[c]
        elif 0xB4 <= c <= 0xC0:
            out += '0123456789MFB'[c - 0xB4]
        elif c == 0xC1:
            out += ' '
        else:
            out += '[%02X]' % c


def extrair(rom_path, out_path):
    rom = pathlib.Path(rom_path).read_bytes()
    out = ['; Livros (texto japonês original, só para referência)']
    for b in range(BOOKS):
        out.append(f'\n@ livro {b}')
        for off in pages(rom, b):
            out.append('--- página')
            out.append(decode_page(rom, off))
    pathlib.Path(out_path).write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'{BOOKS} livros -> {out_path}')


def parse(path):
    books = {}
    cur = None
    for blk in re.split(r'^@ livro ', pathlib.Path(path).read_text(encoding='utf-8'), flags=re.M)[1:]:
        head, _, body = blk.partition('\n')
        n = int(head.split()[0])
        body = '\n'.join(l for l in body.split('\n') if not l.startswith(';'))
        books[n] = [p.strip('\n') for p in re.split(r'^--- página.*$', body, flags=re.M)[1:]]
    return books


def check(book, k, text):
    errs = []
    flat = text.replace('\n', '')
    for box in flat.split('{clr}'):
        lines = re.sub(r'\{(?!n\})[^}]*\}', '', box).split('{n}')
        if lines and lines[-1] == '':
            lines.pop()                          # {n} no fim da página
        if len(lines) > MAX_LINES:
            errs.append(f'livro {book} página {k + 1}: {len(lines)} linhas (máx. {MAX_LINES})')
        for l in lines:
            if len(l.replace('　', '  ')) > MAX_LINE:
                errs.append(f'livro {book} página {k + 1}: linha com {len(l)} carateres: {l!r}')
    return errs


def gerar(rom_path, src, outdir):
    rom = pathlib.Path(rom_path).read_bytes()
    books = parse(src)
    data = bytearray()
    asm = ['; gerado por livros.py a partir de livros_en.txt - não editar']
    errs = []
    base = ((DATA_ROM // 0x8000) << 16) | 0x8000
    for b, plist in sorted(books.items()):
        assert 0 <= b < BOOKS
        n_orig = rom[lorom(ptr3(rom, TABLE + 3 * b))]
        assert len(plist) == n_orig, f'livro {b}: {len(plist)} páginas, o original tem {n_orig}'
        head = len(data)
        data += bytes([len(plist)]) + bytes(3 * len(plist))
        for k, text in enumerate(plist):
            errs += check(b, k, text)
            enc = inserir_texto.encode(text.replace('\n', ''), b, [])[:-1] + b'\xFF\x0B'
            p = base + len(data)
            data[head + 1 + 3 * k:head + 4 + 3 * k] = p.to_bytes(3, 'little')
            data += enc
        asm.append(f'org ${0x0E8000 + 3 * b:06X} : dl ${base + head:06X}   ; livro {b}')
    for e in errs:
        print('ERRO', e)
    assert not errs, 'livros_en.txt tem erros'
    assert len(data) <= 0x8000
    out = pathlib.Path(outdir)
    (out / 'livros.bin').write_bytes(data)
    asm.insert(1, f'org ${base:06X} : incbin "livros.bin"')
    (out / 'livros.asm').write_text('\n'.join(asm) + '\n', encoding='utf-8')
    print(f'livros: {len(books)} traduzidos, {len(data)} bytes')


if __name__ == '__main__':
    {'extrair': extrair, 'gerar': gerar}[sys.argv[1]](*sys.argv[2:])
