#!/usr/bin/env python3
"""Extract baseline phage traits; external annotation modules can enrich TSV later."""
import csv,sys
from pathlib import Path
STOP={'TAA','TAG','TGA'}
CODON={}
for cs,aa in [('TTT TTC','F'),('TTA TTG CTT CTC CTA CTG','L'),('ATT ATC ATA','I'),('ATG','M'),('GTT GTC GTA GTG','V'),('TCT TCC TCA TCG AGT AGC','S'),('CCT CCC CCA CCG','P'),('ACT ACC ACA ACG','T'),('GCT GCC GCA GCG','A'),('TAT TAC','Y'),('TGG','W'),('CAT CAC','H'),('CAA CAG','Q'),('AAT AAC','N'),('AAA AAG','K'),('GAT GAC','D'),('GAA GAG','E'),('TGT TGC','C'),('CGT CGC CGA CGG AGA AGG','R'),('GGT GGC GGA GGG','G')]:
 for c in cs.split(): CODON[c]=aa
def fasta(p):
 name=p.stem; s=[]
 for l in p.read_text().splitlines():
  if l.startswith('>'):
   if s:return name,''.join(s).upper()
   name=l[1:].split()[0] or name
  elif l.strip():s.append(l.strip())
 return name,''.join(s).upper()
def proteins(s):
 out=[]
 for frame in range(3):
  i=frame
  while i+3<=len(s):
   if s[i:i+3]=='ATG':
    j=i+3
    while j+3<=len(s) and s[j:j+3] not in STOP:j+=3
    if j-i>=90:out.append(''.join(CODON.get(s[k:k+3],'X') for k in range(i,j,3)));i=j+3;continue
   i+=3
 return out
def main():
 if len(sys.argv)!=3:raise SystemExit('usage: extract_features.py INPUT_DIR OUTPUT_TSV')
 ps=sorted(p for p in Path(sys.argv[1]).glob('*') if p.suffix.lower() in {'.fa','.fasta','.fna','.fas'})
 if not ps:raise SystemExit('No FASTA genomes found')
 out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True); fields=['sample','file','length','protein_count','gc_fraction','depolymerase','anti_defense','sie','rbp','integrase','lysis','host_genus','host_score']
 with out.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader()
  for p in ps:
   name,s=fasta(p); row={k:0 for k in fields};row.update(sample=p.stem,file=str(p.resolve()),length=len(s),protein_count=len(proteins(s)),gc_fraction=round((s.count('G')+s.count('C'))/max(1,len(s)),4),host_genus='',host_score='');w.writerow(row)
if __name__=='__main__':main()
