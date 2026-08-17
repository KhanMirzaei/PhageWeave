#!/usr/bin/env python3
"""Run optional external evidence modules and record an auditable status."""
import json, shutil, subprocess, sys
from pathlib import Path
def main():
    if len(sys.argv)!=4: raise SystemExit('usage: run_modules.py INPUT_DIR OUTPUT_DIR STATUS_JSON')
    inp,out,status=Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]); out.mkdir(parents=True,exist_ok=True)
    fasta=sorted(p for p in inp.glob('*') if p.suffix.lower() in {'.fa','.fasta','.fna','.fas'})
    combined=out/'phages.fasta'
    with combined.open('w') as w:
        for p in fasta: w.write(p.read_text().rstrip()+'\n')
    result={'Pharokka':{'available':False,'ran':False},'RaFAH':{'available':False,'ran':False},'DefenseFinder':{'available':False,'ran':False},'PADLOC':{'available':False,'ran':False},'DePP':{'available':False,'ran':False}}
    ph=Path('/usr/local/Caskroom/miniconda/base/envs/phageorbit-pharokka/bin/pharokka.py')
    db=Path('databases/pharokka')
    if ph.exists():
        result['Pharokka']['available']=True
        if db.exists():
            try:
                subprocess.run(['conda','run','-n','phageorbit-pharokka','pharokka.py','-i',str(combined),'-o',str(out/'pharokka'),'-d',str(db),'-t','2'],check=True)
                result['Pharokka']['ran']=True
            except (OSError,subprocess.CalledProcessError) as e: result['Pharokka']['error']=str(e)
        else: result['Pharokka']['error']='database not found at databases/pharokka'
    for name,commands in {'RaFAH':['rafah','RaFAH.pl'],'DefenseFinder':['defensefinder','defense-finder'],'PADLOC':['padloc'],'DePP':['DePP.py','depp']}.items():
        exe=next((shutil.which(x) for x in commands if shutil.which(x)),None)
        result[name]['available']=bool(exe); result[name]['note']='Detected but not auto-run without a configured database/model.' if exe else 'Executable not installed.'
    status.parent.mkdir(parents=True,exist_ok=True); status.write_text(json.dumps(result,indent=2))
if __name__=='__main__': main()
