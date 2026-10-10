using System; using System.IO; using System.Collections.Generic; using System.Linq; using System.Text;
public static class TraceScan {
  public class Stat { public long Count; public HashSet<int> Offs=new HashSet<int>(); public string Sample; public int FirstFrame=-1, LastFrame; }
  static int Hex(string s,int i,int n){ int v=0; for(int k=0;k<n;k++){ char c=s[i+k]; int d=c<='9'?c-'0':(c&~32)-'A'+10; if(d<0||d>15) return -1; v=v*16+d;} return v; }
  // LoROM: bank 00-7D/80-FF, addr >= 8000 -> rom offset
  public static int RomOff(int ea){ int bank=(ea>>16)&0x7F, addr=ea&0xFFFF; if(bank>=0x7E) return -1; if(addr<0x8000) return -1; return bank*0x8000+(addr-0x8000); }
  public static string Scan(string path){
    var stats=new Dictionary<int,Stat>(); long lines=0, cpu=0;
    foreach(var line in File.ReadLines(path)){
      lines++;
      if(line.Length<40 || line[6]!=' ' || line[7]!=' ') continue;
      int pc=Hex(line,0,6); if(pc<0) continue; cpu++;
      int b=line.IndexOf("[$",8); if(b<0||b>60) continue;
      int ea=Hex(line,b+2,6); if(ea<0) continue;
      int off=RomOff(ea); if(off<0) continue;
      string mn=line.Substring(8,3); if(mn=="JSR"||mn=="JSL"||mn=="JMP"||mn=="JML"||mn=="PEA") continue;
      Stat st; if(!stats.TryGetValue(pc,out st)){ st=new Stat(); st.Sample=line.Substring(0,Math.Min(line.Length,90)); stats[pc]=st; }
      st.Count++; st.Offs.Add(off);
      int fi=line.IndexOf("Fr:"); if(fi>0){ int e=fi+3; int f=0; while(e<line.Length&&char.IsDigit(line[e])){f=f*10+(line[e]-'0');e++;} if(st.FirstFrame<0)st.FirstFrame=f; st.LastFrame=f; }
    }
    var sb=new StringBuilder(); sb.AppendLine("lines="+lines+" cpu="+cpu);
    foreach(var kv in stats.OrderByDescending(k=>k.Value.Offs.Count).Take(40)){
      var o=kv.Value.Offs; sb.AppendLine(string.Format("PC {0:X6} reads={1} distinct={2} rom {3:X6}-{4:X6} fr {5}-{6} | {7}",kv.Key,kv.Value.Count,o.Count,o.Min(),o.Max(),kv.Value.FirstFrame,kv.Value.LastFrame,kv.Value.Sample));
    }
    return sb.ToString();
  }
  // dump all lines whose PC is in the given set (up to max), for inspecting routines
  public static string Grab(string path,int pcLo,int pcHi,int max,int skip){
    var sb=new StringBuilder(); int n=0, s=0;
    foreach(var line in File.ReadLines(path)){
      if(line.Length<40 || line[6]!=' ') continue; int pc=Hex(line,0,6); if(pc<pcLo||pc>pcHi) continue;
      if(s++<skip) continue; sb.AppendLine(line.Length>130?line.Substring(0,130):line); if(++n>=max) break; }
    return sb.ToString();
  }
}
