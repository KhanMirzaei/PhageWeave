#!/usr/bin/env python3
"""Transparent baseline pair scorer (not a clinically validated ML model)."""
import csv,itertools,sys
from pathlib import Path
def num(x):
    try:return float(x)
    except (TypeError,ValueError):return 0.0
def known(x): return str(x or '').strip().lower() not in {'','na','nan','not_available','not_run'}
def main():
 if len(sys.argv)!=3:raise SystemExit('usage: score_pairs.py FEATURES OUTPUT')
 rows=list(csv.DictReader(Path(sys.argv[1]).open(),delimiter='\t'));out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True)
 fields=['phage_a','phage_b','genome_similarity','host_overlap','depolymerase_complementarity','anti_defense_complementarity','sie_competition','rbp_competition','lifestyle_conflict','synergy_score','interference_score','prediction','confidence','explanation']
 with out.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader()
  for a,b in itertools.combinations(rows,2):
   sim=max(0,1-abs(num(a.get('gc_fraction'))-num(b.get('gc_fraction')))*4)*max(0,1-abs(num(a.get('length'))-num(b.get('length')))/max(num(a.get('length')),num(b.get('length')),1))
   host_known=known(a.get('host_genus')) and known(b.get('host_genus')); host=(int(a.get('host_genus')==b.get('host_genus')) if host_known else 'NA')
   dep=int(bool(num(a.get('depolymerase'))))^int(bool(num(b.get('depolymerase')))); anti=int(bool(num(a.get('anti_defense'))))^int(bool(num(b.get('anti_defense')))); sie=max(num(a.get('sie')),num(b.get('sie'))); rbp=sim
   la=(a.get('replication_cycle') or '').lower(); lb=(b.get('replication_cycle') or '').lower(); lifestyle=int(bool(la and lb and la!=lb))
   host_term=(0.2*int(host) if host_known else 0.0)
   sy=.35*dep+.3*anti+host_term+.15*(1-sim)
   inter=.35*sie+.25*sim+.2*lifestyle+(0.2*int(host) if host_known else 0.0)
   pred='Synergy' if sy>=inter and sy>=.35 else ('Interference' if inter>=.35 else 'Additive')
   # Missing host/lifestyle/module evidence lowers confidence; it is not a negative call.
   available=sum(known(a.get(k)) and known(b.get(k)) for k in ('host_genus','replication_cycle'))/2
   conf=(max(sy,inter) if pred!='Additive' else 1-abs(sy-inter))*(.5+.5*available)
   ev=[]
   if dep:ev.append('complementary depolymerase signal')
   if anti:ev.append('complementary anti-defense signal')
   if host_known and host:ev.append('shared predicted host')
   elif not host_known:ev.append('host prediction unavailable; host overlap not scored')
   if lifestyle:ev.append(f"different Replidec cycles ({a.get('replication_cycle')} vs {b.get('replication_cycle')})")
   if sie:ev.append('superinfection-exclusion marker')
   w.writerow(dict(phage_a=a['sample'],phage_b=b['sample'],genome_similarity=f'{sim:.3f}',host_overlap=host,depolymerase_complementarity=dep,anti_defense_complementarity=anti,sie_competition=f'{sie:.3f}',rbp_competition=f'{rbp:.3f}',lifestyle_conflict=lifestyle,synergy_score=f'{sy:.3f}',interference_score=f'{inter:.3f}',prediction=pred,confidence=f'{conf:.3f}',explanation='; '.join(ev) or 'No strong mechanistic evidence'))
if __name__=='__main__':main()
