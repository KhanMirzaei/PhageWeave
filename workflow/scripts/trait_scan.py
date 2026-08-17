#!/usr/bin/env python3
"""Derive auditable phage interaction traits from annotations/proteins.

This is a conservative annotation bridge: curated keyword matches are evidence,
not proof of function. It consumes Pharokka product annotations when present
and falls back to protein identifiers/sequences so the report remains useful
when a large annotation database is unavailable.
"""
import csv, re, sys
from pathlib import Path

TRAITS = {
    'depolymerase': r'depolymerase|polysaccharide lyase|capsule|tailspike|tail spike|pectate lyase|hyaluronidase|glycosidase',
    'anti_defense': r'anti[- ]?(crispr|cbass|pycsar|defen[cs]e)|acr[a-z0-9_-]*|defense inhibitor',
    'sie': r'superinfection exclusion|sie\b|exclusion protein|imm\b|repressor|integrase|lysogenic',
    'rbp': r'receptor[- ]binding|tail fiber|tail fibre|tailspike|baseplate|adsorption',
    'lysis': r'endolysin|holin|spanin|lysis protein|lysin',
}

def annotations(mod):
    """Return (sample, text, protein_count) rows from Pharokka output."""
    out=[]
    for tsv in Path(mod).glob('pharokka/*product*.tsv'):
        with tsv.open(errors='ignore') as h:
            for r in csv.DictReader(h, delimiter='\t'):
                sample=(r.get('contig') or r.get('sequence') or '').split()[0]
                text=' '.join(str(v) for v in r.values())
                if sample: out.append((sample,text))
    # Pharokka's Prodigal table is always available when gene calling worked.
    if not out:
        for tsv in Path(mod).glob('pharokka/cleaned*.tsv'):
            with tsv.open(errors='ignore') as h:
                for r in csv.DictReader(h, delimiter='\t'):
                    sample=(r.get('contig') or '').split()[0]
                    if sample: out.append((sample,' '.join(r.values())))
    return out

def main():
    if len(sys.argv)!=4: raise SystemExit('usage: trait_scan.py RAW_FEATURES MODULE_DIR OUTPUT_FEATURES')
    raw,mod,out=map(Path,sys.argv[1:]); rows=list(csv.DictReader(raw.open(),delimiter='\t'))
    ann=annotations(mod)
    depp={}
    dp=mod/'depp_predictions.csv'
    if dp.exists():
        with dp.open(errors='ignore') as h:
            for r in csv.DictReader(h):
                try: depp[r.get('name','').split()[0]]=float(r.get('Probability_DePol',''))
                except (TypeError,ValueError): pass
    amap={}
    ap=mod/'sample_aliases.tsv'
    if ap.exists():
        with ap.open() as h:
            for r in csv.DictReader(h,delimiter='\t'):
                amap[r.get('sample','')]=r.get('sequence_id','')
    for row in rows:
        aliases={row.get('sample',''), Path(row.get('file','')).stem, amap.get(row.get('sample',''),'')}
        texts=[text.lower() for sample,text in ann if sample in aliases or sample.startswith(row.get('sample',''))]
        text=' '.join(texts)
        contig=amap.get(row.get('sample',''), '')
        dp_scores=[v for k,v in depp.items() if k.startswith(contig) or k.startswith(row.get('sample',''))]
        row['depolymerase_score']=f'{max(dp_scores):.4f}' if dp_scores else ''
        rbp_hits=len(re.findall(TRAITS['rbp'], text, re.I))
        row['rbp_candidate_count']=rbp_hits
        row['rbp_score']=f'{min(1.0,rbp_hits/max(1,int(row.get("protein_count",0)))):.4f}'
        for trait,pat in TRAITS.items(): row[trait]=int(bool(re.search(pat,text,re.I)))
        if dp_scores: row['depolymerase']=int(max(dp_scores)>=0.5)
        row['trait_evidence_count']=sum(row.get(t,'0') in (1,'1') for t in TRAITS)
        row['trait_annotation_status']='annotated' if texts else 'not_available'
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=rows[0].keys() if rows else [],delimiter='\t');w.writeheader();w.writerows(rows)
if __name__=='__main__': main()
