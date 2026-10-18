; 3x3 Eyes - Seima Kourinden: patch para texto em inglês (Asar)
;
; 1) Texto: bytes $20-$7E (ASCII) passam a ser letras de meia largura (8x16).
;    Os restantes códigos continuam a usar a rotina original ($00:E378).
; 2) Fonte: o NMI envia a fonte inglesa para os tiles do BG3 que eram só dos kana,
;    um segmento por frame, enquanto houver texto em inglês a ser desenhado.
;
; Mapa de memória (ROM expandida para 2 MB):
;   $00:FC00  stubs no banco 00 (zona livre)
;   $20:8000  código e tabelas
;   $21:8000  gráficos da fonte

lorom

incsrc "gerado/font_en_defs.asm"

; Variáveis do patch em RAM livre ($7E:D000-EFFF está vazia nos save states e o código não lhe acede).
; ATENÇÃO: antes estavam em $7F:FF00-FF05, que é o fim do mapa das masmorras ($7F:8000-FFFF): estragavam
; 3 células do mapa (ex.: buraco na parede do labirinto da Treasury). Não usar $7F:8000-FFFF.
!Timer  = $7EE800   ; frames que faltam de reenvio da fonte
!SegIdx = $7EE802   ; próximo segmento a enviar

; --- ganchos no código original -------------------------------------------
; A rotina de glifos $00:E378 é chamada de ~30 sítios (diálogo, menus, combate),
; por isso o desvio fica na entrada da própria rotina. Original: PHX / JSR $E9D5.
org $00E378
    JMP TextHook

org $00FFEA          ; vetor NMI (modo nativo): era $80F9
    dw NmiStub

; --- código de controlo novo: FF 2E ll hh bb = continuar a ler o texto em $bb:hhll ----
; A tabela de saltos dos códigos FF xx ($00:E809, códigos $00-$2D) é copiada para $00:F600
; e ganha a entrada $2E. Serve para reescrever pedaços de menus noutro sítio (blocos_en.txt).
org $00E413
    LDA.w CtrlTable,y
org $00F600
CtrlTable:
    !i = 0
    while !i < $2E
        dw read2($00E809+(!i*2))
        !i #= !i+1
    endwhile
    dw CtrlGoto          ; $2E
CtrlGoto:                ; X = contexto do texto; E8F9 devolve o byte seguinte em A (16 bits)
    JSR $E8F9            ; endereço: byte baixo
    PHA
    LDA $14,x            ; sub-texto com limite de carateres (nomes de itens, locais...)?
    BEQ +
    LDA.w #$0040         ; o destino acaba em 0: limite alargado para nomes longos
    STA $14,x
+   PLA
    PHA
    JSR $E8F9            ; byte alto
    XBA
    ORA 1,s
    STA 1,s
    JSR $E8F9            ; banco
    STA $1A,x
    PLA
    STA $18,x
    RTS
assert pc() <= $00FC00

; --- nomes das personagens ------------------------------------------------
; As rotinas em $01:9A62/$01:9A77 copiavam 5 bytes (4 kana + 0) da tabela $01:D5A4
; para os buffers $7E:2252/$7E:2272. Agora copiam 9 bytes da tabela NameTable (banco $20).
org $019A68
    LDA.l NameTable,x
org $019A71
    LDA.w #$0008         ; MVN copia A+1 bytes
    MVN $7E,NameTable>>16
org $019A7D
    LDA.l NameTable,x
org $019A86
    LDA.w #$0008
    MVN $7E,NameTable>>16

; A rotina em $01:AF44 copia 4 palavras da tabela $01:D5D0 (banco 01).
; Passa a copiar 5 palavras (10 bytes); os nomes ficam no espaço da tabela antiga.
org $01AF4B
    LDA.w #$0005
org $01D5D0
    dw Name2_0, Name2_1, Name2_2
org $01D5A4
Name2_0: db "Takuhi",0,0,0,0
Name2_1: db "Fei-Oh",0,0,0,0
Name2_2: db "Hon-Nyan",0,0
assert pc() <= $01D5D0

; Segunda tabela de nomes ($00:ED32 -> nomes de 5 bytes em $00:ED40), usada pelo
; menu de estado ($00:DBC0) e pelos códigos {1A:xx} ($00:E5CA) e {2A:xx} ($00:E74F).
; Os ponteiros passam a apontar para os nomes ingleses e o banco da sub-string passa a $20.
; Como no original (nomes completados com espaços largos até 8 colunas), os nomes desta tabela têm 8 carateres,
; para taparem o "Poison"/"Numb" do estado quando o nome volta a ser desenhado. O guião não usa {1A}/{2A}.
org $00ED32
    dw NamePad_yakumo, NamePad_pai, NamePad_haan, NamePad_linlin
    dw NamePad_jake, NamePad_gupta, NamePad_sanjiyan
org $00DBC5
    LDA.w #NameTable>>16
org $00E5CF
    LDA.w #NameTable>>16
org $00E754
    LDA.w #NameTable>>16

; --- comandos de combate --------------------------------------------------
; Tabela $01:D3A9 -> 6 conjuntos de 6 comandos, 8 bytes cada (máx. 7 letras + 0).
; A rotina em $01:9ED3 copia um conjunto (48 bytes) para $7E:2200.
org $01D3B7
    db "Attack",0,0, "Magic",0,0,0, "Item",0,0,0,0, "Defend",0,0, "Run",0,0,0,0,0, "Regen",0,0,0
    db "Attack",0,0, "Magic",0,0,0, "Item",0,0,0,0, "Defend",0,0, "Run",0,0,0,0,0, "Awaken",0,0
    db "Attack",0,0, "Magic",0,0,0, "Item",0,0,0,0, "Defend",0,0, "Run",0,0,0,0,0, 0,0,0,0,0,0,0,0
    db "Attack",0,0, "Item",0,0,0,0, "Defend",0,0, "Run",0,0,0,0,0, 0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0
    db "Attack",0,0, "Item",0,0,0,0, "Defend",0,0, "Run",0,0,0,0,0, 0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0
    db "Attack",0,0, "Magic",0,0,0, "Item",0,0,0,0, "Defend",0,0, "Run",0,0,0,0,0, 0,0,0,0,0,0,0,0
assert pc() == $01D4D7

; --- atributos (subida de nível) -------------------------------------------
; Ponteiros em $01:DB45 -> 7 nomes de 8 bytes em $01:DB53, copiados (8 bytes) para $7E:2252 em $01:9AB6.
; たいりょく/せいしんりょく/わんりょく/きゃくりょく/しゅびりょく/ちりょく/うん
org $01DB53
    db "Body",0,0,0,0, "Mind",0,0,0,0, "Power",0,0,0, "Speed",0,0,0
    db "Defense",0, "Wisdom",0,0, "Luck",0,0,0,0
assert pc() == $01DB8B

; --- Body/Mind -------------------------------------------------------------
; Cada kanji de largura inteira (16 px) passa a mostrar duas letras inglesas:
; 体力 (A3 A4) -> "Body", 精神 (A1 A2) -> "Mind". Não muda nenhum menu.
; Entrada na tabela de glifos $00:ED89 (código-1)*8: cima-esq, baixo-esq, cima-dir, baixo-dir.
macro wide(code, c1, c2)
    org $00ED89+((<code>-1)*8)
    dw !GT_<c1>, !GB_<c1>, !GT_<c2>, !GB_<c2>
endmacro
%wide($A3, 42, 6F)   ; 体 -> "Bo"
%wide($A4, 64, 79)   ; 力 -> "dy"
%wide($A1, 4D, 69)   ; 精 -> "Mi"
%wide($A2, 6E, 64)   ; 神 -> "nd"

; janela de quantidade: o contador "コ" a seguir ao número passa a espaço
org $0F9852 : db $C1

; rótulos dos menus (menus_en.tsv -> menus.py): pares de letras em códigos de katakana
incsrc "gerado/menus.asm"

; nomes de feitiços, inimigos e itens (nomes_en.tsv -> nomes.py)
incsrc "gerado/nomes.asm"

; campos de largura fixa: locais e sim/não (campos_en.tsv -> campos.py)
incsrc "gerado/campos.asm"

; blocos de menus reescritos no banco $21 (blocos_en.txt -> blocos.py), via código FF 2E
incsrc "gerado/blocos.asm"

; --- fonte inglesa enviada logo quando o jogo carrega a fonte de diálogo -----------
; O carregador de gráficos ($00:865D, A = nº do descritor) descomprime a fonte de diálogo (#000/#001)
; diretamente para a VRAM. À saída ($00:86EF), se foi a fonte, as letras inglesas são copiadas por cima,
; para não aparecerem kana nos primeiros frames das mensagens. (Assim o patch não leva a fonte original.)
!LastDesc = $7EE804
org $00865D
    JMP LoadHookIn       ; era REP #$30 / PHP / PHB / PHA
org $0086EF
    JMP LoadHookOut      ; era PLB / PLP / RTS
org $00FE60
LoadHookIn:
    REP #$30
    STA.l !LastDesc
    PHP
    PHB
    PHA
    JMP $8662
LoadHookOut:
    PHP
    REP #$30
    PHA
    LDA.l !LastDesc
    CMP.w #$0002
    BCS +
    JSL FontUploadAll
+   PLA
    PLP
    PLB
    PLP
    RTS
assert pc() <= $00FFB0

; páginas gráficas da introdução (intro_en.txt -> intro.py): glifos e mapas novos no banco $38
incsrc "gerado/intro.asm"

; 精神力 (força mental) nos menus: o 力 passa a espaço, para ficar "Mind" e não "Minddy"
org $0F99F1 : db $AF
org $0F9E40 : db $AF
org $0F9F07 : db $AF

; 体　力 (com espaço, alinhado com 精神力) -> 体力　, para ficar "Body" e não "Bo  dy"
org $0F99D4 : db $A4,$AF
org $0F9E25 : db $A4,$AF
org $0F9EEC : db $A4,$AF

; --- estado de saúde no ecrã de estado -------------------------------------
; {08:06}/{08:07} usam as entradas 6 e 7 da tabela $00:ECF0 (ponteiros de 3 bytes)
; para "けんこう" e "　　どく" no banco 00. Passam a apontar para inglês no banco $20.
org $00ECF0+(6*3)
    dl StatusHealthy, StatusPoison, StatusNumb     ; entrada 8: "　　まひ" (paralisia)

; Janela de combate: em vez do nome, a rotina $00:DBE2 mostra o estado com sub-textos no banco 00
; ($00:DC19 "ど　く" = veneno, $00:DC1E "マ　ヒ" = paralisia). Passam a apontar para inglês no banco 00.
org $00DBE6 : dw BattlePoison
org $00DBEE : dw BattleNumb
org $00DC07 : dw BattlePoison
org $00FCC0
BattlePoison: db "Poison  ",0   ; 8 carateres: tapa o nome todo (até 8 letras)
BattleNumb:   db "Numb    ",0
assert pc() <= $00FD00

; --- stubs no banco 00 ----------------------------------------------------
org $00FC00
TextHook:            ; A/X 16 bits, X = estrutura da janela, $04 = código do carácter
    PHX              ; (instruções originais de $E378)
    JSR $E9D5        ; calcula X = posição no mapa de tiles ($7E:3000)
    LDA $04
    CMP.w #$0020
    BCC .orig
    CMP.w #$007F
    BCS .orig
    JSL LatinGlyph
    PLX
    LDA.w #$0002     ; avanço: 1 tile
    RTS
.orig
    LDA.w #$0010         ; glifos da tabela original também podem usar letras inglesas (Body/Mind)
    STA.l !Timer
    JMP $E37C            ; resto da rotina original (termina com PLX / RTS)

NmiStub:
    JML NmiFar

; --- código no banco $20 --------------------------------------------------
org $208000
LatinGlyph:
    PHB
    PHY
    PHK
    PLB
    LDA $04
    SEC
    SBC.w #$0020
    ASL
    ASL
    TAY
    LDA.w GlyphMap,y
    STA.l $7E3000,x
    LDA.w GlyphMap+2,y
    STA.l $7E3040,x
    LDA.w #$0010
    STA.l !Timer
    PLY
    PLB
    RTL

NmiFar:
    PHP
    REP #$30
    PHA
    PHX
    LDA.l !Timer
    BEQ .done
    DEC
    STA.l !Timer
    LDA.l !SegIdx
    CMP.w #!FontSegCount
    BCC +
    LDA.w #$0000
+   TAX
    INC
    CMP.w #!FontSegCount
    BCC +
    LDA.w #$0000
+   STA.l !SegIdx
    TXA
    ASL
    ASL
    ASL
    TAX
    SEP #$20
    LDA.b #$80
    STA.l $002115
    REP #$20
    LDA.l FontSegs,x
    CLC
    ADC.l $0000DC        ; base de caracteres do BG3 (cópia do jogo: $3000 no campo, $2000 no combate)
    STA.l $002116
    LDA.w #$1801         ; DMA canal 6: modo 1 (2 registos) -> $2118 (o jogo usa o canal 7 para HDMA: não usar)
    STA.l $004360
    LDA.l FontSegs+2,x
    STA.l $004362
    LDA.l FontSegs+4,x
    STA.l $004365
    SEP #$20
    LDA.b #FontGfx>>16
    STA.l $004364
    LDA.b #$40          ; canal 6
    STA.l $00420B
.done
    REP #$30
    PLX
    PLA
    PLP
    JML $0080F9          ; NMI original

FontUploadAll:       ; envia todos os segmentos da fonte inglesa (chamado logo após o jogo carregar a fonte)
    PHP
    REP #$30
    PHX
    LDA.w #$0000
    STA.l !Timer         ; o NMI deixa de enviar segmentos (e não mexe no canal 6 a meio)
    SEP #$20
    LDA.b #$80
    STA.l $002115
    REP #$20
    LDX.w #$0000
.seg
    LDA.l FontSegs,x
    CLC
    ADC.l $0000DC        ; base de caracteres do BG3 (mesma conta do NMI e do carregador)
    STA.l $002116
    LDA.w #$1801
    STA.l $004360
    LDA.l FontSegs+2,x
    STA.l $004362
    LDA.l FontSegs+4,x
    STA.l $004365
    SEP #$20
    LDA.b #FontGfx>>16
    STA.l $004364
    LDA.b #$40          ; canal 6
    STA.l $00420B
    REP #$20
    TXA
    CLC
    ADC.w #$0008
    TAX
    CPX.w #!FontSegCount*8
    BCC .seg
    PLX
    PLP
    RTL

NameTable:           ; ponteiros (banco $20) para nomes de 9 bytes
    dw .yakumo, .pai, .haan, .linlin, .jake, .gupta, .sanjiyan
.yakumo:   db "Yakumo",0,0,0
.pai:      db "Pai",0,0,0,0,0,0
.haan:     db "Haan",0,0,0,0,0
.linlin:   db "Lin-Lin",0,0
.jake:     db "Jake",0,0,0,0,0
.gupta:    db "Gupta",0,0,0,0
.sanjiyan: db "Sanjiyan",0

NamePad:             ; nomes com 8 carateres (tabela $00:ED32: menu de estado)
.yakumo:   db "Yakumo  ",0
.pai:      db "Pai     ",0
.haan:     db "Haan    ",0
.linlin:   db "Lin-Lin ",0
.jake:     db "Jake    ",0
.gupta:    db "Gupta   ",0
.sanjiyan: db "Sanjiyan",0

StatusHealthy: db "Healthy ",0   ; 8 carateres, como os originais (4 de largura inteira)
StatusPoison:  db "Poison  ",0
StatusNumb:    db "Numb    ",0

incsrc "gerado/font_en.asm"

org $218000
FontGfx:
    incbin "gerado/font_en.bin"

; livros e textos lidos no menu (Atlas, Pyramid Book...): tabela $0E:8000 reapontada para o banco $33 (livros.py)
incsrc "gerado/livros.asm"

; janela das respostas aos Kaiyan Generals ($0F:A1C4): cabeçalho [ponteiro][largura][altura] em $0F:A1BC.
; Largura (meios tiles) $16 -> $1A, para caber "Body Heat".
org $0FA1BE : db $1A

; --- nomes dos países (menu de destinos do aeroporto, mapa do mundo) ------------------
; A rotina $00:E638 (código FF 20) lia o nome em $0C:CF07 + nº*4 (4 carateres; "HongKong" em pares de letras).
; Passa a ler da tabela CountryNames (banco $20), com 16 bytes por país e limite de 16 carateres.
org $00E64B : dw $0010               ; tamanho de cada entrada (era 4)
org $00E654 : dw CountryNames        ; base da tabela (era $CF07)
org $00E659 : dw CountryNames>>16    ; banco (era $0C)
org $00E65E : dw $0010               ; limite de carateres do sub-texto (era 5)
; janela do menu de destinos ($0F:A145: [ponteiro][largura][altura]): largura $16 -> $1A, para "Hong Kong"
org $0FA147 : db $1A

org $20F000
CountryNames:        ; nº 0-4, como em $0C:CF07 (0 = vazio)
    db 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    db "Hong Kong",0,0,0,0,0,0,0
    db "Greece",0,0,0,0,0,0,0,0,0,0
    db "Mexico",0,0,0,0,0,0,0,0,0,0
    db "India",0,0,0,0,0,0,0,0,0,0,0

