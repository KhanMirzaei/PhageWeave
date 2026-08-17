#!/usr/bin/env python3
"""Convert annotation output text into explicit pairwise trait flags."""
import csv,sys
from pathlib import Path
def main():
 if len(sys.argv)!=4:raise SystemExit('usage: enrich_features.py RAW_FEATURES MODULE_DIR OUTPUT_FEATURES')
 raw,mod,out=map(Path,sys.argv[1:]); text=' '.join(p.read_text(errors='ignore').lower() for p in mod.rglob('*') if p.is_file() and p.stat().st_size<100_000_000)
 flags={'depolymerase':('depolymerase','polysaccharide lyase','tailspike'),'anti_defense':('anti-crispr','anti-cbASS','anti-defense','anti defense'),'sie':('superinfection exclusion','sie protein','membrane exclusion'),'rbp':('tail fiber','tail fibre','receptor binding'),'integrase':('integrase','repressor','lysogen'),'lysis':('holin','endolysin','spanin')}
 rows=list(csv.DictReader(raw.open(),delimiter='\t')); fields=rows[0].keys() if rows else []
 for r in rows:
  for key,terms in flags.items():
   if key in r and float(r.get(key,0) or 0)==0:r[key]=int(any(t in text for t in terms))
 out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(rows)
if __name__=='__main__':main()
