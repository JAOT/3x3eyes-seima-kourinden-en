param([string]$State,[string]$Out)
# Unpacks a Mesen2 .mss save state: screenshot.png, vram.bin, wram.bin, cgram.bin, and a key list
New-Item -ItemType Directory -Force $Out | Out-Null
$b=[IO.File]::ReadAllBytes($State)
$streams=@()
for($i=0;$i -lt $b.Length-2;$i++){ if($b[$i] -eq 0x78 -and ($b[$i+1] -in 0x01,0x5E,0x9C,0xDA)){
 try{ $ms=[IO.MemoryStream]::new($b,$i,$b.Length-$i); $z=[IO.Compression.ZLibStream]::new($ms,[IO.Compression.CompressionMode]::Decompress); $o=[IO.MemoryStream]::new(); $z.CopyTo($o); $d=$o.ToArray(); if($d.Length -gt 1000){ $streams+=,$d } } catch {} } }
$shot=$streams[0]; $st=$streams[1]
# screenshot: 32-bit ARGB or 16-bit; detect from size
Add-Type -AssemblyName System.Drawing.Common -ErrorAction SilentlyContinue
$px=$shot.Length
if($px -eq 256*239*4 -or $px -eq 256*224*4){ $bpp=4 } else { $bpp=2 }
$wd=256; $ht=[int]($px/($wd*$bpp))
$bmp=[System.Drawing.Bitmap]::new($wd,$ht)
for($y=0;$y -lt $ht;$y++){ for($x=0;$x -lt $wd;$x++){ $k=($y*$wd+$x)*$bpp
 if($bpp -eq 4){ $c=[System.Drawing.Color]::FromArgb(255,$shot[$k+2],$shot[$k+1],$shot[$k]) }
 else { $v=$shot[$k]+256*$shot[$k+1]; $c=[System.Drawing.Color]::FromArgb(255,(($v -band 31)*8),((($v -shr 5) -band 31)*8),((($v -shr 10) -band 31)*8)) }
 $bmp.SetPixel($x,$y,$c) } }
# GDI+ chokes on long paths, so save via a memory stream
$pm=[IO.MemoryStream]::new(); $bmp.Save($pm,[System.Drawing.Imaging.ImageFormat]::Png); [IO.File]::WriteAllBytes("$Out\screenshot.png",$pm.ToArray())
$p=0; $keys=@()
while($p -lt $st.Length){ $s=$p; while($p -lt $st.Length -and $st[$p] -ne 0){$p++}; $name=[Text.Encoding]::ASCII.GetString($st,$s,$p-$s); $p++; if($p+4 -gt $st.Length){break}; $sz=[BitConverter]::ToUInt32($st,$p); $p+=4; if($sz -gt 0x100000){break}
 switch($name){ 'ppu.vram'{[IO.File]::WriteAllBytes("$Out\vram.bin",$st[$p..($p+$sz-1)])} 'memoryManager.workRam'{[IO.File]::WriteAllBytes("$Out\wram.bin",$st[$p..($p+$sz-1)])} 'ppu.cgram'{[IO.File]::WriteAllBytes("$Out\cgram.bin",$st[$p..($p+$sz-1)])} }
 if($sz -le 4){ $val=0; for($k=0;$k -lt $sz;$k++){$val+=[long]$st[$p+$k] -shl (8*$k)}; $keys+=('{0}={1:X}' -f $name,$val) } else { $keys+=('{0} [{1}]' -f $name,$sz) }
 $p+=$sz }
$keys | Set-Content "$Out\keys.txt"
"screenshot ${wd}x$ht bpp=$bpp; keys=$($keys.Count)"
