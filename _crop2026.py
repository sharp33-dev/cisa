# -*- coding: utf-8 -*-
import fitz, re, os
PDF="/sessions/epic-eloquent-hypatia/mnt/CISA/6 기출문제/2026년(제27회) 정보시스템 감리사 필기시험 문제 및 답안.pdf"
d=fitz.open(PDF)
def qtop(pg, qnum):
    mid=pg.rect.width/2
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines",[]):
            txt="".join(s["text"] for s in l["spans"]).strip()
            m=re.match(r'^(\d+)\.\s',txt)
            if m and int(m.group(1))==qnum:
                col='L' if (l["bbox"][0]+l["bbox"][2])/2<mid else 'R'
                return l["bbox"], col
    return None,None
def next_qtop(pg, qnum, col):
    mid=pg.rect.width/2; best=pg.rect.height
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines",[]):
            txt="".join(s["text"] for s in l["spans"]).strip()
            m=re.match(r'^(\d+)\.\s',txt)
            if m and int(m.group(1))>qnum:
                c='L' if (l["bbox"][0]+l["bbox"][2])/2<mid else 'R'
                if c==col and l["bbox"][1]>0: best=min(best,l["bbox"][1])
    return best
def option_top(pg, qnum, col, y0, y1):
    # 첫 ① 라인 y (stem-figure에서 figure 하단 경계로 사용)
    mid=pg.rect.width/2
    cand=[]
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines",[]):
            txt="".join(s["text"] for s in l["spans"]).strip()
            if txt[:1]=="①":
                c='L' if (l["bbox"][0]+l["bbox"][2])/2<mid else 'R'
                if c==col and y0<l["bbox"][1]<y1: cand.append(l["bbox"][1])
    return min(cand) if cand else None
def crop(qnum, page_idx, slug, mode='stem', pad=6, zoom=3.5):
    pg=d[page_idx]; mid=pg.rect.width/2
    qb,col=qtop(pg,qnum); assert qb, f"Q{qnum} not found"
    y0=qb[3]; y1=next_qtop(pg,qnum,col)
    xr=(0,mid) if col=='L' else (mid,pg.rect.width)
    # 그림 요소(드로잉+이미지) 수집
    rects=[]
    for dr in pg.get_drawings():
        r=dr['rect']
        if xr[0]<=(r[0]+r[2])/2<xr[1] and y0-2<=r[1] and r[3]<=y1+2: rects.append(fitz.Rect(r))
    for ii in pg.get_image_info():
        r=fitz.Rect(ii['bbox'])
        if xr[0]<=(r[0]+r[2])/2<xr[1] and y0-2<=r.y0 and r.y1<=y1+2: rects.append(r)
    imgs_reg=[]
    for ii in pg.get_image_info():
        r=fitz.Rect(ii['bbox'])
        if xr[0]<=(r.x0+r.x1)/2<xr[1] and y0-2<=r.y0 and r.y1<=y1+2: imgs_reg.append(r)
    if mode=='stem' and imgs_reg:
        iy0=min(r.y0 for r in imgs_reg); iy1=max(r.y1 for r in imgs_reg)
        # 래스터 수직범위와 겹치는 드로잉만 포함(도형 라벨/박스테두리)
        keep=[r for r in imgs_reg]
        for dr in pg.get_drawings():
            rr=dr['rect']; cy=(rr[1]+rr[3])/2; h=abs(rr[3]-rr[1])
            if not (xr[0]<=(rr[0]+rr[2])/2<xr[1] and iy0-14<=cy<=iy1+14): continue
            if cy<iy0-1 and h<5: continue   # 래스터 위쪽의 얇은 밑줄(강조선) 제외
            keep.append(fitz.Rect(rr))
        rects=keep
    if not rects:
        print(f"Q{qnum}: no figure rects"); return None
    nr=[]
    for r in rects:
        x0,y0r,x1,y1r=min(r.x0,r.x1),min(r.y0,r.y1),max(r.x0,r.x1),max(r.y0,r.y1)
        if x1-x0<0.5 and y1r-y0r<0.5: continue
        nr.append((x0,y0r,x1,y1r))
    fig=fitz.Rect(min(a[0] for a in nr),min(a[1] for a in nr),max(a[2] for a in nr),max(a[3] for a in nr))
    if mode=='stem':
        # 옵션 위까지로 상한(옵션이 텍스트인 경우 figure가 옵션 위)
        ot=option_top(pg,qnum,col,y0,y1)
        if ot: fig.y1=min(fig.y1, ot-2)
    # 컬럼 경계로 클립 + 패딩
    clip=fitz.Rect(max(xr[0],fig.x0-pad), max(y0-2,fig.y0-pad), min(xr[1],fig.x1+pad), fig.y1+pad)
    pix=pg.get_pixmap(matrix=fitz.Matrix(zoom,zoom), clip=clip)
    outdir=os.path.join(slug,"assets","2026"); os.makedirs(outdir,exist_ok=True)
    path=os.path.join(outdir,f"q{qnum}.png"); pix.save(path)
    print(f"Q{qnum} -> {path}  ({pix.width}x{pix.height})")
    return path
if __name__=="__main__":
    import sys
