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
    result={'Pharokka':{'available':False,'ran':False},'Replidec':{'available':False,'ran':False},'vHULK':{'available':False,'ran':False},'WIsH':{'available':False,'ran':False},'DefenseFinder':{'available':False,'ran':False},'PADLOC':{'available':False,'ran':False},'DePP':{'available':False,'ran':False},'Depolymerase/RBP/Sie':{'available':True,'ran':False,'note':'Derived by trait_scan.py from Pharokka annotations.'},'AcrFinder':{'available':False,'ran':False}}
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
    # vHULK is the primary host predictor. It ships trained models and emits
    # one CSV per input genome. Keep its environment separate because it uses
    # an older TensorFlow/Prokka stack than the main workflow.
    vh_prefix=Path(os.environ.get('PHAGEWEAVE_VHULK_PREFIX',str(Path(conda_base)/'envs/phageweave-vhulk')))
    vh_env=vh_prefix/'bin'; vh=vh_env/'vHULK.py'
    if not vh.exists(): vh=Path(__file__).resolve().parents[2]/'tools'/'vHULK'/'vHULK.py'
    result['vHULK']['available']=vh.exists()
    if vh.exists():
        vh_out=out/'vhulk'; vh_out.mkdir(parents=True,exist_ok=True)
        vh_envvars=env.copy(); vh_envvars['PATH']=str(vh_env)+os.pathsep+vh_envvars.get('PATH','')
        try:
            vh_cmd=[str(vh)] if os.access(vh,os.X_OK) else [sys.executable,str(vh)]
            subprocess.run(vh_cmd+['-i',str(inp),'-o',str(vh_out),'-t','2','--all'],check=True,env=vh_envvars)
            preds=list(vh_out.glob('prediction_*.csv'))
            result['vHULK']['ran']=bool(preds); result['vHULK']['prediction_files']=[str(p) for p in preds]
            if not preds: result['vHULK']['error']='completed without prediction_*.csv'
        except (OSError,subprocess.CalledProcessError) as e: result['vHULK']['error']=str(e)
    else: result['vHULK']['note']='Install vHULK in phageweave-vhulk or set PHAGEWEAVE_VHULK_PREFIX.'
    # WIsH is intentionally conditional: it requires a directory of bacterial
    # genomes supplied by the user to build its host models.
    local_wish=Path(__file__).resolve().parents[2]/'tools'/'WIsH'/'WIsH'
    wish=str(local_wish) if local_wish.exists() else shutil.which('WIsH')
    host_db=os.environ.get('PHAGEWEAVE_WISH_HOST_DB','')
    result['WIsH']['available']=bool(wish); result['WIsH']['host_database']=host_db or None
    if wish and host_db and Path(host_db).is_dir():
        wm=out/'wish_models'; wr=out/'wish'; wm.mkdir(parents=True,exist_ok=True); wr.mkdir(parents=True,exist_ok=True)
        try:
            subprocess.run([wish,'-c','build','-g',host_db,'-m',str(wm)],check=True)
            subprocess.run([wish,'-c','predict','-g',str(inp),'-m',str(wm),'-r',str(wr),'-b','5'],check=True)
            result['WIsH']['ran']=(wr/'prediction.list').exists(); result['WIsH']['output']=str(wr/'prediction.list')
        except (OSError,subprocess.CalledProcessError) as e: result['WIsH']['error']=str(e)
    elif not wish: result['WIsH']['note']='WIsH executable not installed.'
    else: result['WIsH']['note']='Provide bacterial FASTA directory with PHAGEWEAVE_WISH_HOST_DB to enable WIsH.'
    # Trait scan is always wired; it uses Pharokka product annotations and
    # explicitly reports unavailable when no annotation text exists.
    result['Depolymerase/RBP/Sie']['ran']=bool((out/'pharokka').exists())
    for name,commands in {'DefenseFinder':['defense-finder','defensefinder'],'PADLOC':['padloc'],'DePP':['DePP.py','depp'],'AcrFinder':['acrfinder','AcrFinder']}.items():
        exe=next((shutil.which(x) for x in commands if shutil.which(x)),None)
        result[name]['available']=bool(exe)
        bacteria=os.environ.get('PHAGEWEAVE_BACTERIA_DIR','')
        # DefenseFinder/PADLOC operate on bacterial proteins/genomes, not on
        # phage FASTA. Run only when the user supplies a bacterial directory.
        if exe and bacteria and Path(bacteria).is_dir() and name in {'DefenseFinder','PADLOC'}:
            target=out/'bacterial_defense'/name.lower(); target.mkdir(parents=True,exist_ok=True)
            try:
                if name=='DefenseFinder':
                    subprocess.run([exe,'run','--out-dir',str(target),bacteria],check=True)
                else:
                    subprocess.run([exe,'--faa',bacteria,'--outdir',str(target)],check=True)
                result[name]['ran']=True; result[name]['output']=str(target)
            except (OSError,subprocess.CalledProcessError) as e: result[name]['error']=str(e)
        elif exe: result[name]['note']='Installed; provide PHAGEWEAVE_BACTERIA_DIR to run bacterial defense screening.'
        else: result[name]['note']='Executable not installed.'
    status.parent.mkdir(parents=True,exist_ok=True); status.write_text(json.dumps(result,indent=2))
if __name__=='__main__': main()
