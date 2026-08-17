"""Merge module outputs into per-phage feature rows.

Missing module results are represented as ``not_available``/``not_run`` rather
than as biological negatives. This distinction is important for pair scoring.
"""
import csv, json, sys
from pathlib import Path

def fnum(value):
    try: return float(value)
    except (TypeError, ValueError): return ""

def aliases(row):
    vals={row.get('sample',''), Path(row.get('file','')).stem}
    return {v for v in vals if v}

def load_replidec(mod):
    out={}; p=mod/'replidec'/'prediction_summary.tsv'
    if not p.exists(): return out
    with p.open(errors='ignore') as h:
        for r in csv.DictReader(h, delimiter='\t'):
            key=(r.get('sample_name') or r.get('sample') or r.get('name') or '').split()[0]
            if key: out[key]=r
    return out

def load_aliases(mod):
    p=mod/'sample_aliases.tsv'; out={}
    if p.exists():
        with p.open() as h:
            for r in csv.DictReader(h,delimiter='\t'):
                if r.get('sample') and r.get('sequence_id'): out[r['sample']]=r['sequence_id']
    return out

def load_vhulk(mod):
    out={}
    for p in (mod/'vhulk').glob('prediction_*.csv'):
        try:
            with p.open() as h:
                r=next(csv.DictReader(h))
            key=p.stem.removeprefix('prediction_')
            out[key]=r
        except (StopIteration, OSError): pass
    return out

def load_wish(mod):
    out={}; p=mod/'wish'/'prediction.list'
    if not p.exists(): return out
    with p.open() as h:
        next(h,None)
        for line in h:
            cols=[x.strip().strip('"') for x in line.rstrip().split('\t')]
            if len(cols)>=3 and cols[0]: out[cols[0]]={'host':cols[1],'score':cols[2]}
    return out

def main():
    if len(sys.argv)!=4: raise SystemExit('usage: enrich_features.py RAW_FEATURES MODULE_DIR OUTPUT_FEATURES')
    raw,mod,out=map(Path,sys.argv[1:]); rows=list(csv.DictReader(raw.open(),delimiter='\t'))
    status={}
    sp=mod.parent/'analysis'/'module_status.json'
    if sp.exists():
        try: status=json.loads(sp.read_text())
        except json.JSONDecodeError: pass
    repl=load_replidec(mod); vhulk=load_vhulk(mod); wish=load_wish(mod); aliases_map=load_aliases(mod)
    for r in rows:
        keyset=aliases(r); mapped=aliases_map.get(r.get('sample','')); keyset.add(mapped or '')
        rr=next((v for k,v in repl.items() if k in keyset),None)
        hv=next((v for k,v in vhulk.items() if k in keyset),None)
        hw=wish.get(r.get('sample',''))
        if hv:
            r['host_genus']=hv.get('pred_genus','')
            r['host_score']=fnum(hv.get('score_genus'))
            r['host_species']=hv.get('pred_species','')
            r['host_species_score']=fnum(hv.get('score_species'))
            r['host_entropy']=fnum(hv.get('entropy_genus'))
            r['host_method']='vHULK'; r['host_status']='available'
        elif hw:
            r['host_genus']=hw['host']; r['host_score']=fnum(hw['score'])
            r['host_method']='WIsH'; r['host_status']='available'
        if rr:
            # Replidec's Pfam call is a per-genome integrase/excisionase
            # measurement; preserve it without scanning unrelated log text.
            r['integrase']=rr.get('integrase_number') or 0
            r['replication_cycle']=rr.get('final_label') or rr.get('bc_label') or rr.get('pfam_label') or ''
            r['replication_temperate_score']=fnum(rr.get('bc_temperate'))
            r['replication_virulent_score']=fnum(rr.get('bc_virulent'))
            r['replication_chronic_score']=fnum(rr.get('bc_chronic'))
        else:
            r['replication_cycle']=''
        if not hv and not hw: r['host_status']='not_available'
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=rows[0].keys() if rows else [],delimiter='\t'); w.writeheader(); w.writerows(rows)
if __name__=='__main__': main()
