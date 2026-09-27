from pathlib import Path
import sys,json
from collections import defaultdict
from PIL import Image
import pdfplumber
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'C:\geonet_beregning')
OUT=ROOT/'tmp/pdfs/codex-diagram-kontrol'
p=pdfplumber.open(ROOT/'Dokumenter og data/datablade og designmanualer/brochure-tensar-designmanual-sept-2024-1.pdf').pages[9]
colors={(1.0,0.932,0.256,0.137):'blue',(0.095,0.0,0.952,0.0):'yellow',(0.411,0.778,0.0,0.0):'purple'}
regions=[(60,190,285,365),(335,475,285,362),(60,180,474,552),(335,458,480,555),(65,188,672,749),(335,461,673,749)]
pdf=[]
for i,(l,r,t,b) in enumerate(regions,1):
    marks=defaultdict(list)
    for o in p.curves+p.rects:
        c=colors.get(o['non_stroking_color'])
        x=(o['x0']+o['x1'])/2;y=(o['top']+o['bottom'])/2
        if c and o['fill'] and l<x<r and t<y<b:
            marks[c].append([x,y])
    for pts in marks.values():pts.sort()
    grid=sorted(set(round(o['top'],5) for o in p.lines if o['stroking_color']==(0.912,0.787,0.62,0.974) and o['width']>100 and o['height']<0.0001 and l<o['x0']<r and t<o['top']<b))
    # Deduplicate subpixel offsets in the repeated zero-axis strokes.
    grid2=[]
    for y in grid:
        if not grid2 or y-grid2[-1]>.01:grid2.append(y)
    print('PDF',i,'grid',grid2,'markers',dict(marks))
    pdf.append({'grid':grid2,'markers':dict(marks)})
(OUT/'pdf-coordinates.json').write_text(json.dumps(pdf,indent=2))

# Local grid positions read from each PNG; individual grid bands are calibrated separately.
cfg=[
 dict(x=[140,185,227,272,317,359,404,447,491,536,579,623],xstart=0,ys=[531,490,449,407,364,323,282,241],step=5,starts={'purple':0,'blue':2},ends={'purple':11,'blue':9}),
 dict(x=[121,162,204,244,286,327,369,410,452,492,534,575,617,657],xstart=0,ys=[518,461,403,347,290,231],step=10,starts={'yellow':0,'blue':2,'purple':5},ends={'yellow':13,'blue':10,'purple':9}),
 dict(x=[128,163,199,234,268,303,339,374,410,445,479,514,550,586],xstart=10,ys=[516,457,399,340,282,224],step=10,starts={'yellow':0,'blue':1,'purple':4},ends={'yellow':13,'blue':10,'purple':9}),
 dict(x=[118,155,192,229,264,301,338,375,412,449,484,521,558,594],xstart=20,ys=[534,476,416,358,298,241],step=10,starts={'yellow':0,'blue':0,'purple':4},ends={'yellow':13,'blue':10,'purple':9}),
 dict(x=[136,172,208,244,281,317,353,389,426,462,498,534,570,606],xstart=30,ys=[521,463,406,347,289,232],step=10,starts={'yellow':0,'blue':0,'purple':2},ends={'yellow':13,'blue':10,'purple':10-1}),
 dict(x=[110,147,185,223,261,298,336,374,411,449,486,524,561,599],xstart=40,ys=[525,468,409,351,294,236],step=10,starts={'yellow':0,'blue':0,'purple':1},ends={'yellow':13,'blue':10,'purple':9}),
]
def interp(y,ys,step):
    for n in range(len(ys)-1):
        if ys[n]>=y>=ys[n+1]:return step*(n+(ys[n]-y)/(ys[n]-ys[n+1]))
    raise ValueError((y,ys))
data=[]
for i,c in enumerate(cfg,1):
    im=Image.open(ROOT/f'diagrambilleder/Diagram {i}.png').convert('RGB')
    refined=[]
    for nominal in c['ys']:
        weights=[]
        for yy in range(nominal-2,nominal+3):
            darkness=0
            for xx in range(c['x'][0]+6,c['x'][-1]-6):
                if any(abs(xx-gx)<5 for gx in c['x']):continue
                rgb=im.getpixel((xx,yy))
                if max(rgb)-min(rgb)<12:darkness+=255-sum(rgb)/3
            weights.append((yy,darkness))
        peak=max(w for _,w in weights)
        strong=[(y,w) for y,w in weights if w>peak*.2]
        refined.append(sum(y*w for y,w in strong)/sum(w for _,w in strong))
    c['ys']=refined
    res={}
    for color,start in c['starts'].items():
        pts=[]
        for k in range(start,c['ends'][color]+1):
            xx=c['x'][k];hist={}
            for y in range(int(c['ys'][-1]),int(c['ys'][0])+5):
                count=0
                for x in range(xx-3,xx+4):
                    R,G,B=im.getpixel((x,y))
                    good=(R>180 and G>180 and B<100) if color=='yellow' else ((90<R<210 and 40<G<160 and 100<B<220 and R>G*1.25) if color=='purple' else (R<90 and G<110 and B>80 and B>R*1.35))
                    count+=bool(good)
                if count:hist[y]=count
            peak=max(hist.values())
            # Thick marker rows; discard the thin incoming/outgoing curve.
            rows=[y for y,v in hist.items() if v>=max(4,peak-1)]
            center=(min(rows)+max(rows))/2
            # Triangles: center of bounding box of entire narrow central cross-section.
            if color=='yellow':center=(min(hist)+max(hist))/2
            val=interp(center,c['ys'],c['step'])
            pts.append({'h':c['xstart']+k*10,'y_pixel':center,'png':val})
        res[color]=pts
    print('PNG',i,{co:[(z['h'],round(z['png'],2)) for z in pp] for co,pp in res.items()})
    data.append(res)
(OUT/'png-readings.json').write_text(json.dumps(data,indent=2))

for i,(a,v,c) in enumerate(zip(data,pdf,cfg),1):
    diffs=[]
    for color,pts in a.items():
        assert len(pts)==len(v['markers'][color]),(i,color)
        for z,xy in zip(pts,v['markers'][color]):
            z['pdf']=interp(xy[1],list(reversed(v['grid'])),c['step'])
            z['diff']=abs(z['png']-z['pdf'])
            diffs.append(z['diff'])
    print('CHECK',i,'count',len(diffs),'max_diff',round(max(diffs),3),{co:[(z['h'],round(z['png'],1),round(z['pdf'],1)) for z in pp] for co,pp in a.items()})
(OUT/'checked-readings.json').write_text(json.dumps(data,indent=2))
for i,box in [(1,(420,445,640,546)),(3,(400,455,595,530)),(6,(365,458,610,540))]:
    im=Image.open(ROOT/f'diagrambilleder/Diagram {i}.png')
    im.crop(box).resize(((box[2]-box[0])*4,(box[3]-box[1])*4)).save(OUT/f'detail-{i}.png')
