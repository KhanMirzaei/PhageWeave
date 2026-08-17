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

def main():
    if len(sys.argv)!=4: raise SystemExit('usage: enrich_features.py RAW_FEATURES MODULE_DIR OUTPUT_FEATURES')
    raw,mod,out=map(Path,sys.argv[1:]); rows=list(csv.DictReader(raw.open(),delimiter='\t'))
    status={}
    sp=mod.parent/'analysis'/'module_status.json'
    if sp.exists():
        try: status=json.loads(sp.read_text())
        except json.JSONDecodeError: pass
    repl=load_replidec(mod); aliases_map=load_aliases(mod); repl_status=status.get('Replidec',{})
    for r in rows:
        keyset=aliases(r); mapped=aliases_map.get(r.get('sample','')); keyset.add(mapped or '')
        rr=next((v for k,v in repl.items() if k in keyset),None)
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
        r['host_status']='not_available' if not status.get('RaFAH',{}).get('ran') else r.get('host_status','available')
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=rows[0].keys() if rows else [],delimiter='\t'); w.writeheader(); w.writerows(rows)
if __name__=='__main__': main()
