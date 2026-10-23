# -*- coding: utf-8 -*-
# 범용 도형 크롭(다중 컬럼 대응): python3 _crop_year.py <YEAR> <slug_dir> <qnum:page_idx> ...
import fitz, re, os, sys
YEAR=sys.argv[1]; SLUG=sys.argv[2]
PDFS={"2025":"1 기출문제/2025년(제26회) 정보시스템 감리사 필기시험 문제 및 답안.pdf",
 "2021":"1 기출문제/2021년(제22회) 정보시스템 감리사 필기시험 문제 및 답안.pdf",
 "2022":"1 기출문제/2022년(제23회) 정보시스템 감리사 필기시험 문제 및 답안.pdf",
 "2023":"1 기출문제/2023년(제24회) 정보시스템 감리사 필기시험 문제 및 답안.pdf",
 "2024":"1 기출문제/2024년(제25회) 정보시스템 감리사 필기시험 문제.pdf",
 "2016":"1 기출문제/2016년(제17회) 정보시스템 감리사 필기시험 문제 및 답안.pdf",
 "2017":"1 기출문제/2017년(제18회) 정보시스템 감리사 필기시험 문제 및 답안.pdf",
 "2018":"1 기출문제/2018년(제19회) 정보시스템 감리사 필기시험 문제 및 답안.pdf",
 "2026":"1 기출문제/2026년(제27회) 정보시스템 감리사 필기시험 문제 및 답안.pdf"}
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=fitz.open(os.path.join(ROOT,PDFS[YEAR]))

def qlines(pg):
    out=[]
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines",[]):
            txt="".join(s["text"] for s in l["spans"]).strip()
            m=re.match(r'^(\d+)\.\s',txt)
            if m: out.append((int(m.group(1)), l["bbox"][0], l["bbox"][1], l["bbox"][3]))
    return out

def columns(pg):
    xs=sorted(set(round(x) for _,x,_,_ in qlines(pg)))
    cols=[]
    for x in xs:
        if not cols or x-cols[-1]>60: cols.append(x)
        # else same column cluster
    return cols  # 정렬된 컬럼 좌측 경계들

def crop(qnum,page_idx,pad=6,zoom=3.5):
    pg=d[page_idx]
    ql=qlines(pg); cols=columns(pg)
    me=[q for q in ql if q[0]==qnum]
    if not me: print(f"Q{qnum}: not found p{page_idx}"); return
    _,qx,qy0,qy3=me[0]
    # 이 문항이 속한 컬럼 좌/우 경계
    left=max([c for c in cols if c<=qx+1], default=qx)
    right=min([c for c in cols if c>left+1], default=pg.rect.width)
    band=(left-2, right-2)  # 오른쪽 컬럼 시작 직전까지
    def incol(cx): return band[0]<=cx<band[1]
    y0=qy3
    # 같은 컬럼 내 다음 문항 top
    y1=pg.rect.height
    for n,x,yy0,yy3 in ql:
        if n>qnum and incol(x) and yy0>y0: y1=min(y1,yy0)
    # 같은 컬럼 내 첫 ① top
    mid=None
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines",[]):
            t="".join(s["text"] for s in l["spans"]).strip()
            if t[:1]=="①":
                cx=(l["bbox"][0]+l["bbox"][2])/2
                if incol(cx) and y0<l["bbox"][1]<y1: mid=l["bbox"][1] if mid is None else min(mid,l["bbox"][1])
    yopt=mid
    ymax = yopt-2 if yopt else y1
    draws=[]; imgs=[]
    for dr in pg.get_drawings():
        r=dr['rect']; cx=(r[0]+r[2])/2
        if incol(cx) and y0-2<=r[1] and r[3]<=ymax+2:
            draws.append((min(r[0],r[2]),min(r[1],r[3]),max(r[0],r[2]),max(r[1],r[3])))
    for ii in pg.get_image_info():
        r=ii['bbox']; cx=(r[0]+r[2])/2
        if incol(cx) and y0-2<=r[1] and r[3]<=ymax+2:
            imgs.append((r[0],r[1],r[2],r[3]))
    if imgs:
        iy0=min(r[1] for r in imgs); iy1=max(r[3] for r in imgs)
        keep=list(imgs)
        for r in draws:
            cy=(r[1]+r[3])/2; h=r[3]-r[1]
            if iy0-16<=cy<=iy1+16 and not (cy<iy0-1 and h<5): keep.append(r)
        rects=keep
    else:
        # 벡터 전용: 얇은 밑줄(강조선) 제외 후 최대 군집 사용
        big=[r for r in draws if (r[3]-r[1])>=5 or (r[2]-r[0])>=40]
        rects=big if big else draws
    rects=[r for r in rects if (r[2]-r[0])>=0.5 or (r[3]-r[1])>=0.5]
    if not rects: print(f"Q{qnum}: no figure rects band={band} y0={y0:.0f} y1={y1:.0f}"); return
    # 밑줄로 인한 상단 과포함 방지: 본체(가장 큰 요소) 기준 상단 정리
    anchor=max(rects,key=lambda r:(r[2]-r[0])*(r[3]-r[1]))
    top_lim=anchor[1]-40
    rects=[r for r in rects if r[3]>=top_lim]
    fx0=min(r[0] for r in rects); fy0=min(r[1] for r in rects)
    fx1=max(r[2] for r in rects); fy1=max(r[3] for r in rects)
    if yopt: fy1=min(fy1, yopt-2)
    clip=fitz.Rect(max(band[0],fx0-pad), max(y0-2,fy0-pad), min(band[1],fx1+pad), fy1+pad)
    pix=pg.get_pixmap(matrix=fitz.Matrix(zoom,zoom),clip=clip)
    outdir=os.path.join(os.path.dirname(os.path.abspath(__file__)),"기출해설",SLUG,"assets",YEAR); os.makedirs(outdir,exist_ok=True)
    path=os.path.join(outdir,f"q{qnum}.png"); pix.save(path)
    print(f"Q{qnum} p{page_idx} band=({band[0]:.0f},{band[1]:.0f}) -> q{qnum}.png ({pix.width}x{pix.height}) y0={y0:.0f} y1={fy1:.0f} opt={yopt}")

for a in sys.argv[3:]:
    q,p=a.split(":"); crop(int(q),int(p))
