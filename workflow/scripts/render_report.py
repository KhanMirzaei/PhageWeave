#!/usr/bin/env python3
import csv,html,sys
from pathlib import Path
def table(p):
 rows=list(csv.reader(Path(p).open(),delimiter='\t'))
 return '<p>No records.</p>' if not rows else '<table><tr>'+''.join(f'<th>{html.escape(x)}</th>' for x in rows[0])+'</tr>'+''.join('<tr>'+''.join(f'<td>{html.escape(x)}</td>' for x in r)+'</tr>' for r in rows[1:])+'</table>'
def main():
 if len(sys.argv)!=5:raise SystemExit('usage: render_report.py FEATURES PAIRS MODULE_STATUS REPORT')
 feat,pairs,modules,report=map(Path,sys.argv[1:]);report.parent.mkdir(parents=True,exist_ok=True)
 status=html.escape(modules.read_text())
 report.write_text(f'<!doctype html><html><head><meta charset="utf-8"><title>PhageWeave Report</title><style>body{{font:14px system-ui;max-width:1250px;margin:30px auto;color:#172033}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d5dee8;padding:6px;font-size:12px}}th{{background:#edf4fa}}pre{{background:#f5f7fa;padding:12px}}</style></head><body><h1>PhageWeave Report</h1><p>Evidence-based pairwise screening; predictions require experimental validation.</p><h2>External evidence modules</h2><pre>{status}</pre><h2>Feature matrix</h2>{table(feat)}<h2>Pairwise predictions</h2>{table(pairs)}</body></html>')
if __name__=='__main__':main()
