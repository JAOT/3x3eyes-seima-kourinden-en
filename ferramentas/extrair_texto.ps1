# Extrai o guião de "3x3 Eyes - Seima Kourinden (Japan).sfc"
# Uso: pwsh -File extrair_texto.ps1 -Rom "<caminho da rom>" [-Saida "<pasta>"]
#
# Formato do texto (descoberto por engenharia reversa):
#   - Tabela de ponteiros: ROM 0x68000 ($0D:8000), 4216 entradas de 3 bytes (endereço LoROM de 24 bits)
#   - Texto: ROM 0x6B168 em diante, 1 byte por carácter, sem compressão
#   - 01..B3 = glifos 16x16 (tabela de tiles em $00:ED89, índice = código-1)
#   - B4..CE = glifos 8x16 (dígitos, pontuação; tabela em $00:F321)
#   - CF..FE = peças de moldura (tabela em $00:F38D)
#   - 00     = fim de mensagem
#   - FF xx  = código de controlo (tabela de saltos em $00:E809), com 0-3 parâmetros
param(
  [Parameter(Mandatory)][string]$Rom,
  [string]$Saida = (Join-Path $PSScriptRoot '..')
)

$cs = @'
using System; using System.IO; using System.Text; using System.Collections.Generic;
public static class Seima {
  public const int PtrTable = 0x68000, MsgCount = 0x1078;

  // Códigos 01..B3 (índice = código-1)
  public const string Main =
    "アイウエオカキクケコサシスセソタ" + "チツテトナニヌネノハヒフヘホマミ" +
    "ムメモヤユヨワンラリルレロッャュ" + "ョァィゥェォガギグゲゴザジズゼゾ" +
    "ダヂヅデドバビブベボパピプペポヴ" + "あいうえおかきくけこさしすせそた" +
    "ちつてとなにぬねのはひふへほまみ" + "むめもやゆよわをんらりるれろっゃ" +
    "ゅょぁぃぅぇぉがぎぐげござじずぜ" + "ぞだぢづでどばびぶべぼぱぴぷぺぽ" +
    "精神体力三只眼鍵書殿像港魔術　ー" + "／＋・";
  // Códigos B4..CC (meia largura)
  public static readonly string[] Half = { "0","1","2","3","4","5","6","7","8","9","M","F","B"," ","「","」","、","。","！","？","″","◀","▶","◁","▷" };

  // Nº de parâmetros de cada código FF xx (lido dos tratadores em $00:E809)
  public static readonly int[] Params = {
    0,0,0,0,0,1,1,1, 1,2,0,0,0,0,0,0,   // 00-0F
    1,0,0,0,0,0,0,1, 0,1,1,0,0,2,2,2,   // 10-1F
    3,3,3,1,1,0,0,0, 0,0,1,1,1,1        // 20-2D
  };

  public static int LoRom(int p){ int bank=(p>>16)&0x7F, a=p&0xFFFF; return bank*0x8000 + (a-0x8000); }

  public static string Tbl(){
    var sb=new StringBuilder();
    for(int i=0;i<Main.Length;i++) sb.AppendFormat("{0:X2}={1}\n",i+1,Main[i]);
    for(int i=0;i<Half.Length;i++) sb.AppendFormat("{0:X2}={1}\n",0xB4+i,Half[i]);
    sb.Append("FF02={n}\nFF04={w}\nFF01={clr}\n/00\n");
    return sb.ToString();
  }

  // Descodifica a mensagem em 'off'; devolve o texto e o offset a seguir ao terminador
  public static string Decode(byte[] r,int off,out int end,out bool ok){
    var sb=new StringBuilder(); int p=off; ok=true;
    while(true){
      if(p>=r.Length){ ok=false; break; }
      int c=r[p++];
      if(c==0x00){ break; }
      if(c==0xFF){
        int k=r[p++];
        if(k>=Params.Length){ sb.AppendFormat("{{FF{0:X2}?}}",k); ok=false; continue; }
        if(k==0x00){ sb.Append("{fim}"); break; }
        if(k==0x01){ sb.Append("{clr}"); continue; }
        if(k==0x02){ sb.Append("{n}\n"); continue; }
        if(k==0x04){ sb.Append("{w}\n"); continue; }
        sb.AppendFormat("{{{0:X2}",k);
        for(int i=0;i<Params[k];i++) sb.AppendFormat(":{0:X2}",r[p++]);
        sb.Append("}");
        continue;
      }
      if(c>=1 && c<=Main.Length){ sb.Append(Main[c-1]); continue; }
      if(c>=0xB4 && c<0xB4+Half.Length){ sb.Append(Half[c-0xB4]); continue; }
      sb.AppendFormat("[{0:X2}]",c);
    }
    end=p; return sb.ToString();
  }

  public static string Run(byte[] r,string outTxt,out int bad,out int gaps){
    var sb=new StringBuilder(); bad=0; gaps=0;
    var ptrs=new int[MsgCount];
    for(int i=0;i<MsgCount;i++){ int o=PtrTable+i*3; ptrs[i]=r[o]|(r[o+1]<<8)|(r[o+2]<<16); }
    for(int i=0;i<MsgCount;i++){
      int off=LoRom(ptrs[i]); int end; bool ok;
      string t=Decode(r,off,out end,out ok);
      if(!ok) bad++;
      // a mensagem seguinte deve começar logo a seguir (ou ser um ponteiro repetido)
      if(i+1<MsgCount){ int nx=LoRom(ptrs[i+1]); if(nx!=end && nx>off && nx<end) gaps++; }
      sb.AppendFormat("#### {0:X4} @{1:X2}:{2:X4} (ROM 0x{3:X5}){4}\n",i,(ptrs[i]>>16)&0xFF,ptrs[i]&0xFFFF,off,ok?"":"  !!VERIFICAR");
      sb.Append(t.TrimEnd('\n')); sb.Append("\n\n");
    }
    File.WriteAllText(outTxt,sb.ToString(),new UTF8Encoding(false));
    return string.Format("{0} mensagens; {1} com bytes desconhecidos; {2} com sobreposição de ponteiros",MsgCount,bad,gaps);
  }
}
'@
if (-not ('Seima' -as [type])) { Add-Type -TypeDefinition $cs }

$bytes = [IO.File]::ReadAllBytes($Rom)
New-Item -ItemType Directory -Force $Saida | Out-Null
$txt = Join-Path $Saida 'guiao_jp.txt'
$bad = 0; $gaps = 0
[Seima]::Run($bytes, $txt, [ref]$bad, [ref]$gaps)
[IO.File]::WriteAllText((Join-Path $Saida 'tabela.tbl'), [Seima]::Tbl(), [Text.UTF8Encoding]::new($false))
"Guião: $txt"
