#!/usr/bin/env python3
"""Run optional external evidence modules and record an auditable status."""
import json, os, shutil, subprocess, sys
from pathlib import Path
def main():
    if len(sys.argv)!=4: raise SystemExit('usage: run_modules.py INPUT_DIR OUTPUT_DIR STATUS_JSON')
    inp,out,status=Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]); out.mkdir(parents=True,exist_ok=True)
    fasta=sorted(p for p in inp.glob('*') if p.suffix.lower() in {'.fa','.fasta','.fna','.fas'})
    combined=out/'phages.fasta'
    aliases=out/'sample_aliases.tsv'
    with combined.open('w') as w, aliases.open('w') as a:
        a.write('sample\tsequence_id\n')
        for p in fasta:
            txt=p.read_text().rstrip(); w.write(txt+'\n')
            header=next((x[1:].split()[0] for x in txt.splitlines() if x.startswith('>')),p.stem)
            a.write(f'{p.stem}\t{header}\n')
    result={'Pharokka':{'available':False,'ran':False},'Replidec':{'available':False,'ran':False},'RaFAH':{'available':False,'ran':False},'DefenseFinder':{'available':False,'ran':False},'PADLOC':{'available':False,'ran':False},'DePP':{'available':False,'ran':False}}
    ph=Path('/usr/local/Caskroom/miniconda/base/envs/phageorbit-pharokka/bin/pharokka.py')
    db=Path(__import__('os').environ.get('PHAGEWEAVE_PHAROKKA_DB','databases/pharokka'))
    if ph.exists() and os.environ.get('PHAGEWEAVE_SKIP_PHAROKKA','0') not in {'1','true','yes'}:
        result['Pharokka']['available']=True
        if db.exists():
            try:
                subprocess.run(['conda','run','-n','phageorbit-pharokka','pharokka.py','-i',str(combined),'-o',str(out/'pharokka'),'-d',str(db),'-t','2','-m','-f'],check=True)
                result['Pharokka']['ran']=True
            except (OSError,subprocess.CalledProcessError) as e:
                result['Pharokka']['error']=str(e)
                # Pharokka may complete gene prediction before a downstream
                # PHROG/MMseqs database failure. Preserve that usable output.
                aa=out/'pharokka'/'prodigal-gv_aas_tmp.fasta'
                result['Pharokka']['partial']=aa.exists(); result['Pharokka']['ran']=aa.exists()
        else: result['Pharokka']['error']='database not found at databases/pharokka'
    elif ph.exists():
        result['Pharokka']['available']=True; result['Pharokka']['note']='Skipped by PHAGEWEAVE_SKIP_PHAROKKA.'
    # Replidec predicts virulent, temperate, or chronic replication cycle.
    # Prefer an executable in PATH, then the dedicated conda environment.
    replidec=shutil.which('Replidec') or shutil.which('replidec')
    env=os.environ.copy()
    conda_base=subprocess.run(['conda','info','--base'],capture_output=True,text=True).stdout.strip()
    repl_prefix=Path(os.environ.get('PHAGEWEAVE_REPLIDEC_PREFIX',str(Path(conda_base)/'envs/phageweave-replidec')))
    repl_env=repl_prefix/'bin'
    if repl_env.exists(): env['PATH']=str(repl_env)+os.pathsep+env.get('PATH','')
    if not replidec and repl_env.joinpath('Replidec').exists(): replidec=str(repl_env/'Replidec')
    replidec_cmd=[replidec] if replidec else None
    result['Replidec']['available']=bool(replidec_cmd)
    if replidec_cmd:
        repl_out=out/'replidec'; repl_out.mkdir(parents=True,exist_ok=True)
        try:
            subprocess.run(replidec_cmd+['-p','multi_fasta','-i',str(combined),'-w',str(repl_out),'-n','prediction_summary.tsv','-t','2'],check=True,env=env)
            summary=repl_out/'prediction_summary.tsv'
            result['Replidec']['ran']=summary.exists()
            result['Replidec']['summary']=str(summary)
            if not summary.exists(): result['Replidec']['error']='completed without prediction_summary.tsv'
        except (OSError,subprocess.CalledProcessError) as e:
            result['Replidec']['error']=str(e)
    else:
        result['Replidec']['note']='Install Replidec (conda environment phageweave-replidec) to enable replication-cycle evidence.'
    for name,commands in {'RaFAH':['rafah','RaFAH.pl'],'DefenseFinder':['defensefinder','defense-finder'],'PADLOC':['padloc'],'DePP':['DePP.py','depp']}.items():
        exe=next((shutil.which(x) for x in commands if shutil.which(x)),None)
        if name=='RaFAH':
            root=Path(__file__).resolve().parents[2]/'tools'/'RaFAH'; script=root/'RaFAH.pl'
            required=[root/'HP_Ranger_Model_3_Valid_Cols.txt',root/'HP_Ranger_Model_3_Filtered_0.9_Valids.hmm',root/'MMSeqs_Clusters_Ranger_Model_1+2+3_Clean.RData',root/'RaFAH_Predict_Host.R']
            missing=[p.name for p in required if not p.exists()]
            result[name]['available']=script.exists(); result[name]['model_assets']=not missing
            result[name]['note']=('RaFAH scripts found; missing model assets: '+', '.join(missing)) if missing else 'Model assets found; R/ranger and runtime dependencies still require verification.'
        else:
            result[name]['available']=bool(exe); result[name]['note']='Detected but not auto-run without a configured database/model.' if exe else 'Executable not installed.'
    status.parent.mkdir(parents=True,exist_ok=True); status.write_text(json.dumps(result,indent=2))
if __name__=='__main__': main()
