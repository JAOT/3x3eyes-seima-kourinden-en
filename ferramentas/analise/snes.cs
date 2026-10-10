using System; using System.Drawing; using System.Drawing.Imaging;
public static class Snes {
 // bpp 1,2,4 SNES planar 8x8 tiles. scale s, w tiles per row
 public static void Tiles(byte[] r,int off,int count,int w,int bpp,int s,string path){
  int ts=bpp*8; int h=(count+w-1)/w; var bmp=new Bitmap(w*8*s,h*8*s);
  int max=(1<<bpp)-1;
  for(int t=0;t<count;t++){int o=off+t*ts; if(o+ts>r.Length)break; int tx=(t%w)*8*s, ty=(t/w)*8*s;
   for(int y=0;y<8;y++)for(int x=0;x<8;x++){int bit=7-x,v=0;
    if(bpp==1)v=(r[o+y]>>bit)&1;
    else{ v=((r[o+y*2]>>bit)&1)|(((r[o+y*2+1]>>bit)&1)<<1);
      if(bpp==4) v|=(((r[o+16+y*2]>>bit)&1)<<2)|(((r[o+16+y*2+1]>>bit)&1)<<3);}
    int c=255-v*255/max; var col=Color.FromArgb(c,c,c);
    for(int a=0;a<s;a++)for(int b=0;b<s;b++)bmp.SetPixel(tx+x*s+a,ty+y*s+b,col);}}
  bmp.Save(path,ImageFormat.Png);}
}
