# -*- coding: utf-8 -*-
import fitz, re, os
CISA="/sessions/epic-eloquent-hypatia/mnt/CISA"
B1=CISA+"/1 감리 및 사업관리/1-1 정보화법_제도_감리"; B2=CISA+"/1 감리 및 사업관리/1-2 사업관리"
PDF={
 "M02":B1+"/1.2 감리 법 지침_V1.0_20190328_최종본.pdf",
 "M03":B1+"/2. 감리 및 사업관리(25)_V1.3_2장 지침_5월 8일_최종본.pdf",
 "M05":B1+"/3. 감리 및 사업관리(25)_V1.1_3장 감리총론.pdf",
 "M07":B2+"/1. 정보시스템감리사_사업관리_V5.4_1장_4장_통합관리.pdf",
 "M08":B2+"/1.1 사업관리 특강 및 출제 예상_V1.2_20190328_최종본.pdf",
 "M09":B2+"/2. 정보시스템감리사_사업관리_V5.4_5장 범위관리 6장 시간관리.pdf",
 "M10":B2+"/3. 정보시스템감리사_사업관리_V5.4_7장 원가관리_8장 품질관리.pdf",
 "M11":B2+"/4. 정보시스템감리사_V5.5_9장 인적자원관리_11장 위험관리.pdf",
 "M12":B2+"/5. 정보시스템감리사_V5.4_12장 조달관리_13장 이해관계자관리.pdf",
}
NOISE=re.compile(r'감리사 합격을 위한 사업관리 총정리|itpe|ITPE|^\s*\d+\s*$')
def esc(x): return (x or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def clean_cell(c, split_items=False):
    if not c: return ""
    lines=[l.strip() for l in c.split("\n") if l.strip() and not NOISE.search(l)]
    txt=" ".join(lines); txt=esc(txt)
    if split_items:
        txt=re.sub(r'(\))\s+(?=[가-힣])', r'\1<br>', txt)   # 영문명 ) 뒤 한글 시작 항목
        txt=re.sub(r'(★+)\s+(?=[가-힣])', r'\1<br>', txt)
        txt=re.sub(r'\s+(?=\d+\.\s)', r'<br>', txt)
        txt=re.sub(r'\s+(?=[①-⑩])', r'<br>', txt)
    return txt.strip()
def page_title(pg):
    lines=[l.strip() for l in pg.get_text().split("\n") if l.strip() and not NOISE.search(l)]
    return lines[0][:60] if lines else ""
def tableize(pg, pnum):
    try: tabs=pg.find_tables().tables
    except: tabs=[]
    if not tabs: return None
    out=[]
    for tb in tabs:
        rows=tb.extract()
        if not rows: continue
        # 빈 열 제거
        ncol=max(len(r) for r in rows)
        rows=[r+[""]*(ncol-len(r)) for r in rows]
        keep=[j for j in range(ncol) if any((rows[i][j] or "").strip() for i in range(len(rows)))]
        rows=[[r[j] for j in keep] for r in rows]
        # 완전 빈 행 제거
        rows=[r for r in rows if any((c or "").strip() for c in r)]
        if not rows or len(rows)<1: continue
        # ITO 여부
        hdr=" ".join((c or "") for c in rows[0])
        ito = ("입력물" in hdr and "산출물" in hdr)
        html='<table>\n'
        if ito and len(rows)>=2:
            html+='  <tr>'+"".join(f'<th>{clean_cell(c)}</th>' for c in rows[0])+'</tr>\n'
            merged=[]
            for j in range(len(rows[0])):
                col=" ".join((rows[i][j] or "").replace("\n"," ") for i in range(1,len(rows)) if j<len(rows[i]))
                merged.append(clean_cell(col, split_items=True))
            html+='  <tr>'+"".join(f'<td style="vertical-align:top;">{m}</td>' for m in merged)+'</tr>\n'
        else:
            for i,r in enumerate(rows):
                tag="th" if i==0 else "td"
                cells="".join(f'<{tag}>{clean_cell(c, split_items=(i>0))}</{tag}>' for c in r)
                html+=f'  <tr>{cells}</tr>\n'
        html+='</table>'
        out.append(html)
    if not out: return None
    title=esc(re.sub(r'^\d+\.\s*','',page_title(pg)))
    cap=f'<p style="font-size:0.82rem;color:#64748b;margin:2px 0 6px;">▸ 원본 p.{pnum} 표 복원: {title}</p>'
    return cap+"\n"+"\n".join(out)
def textize(pg,pnum):
    lines=[l.strip() for l in pg.get_text().split("\n") if l.strip() and not NOISE.search(l)]
    drop={"출제 예상문제","출제예상문제","해설","출제 예상문제 & 기출 문제","문제 풀이","(정답) 강의 해설 참조"}
    lines=[l for l in lines if l not in drop]
    if not lines: return None
    title=esc(re.sub(r'^\d+\.\s*','',lines[0][:60])); rest=lines[1:]
    paras=[]; cur=""
    for l in rest:
        if re.match(r'^([①-⑩]|\d+[\.\)]|[가-힣]\.|[IVX]+\.)\s?', l):
            if cur: paras.append(cur)
            cur=l
        else:
            cur=(cur+" "+l).strip()
    if cur: paras.append(cur)
    cap=f'<p style="font-size:0.82rem;color:#64748b;margin:2px 0 6px;">▸ 원본 p.{pnum} 내용 복원: {title}</p>'
    ps="".join(f'<p>{esc(x)}</p>' for x in paras)
    return cap+"\n"+ps


# ---------- 적용부 ----------
import glob
HDIR=os.path.join(os.path.dirname(__file__),"감리및사업관리")
def hpath(code):
    return os.path.join(HDIR,[x for x in os.listdir(HDIR) if x.startswith(code)][0])
def good_tables(pg):
    try: tabs=pg.find_tables().tables
    except: return []
    res=[]
    for tb in tabs:
        rows=tb.extract()
        if not rows: continue
        ncol=max(len(r) for r in rows)
        rows=[r+[""]*(ncol-len(r)) for r in rows]
        keep=[j for j in range(ncol) if any((rows[i][j] or "").strip() for i in range(len(rows)))]
        rows=[[r[j] for j in keep] for r in rows]
        rows=[r for r in rows if any((c or "").strip() for c in r)]
        if len(rows)>=2 and len(rows[0])>=2: res.append(rows)
    return res
def classify(pg):
    t=pg.get_text(); tl=len(re.sub(r'\s','',t))
    gt=good_tables(pg)
    bigimg=any((im[2] or 0)*(im[3] or 0)>200000 for im in pg.get_images())
    ttext=sum(len(re.sub(r'\s','',(c or ""))) for rows in gt for r in rows for c in r)
    if gt and ttext>=0.45*max(tl,1) and ttext>=80: return "TABLE"
    if tl>=200 and not bigimg: return "TEXT"
    return "DIAGRAM"
def apply(code, dry=False):
    d=fitz.open(PDF[code]); hp=hpath(code); s=open(hp,encoding="utf-8").read()
    pages=sorted(set(int(x) for x in re.findall(r'/%sslides/p0*(\d+)\.jpg'%code, s)))
    log={}
    for m in list(re.finditer(r'(<section id="([^"]+)"[^>]*>)(.*?)(</section>)', s, re.S)):
        sid=m.group(2); body=m.group(3)
        figs=re.findall(r'<figure class="origpg"[^>]*>.*?/%sslides/p0*(\d+)\.jpg.*?</figure>'%code, body, re.S)
        if not figs: continue
        newbody=body; blocks=[]
        for fm in re.finditer(r'<figure class="origpg"[^>]*>.*?/%sslides/p0*(\d+)\.jpg.*?</figure>'%code, body, re.S):
            p=int(fm.group(1)); cls=classify(d[p-1])
            log.setdefault(cls,[]).append(p)
            if cls=="TABLE":
                blk=tableize(d[p-1],p)
            elif cls=="TEXT":
                blk=textize(d[p-1],p)
            else:
                blk=None
            if blk:
                blocks.append(blk)
                newbody=newbody.replace(fm.group(0),"")   # 이미지 제거
        if blocks:
            recon='\n      <div class="recon" style="margin:14px 0;">\n      '+"\n      ".join(blocks)+'\n      </div>\n'
            # 빈 origpg-wrap 정리
            newbody=re.sub(r'<div class="origpg-wrap"[^>]*>\s*</div>','',newbody)
            # 삽입 위치: 첫 quiz-container 앞, 없으면 남은 origpg-wrap 앞, 없으면 끝
            if '<div class="quiz-container">' in newbody:
                newbody=newbody.replace('<div class="quiz-container">', recon+'      <div class="quiz-container">',1)
            elif '<div class="origpg-wrap"' in newbody:
                newbody=newbody.replace('<div class="origpg-wrap"', recon+'      <div class="origpg-wrap"',1)
            else:
                newbody=newbody+recon
            s=s.replace(m.group(0), m.group(1)+newbody+m.group(4))
    if not dry: open(hp,"w",encoding="utf-8").write(s)
    return {k:sorted(v) for k,v in log.items()}
