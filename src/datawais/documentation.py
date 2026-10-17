"""Terminal diagnostics from real MCP responses and clearly labeled saved evidence.

These views do not perform cleaning or replace a real two-session agent run.
Credentials are loaded locally and never printed.
"""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import httpx

from .client import execute

ROOT = Path(__file__).resolve().parents[2]
RAW = 'datasets/raw/university_questions.csv'
CLEAN = 'datasets/cleaned/pt1-demo-1/cleaned.csv'
RULES = 'rules/questions.json'
URL = 'http://127.0.0.1:8765/mcp'


def banner(title,kind='LIVE MCP CHECK'):
    print('\n'+title.upper())
    print(kind+' | '+datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')+' Manila')
    print()


def data(result):
    if result.get('isError'):
        return {'error':True,'message':result.get('content',[{}])[0].get('text','Tool error')}
    if 'structuredContent' in result:
        return result['structuredContent']
    return json.loads(result['content'][0]['text'])


async def call(role,tool,arguments):
    tokens = json.loads((ROOT/'.runtime/secrets.json').read_text())['tokens']
    return data(await execute(URL,tokens[role],'call',tool,arguments))


async def show(section):
    if section == 'tools':
        banner('Tool discovery and role scope')
        tokens=json.loads((ROOT/'.runtime/secrets.json').read_text())['tokens']
        for role in ['admin','inspector','cleaner']:
            result=await execute(URL,tokens[role],'list')
            print(f"{role.upper()}: {len(result['tools'])} tools from {result['server']}")
            print(textwrap.fill(', '.join(t['name'] for t in result['tools']),width=98))
            print()
        print('Tools were discovered through MCP; no token is displayed.')
    elif section == 'before':
        banner('Original dataset quality')
        inspected=await call('inspector','inspect_dataset',{'path':RAW,'sample_rows':2})
        validation=await call('inspector','validate_dataset',{'path':RAW,'rules_path':RULES})
        print('Dataset:',RAW)
        print('Records:',inspected.get('records'))
        print('Columns:',', '.join(inspected.get('columns',[])))
        print('Missing values:',json.dumps(inspected.get('missing_values',{})))
        print('Valid:',validation.get('valid'))
        print('Invalid records:',validation.get('invalid_records'))
        print('Duplicate records:',validation.get('duplicate_records'))
        print('Issue counts:',json.dumps(validation.get('issue_counts',{})))
        print('\nIssue examples:')
        for issue in validation.get('issues',[]):
            print(f"  Record {issue['record']}: {issue['column']} / {issue['code']}")
        print('\nSource SHA-256:',inspected.get('sha256'))
    elif section == 'handoff':
        banner('Persistent shared memory')
        state='Project state could not be read.'
        for name in ['PROJECT_STATE','PLAN_LOG','CHECKPOINTS','DECISIONS']:
            item=await call('inspector','read_file',{'path':f'handoff/{name}.md','limit':4000})
            print(f"{name}.md: {'ERROR' if item.get('error') else 'read through MCP'}")
            if name=='PROJECT_STATE' and not item.get('error'):
                state=item['content']
        print('\nCurrent saved state (first 12 lines):')
        print('\n'.join(state.splitlines()[:12]))
        print('\nThe saved two-session snapshots are in evidence/agent-1-handoff and evidence/completed-workspace.')
    elif section == 'after':
        banner('Cleaned output and preserved original')
        report_file=await call('cleaner','read_file',{'path':'datasets/cleaned/pt1-demo-1/report.json','limit':8000})
        report=json.loads(report_file['content'])
        validation=await call('cleaner','validate_dataset',{'path':CLEAN,'rules_path':RULES})
        original=await call('cleaner','inspect_dataset',{'path':RAW,'sample_rows':0})
        print('Cleaned dataset:',CLEAN)
        print('Input records:',report['input_records'])
        print('Output records:',validation['records'])
        print('Excluded records:',report['excluded_records'])
        print('Mapped labels:',report['mapped_cells'])
        print('Trimmed cells:',report['trimmed_cells'])
        print('Final valid:',validation['valid'])
        print('Final invalid records:',validation['invalid_records'])
        print('Final duplicates:',validation['duplicate_records'])
        print('Original unchanged:',original['sha256']==report['source_sha256'])
        print('\nOriginal SHA-256:',original['sha256'])
        print('Cleaned SHA-256: ',validation['dataset_sha256'])
    elif section == 'security':
        banner('Authentication and sandbox rejection')
        async with httpx.AsyncClient(timeout=10) as client:
            response=await client.post(URL,json={})
        print('MCP request without a token: HTTP',response.status_code)
        rejected=await call('inspector','read_file',{'path':'../outside.txt','limit':100})
        print('\nAttempted read: ../outside.txt')
        print('Request rejected:',bool(rejected.get('error')))
        if rejected.get('error'):
            print('Server explanation:',rejected['message'])
        print('\nThis check only attempts a read. It does not delete or change any file.')
    elif section == 'deployment':
        banner('Server and HTTPS tunnel status','LIVE PROCESS AND HTTP CHECK')
        config=json.loads((ROOT/'.runtime/local-runtime.json').read_text())
        env=dict(os.environ,PM2_HOME=str(ROOT/'.runtime/pm2'))
        output=subprocess.check_output(['cmd.exe','/d','/c',config['pm2'],'jlist'],env=env,text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        start=output.find('[{')
        if start<0:start=output.find('[]')
        apps=json.loads(output[start:])
        for app in apps:
            print(f"{app['name']}: {app['pm2_env']['status']} (PID {app['pid']})")
        public=(ROOT/'.runtime/public-url.txt').read_text().strip()
        print('\nCurrent MCP URL:',public)
        async with httpx.AsyncClient(timeout=10) as client:
            response=await client.get(public.removesuffix('/mcp')+'/healthz')
        print('Public HTTPS health response:',response.status_code,response.text)
        print('\nThe computer must remain awake and online for remote access.')
    elif section == 'sessions':
        banner('Actual recorded agent sessions','SAVED TRANSCRIPTS - NOT A NEW AGENT RUN')
        summary=json.loads((ROOT/'evidence/agent-session-summary.json').read_text())
        for i,item in enumerate(summary,1):
            events=[json.loads(s) for s in (ROOT/f'evidence/agent-{i}-transcript.jsonl').read_text().splitlines() if s.strip()]
            print(item['session'],'| role:',item['role'])
            print('  Tool calls:',item['tool_calls'],'| recorded tool errors:',item['tool_errors'])
            print('  First exchange:',events[0]['time'])
            print('  Last exchange: ',events[-1]['time'])
            print(f'  Full evidence: evidence/agent-{i}-transcript.jsonl\n')
        print('One session inspected and saved a handoff; a fresh session continued from files.')
        print('Repository: https://github.com/tatsu-06/DataWais-MCP')
    else:
        raise ValueError('Unknown section')


def main():
    sections=['tools','before','handoff','after','security','deployment','sessions']
    parser=argparse.ArgumentParser(description='DataWais MCP diagnostics')
    parser.add_argument('--section',choices=sections+['all','tests'])
    args=parser.parse_args()
    os.chdir(ROOT)
    while True:
        chosen=args.section
        if not chosen:
            print('\nDATAWAIS MCP DIAGNOSTICS\n')
            for n,name in enumerate(sections,1):print(f'  {n}. {name}')
            print('  8. Run automated tests\n  0. Exit')
            answer=input('\nChoose a view: ').strip()
            if answer=='0':return
            if answer=='8':chosen='tests'
            elif answer.isdigit() and 1<=int(answer)<=len(sections):chosen=sections[int(answer)-1]
            else:continue
            os.system('cls' if os.name=='nt' else 'clear')
        try:
            if chosen=='tests':
                banner('Automated test run','NEW TEST EXECUTION')
                sys.stdout.flush()
                temp=ROOT/'.runtime'/('documentation-tests-'+datetime.now().strftime('%Y%m%d%H%M%S'))
                subprocess.run([sys.executable,str(ROOT/'scripts/bootstrap.py'),'pytest','-q','--basetemp',str(temp)],check=True)
            else:
                for section in sections if chosen=='all' else [chosen]:asyncio.run(show(section))
        except Exception as exc:
            print('\nCHECK DID NOT COMPLETE:',type(exc).__name__)
            print('Start DataWais with START-DATAWAIS.cmd, then retry.')
            if args.section:raise SystemExit(1)
        if args.section:return
        input('\nPress Enter to return to the menu.')


if __name__=='__main__':main()
