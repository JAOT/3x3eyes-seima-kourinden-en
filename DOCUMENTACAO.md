# 3x3 Eyes: Seima Kourinden — Tradução para inglês

Documentação técnica do projeto: o que foi descoberto sobre a ROM, como as ferramentas funcionam,
que técnicas foram usadas e porquê, e o histórico do trabalho. Para o estado atual e a lista de
tarefas pendentes, ver também [ESTADO.md](ESTADO.md).

---

## 1. Visão geral

| | |
|---|---|
| Jogo | 3x3 Eyes: Seima Kourinden (Super Famicom, 1992) |
| ROM base | `3x3 Eyes - Seima Kourinden (Japan).sfc` — 1 MB, LoROM, sem cabeçalho de copiadora, CRC32 `FBF3C0FF` |
| ROM gerada | `3x3Eyes_EN.sfc` — 2 MB (expandida), gerada sempre a partir da ROM original |
| Língua alvo | Inglês (nomes: "Yakumo", etc. — ver [glossario.md](glossario.md)) |
| Projeto anterior | Tradução de Filler/KingMike (2005) e Dynamic Designs (2018), nunca lançada — este projeto é independente |

---

## 2. Ambiente

| Ferramenta | Uso | Localização |
|---|---|---|
| Mesen 2 | Emulador, depurador, save states, Trace Logger | `Documentos\Mesen2` (save states em `SaveStates`, traces em `Debugger`) |
| Asar 1.91 | Assembler 65816 (aplica `hack.asm`) | `ferramentas\asar\asar.exe` |
| Python 3.12 | Ferramentas de build e análise | `AppData\Local\Programs\Python\Python312\python.exe` |
| PowerShell 7 | Extração inicial e scripts de análise | — |

Notas do ambiente:
- O PowerShell instalado pela Microsoft Store não vê pastas dentro de `AppData\Roaming` (virtualização MSIX). Manter o projeto fora dessa pasta.
- Opções do Trace Logger do Mesen usadas: registos, flags, endereço efetivo, valor de memória, byte code; **sem** labels; só a CPU SNES.

---

## 3. Gerar a ROM

```
python ferramentas\build.py "C:\Users\joseo\Downloads\3x3 Eyes - Seima Kourinden (Japan).sfc"
```

Passos do `build.py`:
1. Lê a ROM original, verifica o CRC32, remove cabeçalho de copiadora se existir.
2. Expande para 2 MB e muda o byte de tamanho no cabeçalho (`$7FD7` = `$0B`).
3. `fonte_en.py` → gráficos da fonte inglesa e tabelas (`gerado/font_en*.asm/.bin`).
4. `menus.py` (`menus_en.tsv`) → pares de letras nos menus (`gerado/menus.asm`).
5. `nomes.py` (`nomes_en.tsv`) → nomes de feitiços, inimigos, itens, ataques (`gerado/nomes.asm`).
6. `campos.py gerar` (`campos_en.tsv`) → campos de largura fixa: locais, sim/não… (`gerado/campos.asm`).
7. `blocos.py` (`blocos_en.txt`) → blocos de menus reescritos no banco `$21` (`gerado/blocos.asm`).
8. `intro.py` (`intro_en.txt`) → ecrãs gráficos de texto no banco `$38` (`gerado/intro.asm`).
9. Asar aplica `hack.asm` (que inclui todos os `gerado/*.asm`).
10. `inserir_texto.py` insere o guião traduzido (`traducao_en.txt`) e reaponta as mensagens.
11. Corrige o checksum do cabeçalho.

Nada é editado à mão na ROM: tudo sai dos ficheiros de texto e do `hack.asm`.

**Patch para distribuição:** `python ferramentas\criar_bps.py <rom original> 3x3Eyes_EN.sfc <saída.bps>`.
Codificador BPS próprio (SourceRead / TargetCopy para sequências repetidas / TargetRead); aplica o patch à ROM
original e confirma que o resultado é igual antes de gravar. O patch não deve conter dados originais do jogo
(por isso a fonte inglesa é enviada por código e não regravada dentro da fonte do jogo).

**Repositório e releases:** https://github.com/JAOT/3x3eyes-seima-kourinden-en (público). O `.gitignore` deixa de
fora ROMs, patches, `historico/`, `ferramentas/gerado/`, o Asar, o guião japonês, `traducao_trabalho/` e imagens
(exceto `docs/screenshots/`). Releases com o `.bps` em GitHub Releases (`gh release create`).

---

## 4. Ficheiros do projeto

| Ficheiro | Conteúdo | Editar? |
|---|---|---|
| `guiao_jp.txt` | Guião japonês extraído (4216 mensagens) | Não (referência) |
| `tabela.tbl` | Tabela de carateres (formato .tbl) | Não |
| `traducao_en.txt` | Guião traduzido (mesmo formato do `guiao_jp.txt`) | **Sim** |
| `nomes_en.tsv` | Feitiços, inimigos, itens, ataques (máx. 7–8 letras) | **Sim** |
| `menus_en.tsv` | Rótulos de menus com pares de letras | **Sim** |
| `campos_en.tsv` | Campos de largura fixa (locais, sim/não, aeroporto, hotel) | **Sim** |
| `blocos_en.txt` | Blocos de menus reescritos sem limite de largura | **Sim** |
| `glossario.md` | Nomes e termos fixos | **Sim** |
| `ESTADO.md` | Estado atual e pendentes | Sim |
| `ferramentas/hack.asm` | Todas as alterações de código (Asar) | Com cuidado |
| `ferramentas/*.py` | Ferramentas de build | Com cuidado |
| `ferramentas/extrair_texto.ps1` | Extrator do guião (PowerShell) | — |
| `ferramentas/validar.py` | Valida a tradução contra o japonês (etiquetas, ASCII, largura das linhas) | — |
| `traducao_trabalho/` | Partes usadas na tradução em paralelo (`jp_parte_N` / `en_parte_N`) | Não (referência) |
| `intro_en.txt` | Ecrãs gráficos de texto: introdução, monólogo inicial, falas das cenas | **Sim** |
| `ferramentas/intro.py` | Gera glifos e mapas dos ecrãs gráficos nos formatos do jogo | — |
| `ferramentas/analise/descomprimir.py` | Descompressores do jogo (LZSS e gráficos por tile) + leitura dos descritores | — |
| `ferramentas/analise/desenhar_ecra.py` | Desenha um mapa de tiles com um conjunto de glifos (PNG) | — |
| `ferramentas/analise/dma_trace.py` | Lista as transferências DMA de um trace | — |
| `ferramentas/analise/procurar_menus.py` | Procura texto japonês por traduzir no banco $0F | — |
| `proposta_intro_*.png` | Simulações da introdução em inglês | — |
| `ferramentas/analise/` | `mss.ps1` (desempacota save states do Mesen), `TraceScan.cs` (analisa traces), `snes.cs` (desenha tiles) | — |
| `ferramentas/gerado/` | Ficheiros gerados pelo build | Não |
| `historico/` | Exportações completas das conversas de trabalho (zip) | Não |

---

## 5. Descobertas sobre a ROM

Endereços no formato SNES `banco:endereço` (LoROM). Offset na ROM = `banco*0x8000 + (endereço-0x8000)`.

### 5.1 Texto (guião principal)
- **Tabela de ponteiros:** `$0D:8000` (ROM `0x68000`), 4216 entradas de 3 bytes (endereço de 24 bits).
- **Texto:** a partir de `$0D:B168` (ROM `0x6B168`) até ao fim do banco `$0E`. **Sem compressão**, 1 byte por carácter.
- Três grandes grupos de entradas vazias partilham ponteiros (0x2A5–0x300, 0x323–0x400, 0x401–0xFFF).
- 12 mensagens começam a meio de outras (sequências ligadas por `{0B}`).
- Mensagens 0x0000–0x006F são as **mensagens de combate**.

### 5.2 Codificação dos carateres
| Códigos | Significado |
|---|---|
| `00` | Fim de mensagem |
| `01`–`B3` | Glifos 16x16: katakana, hiragana, pequenas, dakuten, 14 kanji, ー／＋・ (índice = código−1; tabela de tiles em `$00:ED89`) |
| `B4`–`CE` | Glifos 8x16: 0–9, M, F, B, espaço (`C1`), 「」、。！？″ ◀▶◁▷, molduras (tabela `$00:F321`) |
| `CF`+ | Peças de molduras de janelas (tabela `$00:F38D`) |
| `FF xx` | Código de controlo (tabela de saltos original em `$00:E809`, códigos `00`–`2D`) |

Códigos de controlo principais (nº de parâmetros entre parênteses):
`01` limpar caixa (0) · `02` mudança de linha (0) · `04` esperar botão (0) · `05` velocidade (1) ·
`07` número (1) · `08` sub-texto de tabela `$00:ECF0` (1, máx. 8 carateres) · `09` posição (2) ·
`0B` página seguinte (0) · `10` nome de item (1) · `1A`/`2A` nome de personagem (1) · `20`–`22` (3).
A tabela completa está no `inserir_texto.py`/`extrair_texto.ps1` (`Params`).

### 5.3 Rotinas importantes
| Endereço | Função |
|---|---|
| `$00:E378` | Desenha um glifo (código em `$04`) no mapa de tiles em RAM `$7E:3000`; devolve a largura. Chamada de ~30 sítios |
| `$00:E3E0` | Ciclo principal de texto |
| `$00:E8F9` | Lê o byte seguinte do texto (`[$18,X]`, banco `$1A,X`); `$14,X` = limite de carateres do sub-texto |
| `$00:E8CB` / `$00:E8E2` | Guardar / repor o contexto ao entrar / sair de um sub-texto |
| `$00:CDEE` | Lê o ponteiro da mensagem (`$0D:8000 + id*3`) |
| `$00:D14E` | Copia o nome de um item (8 bytes) para `$7E:22F2` |
| `$00:80F9` | NMI original |
| `$00:9813` | Escreve `$210C` (base de carateres BG3); cópia em `$00DC` |
| `$00:BE88` | Interpretador de scripts de eventos: palavras de 16 bits lidas em `$00:C6DB` (ponteiro `$0C40`/`$0C42`, scripts nos bancos `$1E`/`$1F`), saltos pela tabela `$00:BEB2`. Ex.: `0D vv alvo` = se direção (`$106C`) = vv, saltar; `0B x y alvo` = teste de posição; `42 msg` = mostrar mensagem |
| `$01:8654` | Combates aleatórios: a cada passo, número aleatório 0-511 (`$01:9AF8`) comparado com a taxa do mapa (tabela `$0C:A411`); `BEQ` em `$01:866D` salta quando a taxa é 0. Game Genie para desligar os combates: `6D61-6709` (`$01:866D` = `$80`) |
| `$00:B797` | Colisão: bloco da célula do mapa (`$7F:8000-FFFF`, endereço calculado em `$00:A562`, guardado em `$00`) → atributo em `$7E:8000` (0 = transitável, 1 = parede) |
| `$1F:92FC` | Script de usar objetos nas masmorras: `0068 0003 MAPA destino` escolhe por nº do mapa; `000D 0001` = virado para cima; `000B x y destino` = posição (píxeis); `0024 x y 00B2` troca o bloco por "abertura". Estátuas de Nauthiz (célula onde se fica, virado para cima): 2F (7,8),(7,89); 3F (23,73),(55,89); B1 (8,55),(40,39); B2 (56,10),(8,71); B3 (119,8). Pedestais: `$1F:C776` |
| RAM `$106C` | Direção do jogador (bits 0-1; 1 = cima, 2 = baixo). A porta do Templo de Zeus (`$1F:8DBA`) exige o Yakumo virado para cima |

### 5.4 Vídeo
- Texto no **BG3** (2bpp), mapa de tiles em VRAM `$5000` (cópia na RAM em `$7E:3000`).
- Base de carateres do BG3: **`$3000` no campo, `$2000` no combate** (cópia do jogo em `$00DC`).
- A fonte japonesa está **comprimida** na ROM; na VRAM cada pixel é cor 1 (fundo) ou 2 (letra).

### 5.5 Tabelas de nomes e dados
| O quê | Onde | Formato |
|---|---|---|
| Nomes das personagens (cópia para `$7E:2252`) | `$01:D5A4` → agora `NameTable` no banco `$20` | ponteiros de 16 bits |
| Nomes de invocações (Takuhi, Fei-Oh, Hon-Nyan) | `$01:D5D0` | 3 ponteiros, nomes no banco 01 |
| Nomes das personagens (menu de estado, `{1A}`, `{2A}`) | `$00:ED32` → `NameTable` | 7 ponteiros |
| Sub-textos de `{08:xx}` | `$00:ECF0` | 8 ponteiros de 3 bytes (6 = saudável, 7 = veneno) |
| Comandos de combate | `$01:D3B7` (ponteiros em `$01:D3A9`) | 6 conjuntos × 6 × 8 bytes |
| Feitiços e objetos de combate | `$0C:8F13` (ponteiros em `$0C:8E29`) | 117 × 23 bytes, nome 8 bytes |
| Inimigos | ponteiros em `$0C:9996` (1.º nome em `$0C:9A1C`, os outros de 38 em 38 bytes a partir de `$0C:9A45`) | 67 nomes de 8 bytes |
| Atributos (subida de nível) | `$01:DB53` (ponteiros em `$01:DB45`) | 7 × 8 bytes |
| Ataques especiais dos inimigos | `$0C:8C4D` | 24 × 14 bytes, nome 8 bytes sem terminador |
| Itens (todos) | `$0C:AFE3` (ponteiros em `$0C:AEB3`) | 152 × 30 bytes, nome = 8 primeiros bytes |
| Locais | `$0C:CD9E` e `$0C:CF1B` | campos de 12 bytes, nomes centrados com espaços; lidos como sub-texto com limite 13 (`$00:E67C`, `$00:E6AE`) |
| Livros lidos no menu (Atlas, Pyramid Book...) | `$0E:8000` (lida em `$00:CF79`, livro nº `$060E`) | 10 ponteiros de 3 bytes → [nº de páginas][ponteiros de 3 bytes]; páginas acabam em `FF 0B` |
| Países (aeroporto) | `$0C:CF0B` | 4 campos de 4 bytes |
| Menus / janelas | banco `$0F` | texto com códigos de controlo e posições fixas |

### 5.5b Ecrãs gráficos e compressão
- **Tabela de descritores** em `$02:8000`: entradas de 6 bytes = origem (24 bits) + destino (24 bits).
  Destino com o bit 7 do banco ligado = VRAM, base = uma das cópias `$D0`-`$DE` (nibble baixo) + endereço.
  Rotina de carga: `$00:8650`.
- **Formato escolhido pelo 1.º byte dos dados:** bit 7 ligado = **LZSS** (`$00:8A11`): palavra = nº de
  operações; grupos de 8 com byte de flags (bit 1 = literal; bit 0 = referência de 2 bytes: distância 12 bits+1,
  comprimento nibble+2, ou byte extra +0x12). Bit 7 desligado = **gráficos por tile** (`$00:86F2`): cabeçalho
  [modo][nº de tiles][deslocamento do fluxo de modos]; modo do tile (2 bits, ou 1 bit em 2bpp): vazio,
  máscara de bytes, máscara + XOR entre linhas, ou cópia direta / máscara + XOR sequencial.
- **Introdução:** glifos `#1C8`, páginas `#1C9`-`#1D0` (LZSS). **Monólogo inicial:** glifos `#1E8`, páginas
  `#1E9`-`#1ED` (formato por tile). **Falas das cenas:** glifos `#1E1`, páginas `#1E3`-`#1E5`. `#1EE` usa outro
  conjunto de glifos (por identificar). **Ecrã de derrota:** mapa `#1AE`, glifos `#1AD`, paleta `#1AF`.
- **Truque dos 2 planos (ecrã de derrota):** cada tile 2bpp guarda duas letras, uma por plano de bits; a paleta 0
  (cor 1 branco, cor 2 preto) mostra o plano 0 e a paleta 1 (cor 1 preto, cor 2 branco) o plano 1.
  `intro.py` aceita opções por página: `tinta=`, `sombra=`, `attr=`, `base=`, `fim=`, `x=`, `y=`, `passo=`.
- Paleta 0 da introdução: cor 1 azul-escuro, 2 branco, 3 preto; os glifos originais só usam a cor 2.
- Os dados novos são gravados com literais (gráficos em máscara cheia, LZSS só com literais), sem mudar código;
  glifos nos tiles `$0A2`-`$12A` (fora da fonte de diálogo). Bancos `$38`-`$39`.

### 5.6 Menus do banco $0F (já identificados)
| Endereço | Menu |
|---|---|
| `$0F:97C8` | Items / Equip / Status |
| `$0F:99A0`, `9E16`, `9EDE` | Ecrã de estado (uma cópia por personagem) |
| `$0F:9906`, `9CFD`, `9D90` | Ecrã de equipamento (uma cópia por personagem) |
| `$0F:9850` | Janela de quantidade |
| `$0F:9882`, `A0CC`, `A39D` | Sim / Não (blocos; espaço inicial do cursor largo em 9882, estreito nos outros) |
| `$0F:A0F7` | Hotel |
| `$0F:A243` | Loja (comprar / vender) |
| `$0F:A280` | Aeroporto (ir / ficar) |
| `$0F:A335`–`A387` | Menu inicial (escolher ficheiro, Start / Delete) |
| `$0F:A17C` | Ron (Plastic Bomb / Grenade) |
| `$0F:9862`, `98A2` | Usar / deitar fora; "Are you sure?" |
| `$0F:9A8E`, `9FA4`, `A016` | Equipamento com ranhura de magia (3 cópias) |
| `$0F:9B06`–`9B86` | Grimório / talismãs (Page, Talk, Make Tags, made, Survival Knife) |
| `$0F:A11F` | Balcão do aeroporto (Buy Ticket / Departure) |
| `$0F:A1C4`, `A207`, `A2AE` | Respostas aos Kaiyan Generals (Flesh/Body Heat/Breath/Blood/Organs); 1st–4th; Make / Don't make |

Todos os menus do banco `$0F` foram encontrados com `ferramentas/analise/procurar_menus.py`
(compara a ROM original com a inglesa e lista texto japonês ainda não alterado). O que resta na
listagem são tabelas de dados que por acaso parecem kana.

---

## 6. Alterações ao jogo (`hack.asm`)

| Alteração | Como |
|---|---|
| **Texto em inglês (ASCII)** | Desvio na entrada de `$00:E378` → `TextHook` (`$00:FC00`): códigos `$20`–`$7E` desenham letras 8x16 (meia largura) com a tabela `GlyphMap`; o resto segue a rotina original |
| **Fonte inglesa** | Desenhada de raiz (`fonte_en.py`), 94 glifos 8x16 em 2 tiles cada, colocados por cima de tiles usados só pelos kana |
| **Envio da fonte para a VRAM** | NMI desviado para `NmiFar` (`$20:8025`): envia um segmento por frame (DMA canal 6; o canal 7 é do HDMA do jogo) enquanto há texto a ser desenhado; endereço = segmento + base BG3 (`$00DC`) |
| **Nomes das personagens** | Tabela `NameTable` no banco `$20`; cópias de 9 bytes (`$01:9A68`, `$01:9A7D`); `$00:ED32` reapontado (banco `$20`) |
| **Body/Mind** | Os kanji 体力精神 desenham "Bo","dy","Mi","nd" (tabela `$00:ED89`) |
| **Pares de letras** | Códigos de katakana/hiragana (`$01`–`$1F`, `$80`–`$9F`) reaproveitados para desenhar 2 letras num glifo 16x16 (`menus.py`) |
| **Código de controlo `FF 2E`** | "Continuar a ler em `$bb:hhll`". Tabela de controlo copiada para `$00:F600`; tratador `CtrlGoto`. Usado pelos blocos (`blocos.py`) e pelos nomes longos (`nomes.py`, `campos.py`). Num sub-texto com limite de carateres (`$14,x` ≠ 0), o limite passa a 64 |
| **Atributos** | `$01:DB53`: Body, Mind, Power, Speed, Defense, Wisdom, Luck |
| **Fonte ao carregar** | Ganchos no carregador de gráficos: `$00:865D` → `LoadHookIn` guarda o nº do descritor em `$7F:FF04`; `$00:86EF` → `LoadHookOut` chama `FontUploadAll` (banco `$20`) se foi a fonte de diálogo #000/#001, que envia todos os segmentos da fonte inglesa por DMA. Elimina os kana nos primeiros frames das mensagens |
| **Estado de saúde** | `$00:ECF0` entradas 6 e 7 → "Healthy"/"Poison" no banco `$20` |
| **Contador da quantidade** | `$0F:9852`: "コ" → espaço |

Mapa de memória usado:
| Zona | Conteúdo |
|---|---|
| `$00:F600`–`$00:FBFF` | Tabela de controlo e `CtrlGoto` |
| `$00:FC00`– | `TextHook`, `NmiStub`; `$00:FCC0` textos do estado no combate (livre até `$00:FCFF`) |
| `$00:FE60`– | `LoadHookIn`, `LoadHookOut` (livre até `$00:FFAF`) |
| `$20:8000`– | Código (`LatinGlyph`, `NmiFar`), `NameTable`, textos de estado, `GlyphMap`, `FontSegs` |
| `$21:8000`– | Gráficos da fonte |
| `$21:9000`– | Blocos de menus |
| `$22:8000`– | Guião traduzido (~67 KB; o reinseridor não deixa uma mensagem atravessar bancos) |
| `$30:8000`– / `$30:C000`– | Nomes longos de itens/feitiços / de locais |
| `$38:8000`– | Ecrãs gráficos (`intro.py`) |
| RAM `$7E:E800-E805` | Variáveis do patch: contador e índice do envio da fonte, último descritor carregado. **Não usar `$7F:8000-FFFF`** (mapa das masmorras): até à v0.2.1-beta as variáveis estavam em `$7F:FF00-05` e estragavam 3 células do mapa do labirinto da Treasury |

---

## 7. Técnicas de tradução e regras

1. **Guião** (`traducao_en.txt`): texto ASCII + etiquetas. Só as mensagens presentes são reapontadas. Limite ~21 carateres por linha, 3 linhas por caixa.
2. **Nomes em tabelas** (`nomes_en.tsv`): escritos no próprio registo. Limite 7 letras (8 nos itens e ataques). Verificado que o enchimento original era zero.
   **Nomes longos:** se o nome não cabe, o registo fica com `FF 2E` + ponteiro para o nome completo no banco `$30`
   (itens até 16 letras, feitiços/objetos de combate até 14, inimigos e ataques até 12). Funciona porque os nomes são sempre desenhados pelo motor de texto.
3. **Pares de letras** (`menus_en.tsv`): 1 byte = 2 letras = 16 px. Mantêm exatamente o tamanho e a largura dos menus. Recurso limitado (63 códigos; 53 usados).
4. **Campos fixos** (`campos_en.tsv`): ASCII num campo de N bytes (máx. N letras), centrado ou à esquerda.
   Os locais podem ter até 20 letras (mesmo mecanismo de salto, centrados com espaços ASCII).
5. **Blocos** (`blocos_en.txt`): o texto é reescrito no banco `$21`, sem limite. **Preferir esta técnica para menus novos.**

Regras aprendidas:
- **Tamanho das janelas dos menus do banco $0F:** antes do texto há um cabeçalho `[ponteiro 2 bytes][largura][altura]`
  (meios tiles; altura = 4 por linha + 4). Ex.: respostas aos Kaiyan Generals, `$0F:A1BE` largura `$16` → `$1A`.
- **Cursores com posição fixa:** em menus com várias opções na mesma linha, o inglês tem de manter a largura em píxeis do japonês (ex.: "Go" = par + 3 espaços largos = 64 px).
- **Espaço inicial das linhas:** em muitas janelas, a 1.ª posição de cada linha é onde o cursor é desenhado — manter o espaço (largo `　` ou estreito ` `).
- **Várias cópias:** ecrãs de estado e de equipamento existem uma vez por personagem.
- **Sub-textos `{08:xx}`** mostram no máximo 8 carateres (exceto nomes longos, via salto).
- **Caixa de combate** (mensagens 0000-0064): até 26 carateres por linha (`validar.py`).

---

## 8. Métodos de investigação

- **Save states do Mesen** (`analise/mss.ps1`): desempacota a captura de ecrã, VRAM, WRAM, CGRAM e registos do PPU. Usado para encontrar a fonte, o mapa de tiles e as bases do BG3.
- **Trace logs do Mesen** (`analise/TraceScan.cs` e scripts Python): procurar as leituras de texto em `$00:E90F` (dá o endereço de cada mensagem), as escritas no mapa de tiles e as cópias (`MVN`). Foi assim que se encontraram o formato do texto, a tabela de ponteiros, as tabelas de nomes e os menus.
- **Desmontador** (`analise/dis65816.py <rom> <banco:endereço> [n]`): para ler rotinas sem trace.
- **Render de mapas** (`analise/desenhar_ecra.py` e scripts ad hoc): desenhar cada mapa 32x32 com vários conjuntos
  de glifos até o texto aparecer legível (foi assim que se encontrou o ecrã de derrota).
- **Pesquisa de bytes:** codificar uma palavra japonesa com a tabela de carateres e procurá-la na ROM. Ter em conta que, na ROM inglesa, códigos de kana podem aparecer como pares de letras (ex.: "ファイル1" aparecia como "y 2at+1").

---

## 9. Histórico

### Dia 1 — 2026-10-06
- Análise inicial: LoROM 1 MB; texto não estava em Shift-JIS nem com tabelas simples.
- Save state da introdução: fonte 16x16 encontrada na VRAM (a introdução é um ecrã gráfico à parte).
- Save state de um diálogo + trace log: rotina de leitura em `$00:E8F9`, texto **sem compressão** em `$0E:CE78`.
- Tabela de carateres completa e códigos de controlo; tabela de 4216 ponteiros em `$0D:8000`.
- Extrator (`extrair_texto.ps1`) → `guiao_jp.txt` (0 bytes desconhecidos).
- Projeto movido para `Documentos\3x3Eyes-Traducao`; Asar e Python instalados.
- Fonte inglesa 8x16, gancho de texto, envio da fonte no NMI, expansão para 2 MB, reinseridor, build.
- Primeiro teste: mensagens 0x240/0x241 (Lin-Lin) em inglês no Mesen.
- Nomes das personagens (duas tabelas); HP/MP e depois Body/Mind; comandos de combate.

### Dia 2 — 2026-10-07
- Combate: gancho movido para a entrada de `$00:E378`; envio da fonte relativo à base do BG3 (`$00DC`).
- Ecrã de estado e submenu com pares de letras (`menus.py`).
- Mensagens de combate 0x00–0x6F traduzidas.
- Feitiços, inimigos, ataques especiais (`nomes.py`); estado Healthy/Poison; Luck; To next level.
- Locais (184 campos), países, sim/não, aeroporto, loja, hotel (`campos.py`); regra dos cursores fixos.

### Dia 3 — 2026-10-08
- Todos os 151 itens traduzidos (tabela única em `$0C:AFE3`).
- Código de controlo novo `FF 2E` e ferramenta de blocos (`blocos.py`).
- Ecrã de equipamento (3 cópias) e menu inicial (escolher ficheiro, Start / Delete).
- Esta documentação; exportação da conversa para `historico/`.
- Sim / Não passados para blocos (o cursor tapava a 1.ª letra).
- Bloco 1 do guião (abertura) traduzido e validado em jogo.
- **Guião completo:** validador `validar.py`; as 682 mensagens restantes divididas em 7 partes e traduzidas
  em paralelo por subagentes, cada parte validada; junção, uniformização de nomes e correções de largura.
  Total: 826 mensagens, 0 erros.
- Terminologia: せい三 = せいち (聖地) → "the Sanctuary" / "Sanctuary Keys" (o código mostrado como 三 é 地 nos diálogos).
  Kunlun (コンロン, reino dos Sanjiyan) ≠ Kowloon (クーロン, Hong Kong).
- Menu do Ron e pesquisa automática de todos os menus do banco $0F (15 menus novos em blocos).
- Guia do GameFAQs (ritchie) usado como referência: Nauthiz, labirintos de Kunlun (Earth/Water/Fire/Wind/Air), Pael.
- **Ecrãs gráficos:** descompressores reproduzidos; introdução (8 páginas), monólogo inicial (5 páginas) e
  falas das cenas (3) traduzidos; cores corrigidas (letra branca = cor 2); negrito.

### Dia 4 — 2026-10-09
- Negrito "inteligente" nos ecrãs gráficos: mantém as calhas de 1 píxel do m/w/M/W e preenche as junções do b/h/p/K.
- Revisão de 9 falas do início a pedido do utilizador.
- Nomes com lixo no combate: a tabela de inimigos tem 67 nomes (estava a começar 10 entradas tarde); a tabela de
  feitiços/objetos de combate tem 117 registos; atributos da subida de nível traduzidos.
- Mensagens de combate passadas para uma linha (caixa de 26 carateres).
- Nomes longos de itens e locais via `FF 2E` (ex.: "Takuhi's Staff", "Priest's House").
- Ecrã de derrota (#1AE) traduzido; truque dos 2 planos de bits; sombra preta (cor 2). Testado OK.
- `ESTADO.md` atualizado; conversa exportada para `historico/sessao-2026-10-09_nomes-longos-derrota.zip`.

### Dia 5 — 2026-10-10
- Kana no início das mensagens: 1.ª solução (fonte do jogo regravada, `fonte_rom.py`) funcionava mas levava a fonte
  original para o patch; substituída por ganchos no carregador de gráficos (`FontUploadAll`). Testado OK.
- Porta do Templo de Zeus: não era bug; o evento exige o Yakumo virado para cima (`$106C` = 1). Interpretador de
  eventos (`$00:BE88`) documentado.
- Repositório Git + GitHub (público), README em inglês com capturas, `criar_bps.py`.
- **Release v0.1-beta** (pre-release) com o patch `.bps` (126954 bytes, resultado CRC32 `D97935D1`).
- Conversa exportada para `historico/sessao-2026-10-10_github-release.zip`.
- Livros lidos no menu (Atlas, Pyramid Book, talismãs, pentáculos, provas de Nauthiz): tabela `$0E:8000`, fora do
  guião principal; `livros.py` + `livros_en.txt`. Ron → Long. Inimigos e ataques com nomes completos (até 12 letras).
- **Release v0.2-beta** (130541 bytes, CRC32 `A9A3BC49`).

### Dia 6 — 2026-10-11
- Estado na janela de combate (veneno/paralisia com lixo): sub-textos `$00:DC19`/`$00:DC1E` lidos em `$00:DBE2`
  → "Poison"/"Numb" em `$00:FCC0`, com 8 carateres para taparem o nome. Entrada 8 de `$00:ECF0` (まひ) → "Numb".
- Menu de estado: nomes da tabela `$00:ED32` com 8 carateres (`NamePad`), como os originais (enchidos com espaços).
- "Holy Rock" → "Holy Stone" em todo o guião.
- Manual japonês (PDF do Internet Archive, só imagens JPEG 2000/JBIG2): páginas convertidas com a API
  `Windows.Data.Pdf` (PowerShell 5.1). Controlos: cruz = mover/cursor/página; A = falar/examinar/confirmar;
  B = cancelar/abrir e fechar menu; X = mostrar o local atual; START = começar. Nomes completos das personagens
  (Hazrat Haan, Lee Lin-Lin, Jake McDonald, Armalik Gupta) no glossário; "Almalik" → "Armalik".
- **Release v0.2.1-beta** (130656 bytes, CRC32 `7435533B`).
- Conversa exportada para `historico/sessao-2026-10-11_livros-estados-v0.2.1.zip`.

### Dia 7 — 2026-10-12 a 2026-10-15
- `MANUAL.md`: manual japonês traduzido para inglês (só texto, com as páginas do original 〔p. N〕).
- Kunlun: o menu "exame médico" (`$0F:A1C4`) era afinal a resposta aos Five Kaiyan Generals → Flesh / Body Heat /
  Breath / Blood / Organs (como o Pyramid Book); janela alargada (`$0F:A1BE`). Cabeçalho das janelas do banco $0F:
  `[ponteiro][largura][altura]` (meios tiles).
- Países: `$00:E638` (código FF 20) lê `CountryNames` (banco $20, 16 bytes/país) → "Hong Kong"; janela `$0F:A147`.
- Pequenas revisões pedidas a jogar ("Attack who?", "Use it on who?", aeroporto...). `juntar_linhas.py`: junta
  linhas partidas a meio de frase quando cabem (100 mensagens, texto inalterado).
- Combates aleatórios: `$01:8654` (taxa por mapa em `$0C:A411`); Game Genie `6D61-6709` desliga-os (só para testes).
- **Erro do próprio patch:** as variáveis do patch estavam em `$7F:FF00-05`, no fim do mapa das masmorras
  (`$7F:8000-FFFF`), e estragavam 3 células (buraco na parede do labirinto da Treasury). Movidas para `$7E:E800`.
  Colisão: célula do mapa → atributo do bloco em `$7E:8000` (`$00:B797`). Mapa desenhado a partir de um save state
  (8×8 ecrãs) para guiar o utilizador no labirinto.
- `CHANGELOG.md` criado (histórico das versões e secção "Unreleased").
- Commits locais; sincronização com o GitHub só quando pedida.
- Conversa exportada para `historico/sessao-2026-10-15_manual-kunlun-ram.zip`.
- **Release v0.2.2-beta** (130597 bytes, CRC32 `E2FEF9BD`).

### Dia 8 — 2026-10-15 a 2026-10-18
- Templo de Nauthiz: ferramentas para guiar o utilizador a partir de save states — `analise/mapa_masmorra.py`
  (mapa completo, blocos raros), `analise/caminho_masmorra.py` (caminho mais curto) e `analise/saidas_masmorra.py`
  (escadas que sobem/descem, zona alcançável, estátuas).
- Script de usar objetos nas masmorras (`$1F:92FC`): tabela por nº do mapa; posições das 9 estátuas e dos pedestais.
- Ecrã negro em portas do Templo de Nauthiz: pilha cheia de `$04`; conserto manual em `$019A`. Ainda em investigação.
- **Erro do patch:** o envio da fonte usava o canal de DMA 7, que o jogo usa para HDMA (efeitos de ecrã); passou
  para o canal 6. O deslize dos retratos voltou à velocidade original. (O texto que reaparece entre painéis de
  narração é do jogo original.)
- **Release v0.2.3-beta** (130597 bytes, CRC32 `1B66CBD3`).
- Conversa exportada para `historico/sessao-2026-10-18_nauthiz-hdma.zip`.

---

## 10. Pendentes

Ver [ESTADO.md](ESTADO.md). Principais:
1. Revisão do guião a jogar (rascunho completo feito; nomes duvidosos no glossário).
2. Menus que ainda apareçam em japonês (usar blocos).
3. Gráficos: ecrã de introdução, nomes de cidades em kanji (ex.: 香港 no aeroporto).
4. Acabamentos: kana visíveis por um instante no início das mensagens; fonte de largura variável; patch `.bps` para distribuição.
