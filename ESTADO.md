# Estado do projeto — 3x3 Eyes: Seima Kourinden (EN)

Última atualização: 2026-10-15

## Gerar a ROM

```
python ferramentas\build.py "C:\Users\joseo\Downloads\3x3 Eyes - Seima Kourinden (Japan).sfc"
```

Resultado: `3x3Eyes_EN.sfc` (ROM expandida para 2 MB; a ROM original não é alterada).
Validar o guião: `python ferramentas\validar.py traducao_en.txt guiao_jp.txt` (último resultado: 826 mensagens, 0 erros).

Pipeline (`build.py`): CRC FBF3C0FF → expansão 2 MB → `fonte_en.py` → `menus.py` → `nomes.py` → `campos.py gerar`
→ `blocos.py` → `intro.py` → Asar (`hack.asm`) → `inserir_texto.py` → checksum.

## Feito e testado no Mesen

- **Fonte e texto:** fonte inglesa 8x16 (`fonte_en.py`); desvio na entrada de `$00:E378` (diálogo, menus, combate);
  fonte enviada no NMI relativa à base do BG3 (`$00DC`: $3000 no campo, $2000 no combate).
- **Nomes das personagens:** tabelas `$01:D5A4`, `$01:D5D0`, `$00:ED32` (Yakumo, Pai, Haan, Lin-Lin, Jake, Gupta,
  Sanjiyan, Takuhi, Fei-Oh, Hon-Nyan).
- **Combate:** comandos em `$01:D3B7` (Attack/Magic/Item/Defend/Run/Regen/Awaken); mensagens de combate 0000-006F.
- **Body/Mind:** os kanji 体力/精神 desenham "Body"/"Mind"; espaçamento corrigido (`$0F:99D4/9E25/9EEC`).
- **Menus do banco $0F:** estado, Items/Equip/Status, menu inicial, equipamento (3 variantes), Yes/No, Ron,
  usar/deitar fora, "Are you sure?", Page, Talk, Make Tags, aeroporto, exame médico, etc.
  - Pares de letras (`menus_en.tsv` → `menus.py`): 53 de 63 códigos usados.
  - Blocos reescritos no banco $21 via código de controlo novo **FF 2E** "saltar para"
    (`blocos_en.txt` → `blocos.py`). Preferir blocos aos pares nos menus que faltarem.
  - Regra: em menus com várias opções na mesma linha, o inglês mantém a largura em píxeis do japonês
    (cursores em posições fixas; manter o espaço inicial).
- **Nomes de itens (152), feitiços/objetos de combate (117), inimigos (67), ataques (24), atributos (7):**
  `nomes_en.tsv` → `nomes.py` (atributos em `hack.asm`). Testado no combate (2026-10-09).
  Com base no guia GameFAQs (ritchie) para os nomes menos claros.
- **Locais (184 campos de 12 bytes) e países:** `campos_en.tsv` → `campos.py`.
- **Guião completo:** 826 mensagens em `traducao_en.txt` (limite 21 carateres/linha). "Sei-San" → "the Sanctuary".
- **Ecrãs gráficos de texto** (`intro_en.txt` → `intro.py`, dados no banco $38):
  - Introdução: glifos #1C8, páginas #1C9-#1D0 (LZSS). Testada OK.
  - Monólogo do Yakumo: glifos #1E8, páginas #1ED, #1E9-#1EC (formato por tile).
  - Falas das cenas animadas (Pai/Takuhi): glifos #1E1, páginas #1E3-#1E5.
  - Cor: tinta = cor que os glifos originais usam; sombra preta só quando a tinta é branca.
  - Negrito "inteligente": engrossa 1 píxel para a direita, mas mantém os espaços de 1 píxel que formam
    calhas verticais (m, w, M, W); preenche os isolados (junções do b, h, p, K).

## Sessão 2026-10-08/09

- Negrito dos ecrãs gráficos: 1.ª versão tapava o "m"; 2.ª deixava falhas no b/h/p/K; 3.ª (atual) corrige ambos.
  **Por confirmar no Mesen.**
- Revisão de diálogos do início (pedido do utilizador), 9 falas em `traducao_en.txt`
  (entre outras, mensagens 0178, 0241, 026D, 029D, 02A3, 02A4): "Huh?! Lin-Lin?! / Is that you?", "Is this thing human!?",
  "But Pai, the way you came from is blocked", "We'll have to find another way...", "There is another way!",
  "I need your help to look for it!", "I'll look it up for you when I get to Yogekisha!",
  "Let's have fun together again!!". **Por confirmar no Mesen.**

- Nomes com lixo no combate corrigidos:
  - Inimigos: a tabela tem 67 nomes (ponteiros em `$0C:9996`), não 30 a partir de `$0C:9B9B`. Índices do
    `nomes_en.tsv` renumerados (+10) e acrescentados os inimigos 0-9 e 40-66.
  - Feitiços/objetos de combate: 117 registos (ponteiros em `$0C:8E29`), não 27; todos traduzidos (máx. 7 letras).
  - Atributos da subida de nível (`$01:DB53`, em `hack.asm`): Body, Mind, Power, Speed, Defense, Wisdom, Luck.
- Caixa de combate (mensagens 0000-0064) aceita até 26 carateres por linha (`validar.py`); várias mensagens
  passaram a uma só linha ("What will Pai do?", "Defense went up by 5!", etc.). **Por confirmar no Mesen.**

- **Nomes longos** (itens, objetos de combate, locais): o registo de tamanho fixo passa a conter
  `FF 2E ll hh bb` ("saltar para") e o nome completo fica no banco $30 (`$30:8000` nomes, `$30:C000` locais).
  O `CtrlGoto` (hack.asm) alarga o limite de carateres do sub-texto ($14,x) para 64 quando salta.
  Limites: itens 16 letras, feitiços/objetos de combate 14, locais 20 (centrados com espaços ASCII).
  Ex.: "Takuhi's Staff", "Fakir's Bones", "Priest's House", "Hong Kong Airport". **Por testar**: inventário,
  equipamento, lojas, menu de itens no combate, ecrã de gravação (largura do nome do local).
- **Ecrã de derrota** (texto vertical sobre o Sanjiyan): mapa #1AE, glifos #1AD. Os glifos originais guardam
  2 letras por tile (plano 0 visível com a paleta 0, plano 1 com a paleta 1). Novo texto horizontal em
  `intro_en.txt` com opções novas do `intro.py`: `tinta=`, `attr=`, `base=`, `fim=`, `x=`, `y=`, `passo=`.
  Sombra preta (cor 2 da paleta 0). Testado OK no Mesen (2026-10-09).
- **Kana no início das mensagens:** a 1.ª solução (regravar a fonte #000/#001 com as letras inglesas) foi
  testada OK, mas punha a fonte original do jogo no patch. **2.ª solução (2026-10-10):** ganchos no carregador
  de gráficos (`$00:865D` guarda o nº do descritor, `$00:86EF` chama `FontUploadAll` se for #000/#001), que
  envia logo todos os segmentos da fonte inglesa para a VRAM. `fonte_rom.py` removido. **Testado OK no Mesen (2026-10-10).**
- **Patch BPS:** `python ferramentas\criar_bps.py <rom original> 3x3Eyes_EN.sfc <saída.bps>` (codificador
  próprio; verifica o patch reaplicando-o). v0.1-beta: 126954 bytes, resultado CRC32 D97935D1. v0.2-beta: 130541 bytes, CRC32 A9A3BC49. v0.2.1-beta: 130656 bytes, CRC32 7435533B.
- Desmontador simples de 65816: `ferramentas/analise/dis65816.py <rom> <banco:endereço> [n]`.

- **Livros lidos no menu** (Atlas, Pyramid Book, livros de talismãs/pentáculos/Nauthiz): não estão no guião
  principal. Tabela `$0E:8000` (10 livros × ponteiro de 3 bytes → [nº de páginas][ponteiros das páginas];
  páginas acabam em `FF 0B`), lida em `$00:CF79`. `livros_en.txt` → `ferramentas/livros.py` (dados no banco $33).
  Referência japonesa: `python ferramentas\livros.py extrair <rom> livros_jp.txt` (fora do git). Testado OK (2026-10-10).
- **Ron → Long** (Stephen Long, como no anime).
- **Nomes completos de inimigos e ataques especiais** (até 12 letras, via `FF 2E`): Hunchback, Bone Lizard,
  Mystery Claw, Queen Moth, Ice Breath, Scale Powder... "dodged swiftly" → "dodged it" (cabe com 12 letras).
  Testado OK (2026-10-10).

- **Estado na janela de combate** (veneno/paralisia aparecia com lixo no lugar do nome): rotina `$00:DBE2` usa
  sub-textos no banco 00 (`$00:DC19` どく, `$00:DC1E` マヒ) → "Poison"/"Numb" em `$00:FCC0`. Entrada 8 de
  `$00:ECF0` (まひ, ecrã de estado) → "Numb". Textos com 8 carateres (tapam o nome); nomes da tabela `$00:ED32` (menu de estado) também com 8 carateres (`NamePad`). Testado OK (2026-10-11).

- **Respostas aos Kaiyan Generals** (Kunlun; menu `$0F:A1C4`, antes chamado "exame médico"): Flesh / Body Heat /
  Breath / Blood / Organs, como no Pyramid Book; janela alargada (`$0F:A1BE` = `$1A`). Testado OK (2026-10-13).

- **Nomes dos países** (menu de destinos do aeroporto): a rotina `$00:E638` (código FF 20) lê agora a tabela
  `CountryNames` (banco $20, 16 bytes por país) em vez de `$0C:CF07` (4 carateres). "Hong Kong" com espaço;
  janela do menu (`$0F:A147`) alargada para `$1A`. Testado OK (2026-10-14).

- **Buraco na parede do labirinto da Treasury** (erro do patch, v0.1-beta a v0.2.1-beta): as variáveis do
  patch estavam em `$7F:FF00-05`, no fim do mapa das masmorras, e estragavam 3 células. Passaram para
  `$7E:E800-E805`. Testado OK (2026-10-15). Ver CHANGELOG.md.

## Por testar

- Monólogo e falas das cenas com o negrito novo.
- Mensagens de combate 0028-006F; nomes de inimigos/ataques/feitiços em contexto.
- Contador "コ" da janela de quantidade (passou a espaço).

## Próximos passos

(Feito em 2026-10-09: kana visíveis por um instante no início das mensagens — ver acima.)


1. Jogar do início ao fim e corrigir a tradução à medida (enviar correções em lista, como em 2026-10-09).
2. Procurar e traduzir os restantes ecrãs gráficos de texto (#1EE com conjunto de glifos desconhecido, final do jogo).
3. Releases seguintes (v0.2…) com as correções dos testers: `criar_bps.py` + `gh release create`. v0.1-beta e v0.2-beta publicadas em 2026-10-10; v0.2.1-beta em 2026-10-11.
4. Mais tarde: fonte de largura variável (VWF); gráficos do título e kanji de cidades (ex.: 香港).

## Dúvidas de tradução em aberto

- Huang/Joan, Garga/Galga. (Ron → Long decidido em 2026-10-10.)
- Familiares de demónios (Naam, Yoea, Hippolopos, Haiamon, Ashinel...): romanizações por rever.
- Ordem dos elementos no labirinto de Kunlun (Earth/Water/Fire/Wind/Air): confirmar no jogo.

## Referências

- Documentação técnica completa: `DOCUMENTACAO.md`. Glossário: `glossario.md`.
- Histórico das conversas: `historico/`.
