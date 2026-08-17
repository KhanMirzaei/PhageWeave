#!/usr/bin/env python3
import csv,itertools,sys
from pathlib import Path
def num(x):
 try:return float(x)
 except:return 0.0
def main():
 if len(sys.argv)!=3:raise SystemExit('usage: score_pairs.py FEATURES OUTPUT')
 rows=list(csv.DictReader(Path(sys.argv[1]).open(),delimiter='\t'));out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True);fields=['phage_a','phage_b','genome_similarity','host_overlap','depolymerase_complementarity','anti_defense_complementarity','sie_competition','rbp_competition','synergy_score','interference_score','prediction','confidence','explanation']
 with out.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader()
  for a,b in itertools.combinations(rows,2):
   sim=max(0,1-abs(num(a['gc_fraction'])-num(b['gc_fraction']))*4)*max(0,1-abs(num(a['length'])-num(b['length']))/max(num(a['length']),num(b['length']),1));host=int(bool(a.get('host_genus')) and a.get('host_genus')==b.get('host_genus'));dep=int(bool(num(a['depolymerase'])))^int(bool(num(b['depolymerase'])));anti=int(bool(num(a['anti_defense'])))^int(bool(num(b['anti_defense'])));sie=max(num(a['sie']),num(b['sie']));sy=.35*dep+.3*anti+.2*host+.15*(1-sim);inter=.4*sie+.35*sim+.25*host;pred='Synergy' if sy>=inter and sy>=.35 else ('Interference' if inter>=.35 else 'Additive');conf=max(sy,inter) if pred!='Additive' else 1-abs(sy-inter);ev=[]
   if dep:ev.append('complementary depolymerase signal')
   if anti:ev.append('complementary anti-defense signal')
   if host:ev.append('shared predicted host')
   if sie:ev.append('superinfection-exclusion marker')
   w.writerow(dict(phage_a=a['sample'],phage_b=b['sample'],genome_similarity=f'{sim:.3f}',host_overlap=host,depolymerase_complementarity=dep,anti_defense_complementarity=anti,sie_competition=f'{sie:.3f}',rbp_competition=f'{sim:.3f}',synergy_score=f'{sy:.3f}',interference_score=f'{inter:.3f}',prediction=pred,confidence=f'{conf:.3f}',explanation='; '.join(ev) or 'No strong mechanistic evidence'))
if __name__=='__main__':main()
