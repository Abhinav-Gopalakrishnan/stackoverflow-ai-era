#!/usr/bin/env python3
"""User-run publication commands. Nothing runs unless a subcommand is invoked.

10 real issues, 6 issue-backed project items, 14 work commits, 6 sequential PRs.
Human-dependent issues remain open. No forced push/reset, no forged dates.
"""
import argparse,glob,json,subprocess,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'.review2_git_state.json'
REPO='Abhinav-Gopalakrishnan/stackoverflow-ai-era'
BRANCHES={'m2':'m2/review2-text-mining','m5':'m5/review2-forecasting'}
OWNER='Abhinav-Gopalakrishnan'
PROJECT='3'
MEMBERS={
 'm2':{'login':'Rishiikesh-20','name':'Rishiikesh','reviewer':'NISHANTH-KONCHADA'},
 'm5':{'login':'Adhikkesh','name':'Adhikkesh S K','reviewer':'smallworldsdev'}}
ISSUES={
 'm2':[
  ('Corpus preparation and shared sample','Implement text_prep.py, protected technology tokens, spaCy corpus, written rules, corpus statistics and the 2,000-row sample. Full corpus is shared on Drive.','Data Cleaning'),
  ('Tone scoring and weighted association','Implement original-prose VADER with technical overrides, frustration/politeness flags, weighted trends and tag/year-controlled association. Scores remain exploratory until issue 3 is complete.','Evaluation'),
  ('Independent tone validation and topic review','Complete independent M2/M3 labels for 200 questions, agreement, VADER accuracy/macro-F1/confusion matrix, and M2 independent topic names after M4 supplies terms/examples. Code and label sheet exist; HUMAN WORK IS STILL PENDING. Keep this issue open until those inputs are complete.','Evaluation'),
  ('Complexity measurements and bootstrap intervals','Implement readability, prose/code/tag measurements, weighted monthly summaries and 1,000-resample pre/post confidence intervals.','Evaluation'),
  ('Text notebook, slides and dashboard handoff','Deliver executed Method 2 Part A, two slides, findings, captions, schemas, contribution notes and viva material. Explicitly disclose pending human validation; M4 Part B and M1 dashboard are separate tasks.','Documentation')],
 'm5':[
  ('Complete weekly series and Review 1 correction','Deliver 14 x 400 complete weekly series, log counts, site shares, separate masked monthly rates, and superseded Review 1 forecast note.','Data Cleaning'),
  ('Forecast models, baselines and leakage checks','Implement naive/seasonal-naive/drift, damped ETS, SARIMAX interventions, expanding-window harness, and synthetic leakage/metric contract tests.','Modelling'),
  ('Training-only selection and forecast evaluation','Deliver 2024 H2 validation, training-only AIC, 1/4/13/26-week backtests, matched-origin comparisons, fit failures, DM and residual diagnostics.','Evaluation'),
  ('Final forecasts and integrated tag interpretation','Deliver 26-week forecasts, 80/95% bands, tag classes, half-life and load index. Forecast files exist. Integration with Akshay/M3 ITS slope estimates is STILL PENDING; keep this issue open until the joint interpretation is finished.','Evaluation'),
  ('Forecast notebook, slides and dashboard handoff','Deliver executed Method 1 Part B, two slides, findings, captions, schemas, contribution/viva notes and reproduction checks. M3 Part A and M1 integration are separate tasks.','Documentation')]}
# Exactly three project tasks each, reusing three of the five issues.
PROJECT_ISSUES={'m2':[1,3,5],'m5':[1,3,4]}
PLAN_TASKS={'m2':{1:'M2-20',2:'M2-21, M2-25',3:'M2-22, M2-24',4:'M2-23',5:'M2-26, M2-27, M2-28'},
            'm5':{1:'M5-20',2:'M5-21, M5-22',3:'M5-23',4:'M5-24',5:'M5-26, M5-27, M5-28'}}
PENDING={'m2':3,'m5':4}
CLOSE={'m2':{1:[1],2:[2],3:[4,5]},'m5':{1:[1,2],2:[3],3:[5]}}
REFS={'m2':{1:[],2:[3],3:[3]},'m5':{1:[],2:[],3:[4]}}
PR_TITLES={'m2':{1:'Text corpus and shared preparation',2:'Tone scoring and independent-validation workflow',3:'Complexity, text notebook and presentation handoff'},
           'm5':{1:'Forecasting implementation and prepared series',2:'Validation and multi-horizon backtest results',3:'Forecasts, notebook and presentation handoff'}}
BATCHES={1:[1,2],2:[3,4],3:[5,6,7]}
# Paths are intentionally explicit; ignored full/private datasets are never staged.
COMMITS={
'm2':{
1:(1,'add shared setup and prose corpus pipeline',['.gitignore','requirements-review2-members.txt','src/review2_common.py','src/text_prep.py']),
2:(1,'add corpus sample and preprocessing audit',['data/processed/text_corpus_sample_2000.parquet','reports/review2/text/corpus_stats.json','reports/review2/text/text_preprocessing.json','reports/review2/text/corpus_sample_metadata.parquet']),
3:(2,'add tone scoring and weighted association',['src/sentiment.py','reports/review2/text/tone_method.json','reports/review2/text/tone_monthly.csv','reports/review2/text/tone_resolution_association.csv']),
4:(3,'add text contracts and independent validation sheet',['tests/test_text_review2.py','reports/review2/text/tone_validation_sample.csv','reports/review2/text/tone_validation.csv','reports/review2/text/tone_validation_status.json']),
5:(4,'add complexity measurements and bootstrap results',['src/complexity.py','reports/review2/text/complexity_method.json','reports/review2/text/complexity_monthly.csv','reports/review2/text/complexity_prepost.csv']),
6:(5,'add executed text notebook and findings',['notebooks/08_text_mining.ipynb','reports/review2/m2_findings.md','reports/review2/m2_viva.md','reports/review2/contribution_member2.md','reports/review2/text/tone_prepost.csv','reports/review2/text/tone_complexity.png','reports/review2/text/slide_data.json']),
7:(5,'add text slides and dashboard handoff',['reports/review2/member2_review2_slides.pptx','reports/review2/text/dashboard_captions.csv','reports/review2/text/dashboard_handoff.json','src/review2_deliverables.py','src/make_review2_member_slides.js'])},
'm5':{
1:(2,'add baseline ETS and SARIMAX forecast harness',['src/ts_forecast.py']),
2:(1,'add complete series leakage tests and correction note',['tests/test_ts_forecast.py','reports/review2/ts/series_long.csv','reports/review2/ts/monthly_rates_masked.csv','reports/review2/ts/series_manifest.json','reports/review1/timeseries_superseded.md']),
3:(3,'add training-only AIC and validation results',['reports/review2/ts/model_choices.csv','reports/review2/ts/sarimax_aic_grid.csv','reports/review2/ts/validation_metrics.csv','reports/review2/ts/validation_predictions.csv']),
4:(3,'add matched backtests and residual diagnostics',['reports/review2/ts/backtest_*','reports/review2/ts/diebold_mariano.csv','reports/review2/ts/fit_failures.csv','reports/review2/ts/residual_checks.csv','reports/review2/ts/acf_*.png']),
5:(4,'add 26-week forecasts and tag classes',['reports/review2/ts/forecasts_26w.csv','reports/review2/ts/tag_classes.csv','reports/review2/ts/forecast_*.png','reports/review2/ts/run_status.json']),
6:(5,'add executed forecasting notebook and findings',['notebooks/07_timeseries.ipynb','reports/review2/m5_findings.md','reports/review2/m5_viva.md','reports/review2/contribution_member5.md']),
7:(5,'add slides reproducibility and team handoffs',['reports/review2/member5_review2_slides.pptx','reports/review2/ts/dashboard_captions.csv','reports/review2/ts/dashboard_handoff.json','reports/review2/ts/slide_data.json','src/check_review2_handoffs.py','docs/review2_adhi_rishi_handoff.md','docs/review2_task_status.md','reports/review2/completion_checks.json','reports/review2/run_environment.json','reports/review2/test_results.txt','scripts/review2_git_workflow.py','docs/review2_git_commands.md'])}}


def run(*args,capture=True):
    print('+ '+' '.join(str(a) for a in args),flush=True)
    r=subprocess.run([str(a) for a in args],cwd=ROOT,text=True,capture_output=capture)
    if r.returncode:
        if capture:print(r.stdout+r.stderr,file=sys.stderr)
        raise SystemExit(r.returncode)
    return r.stdout.strip() if capture else ''


def load():return json.loads(STATE.read_text()) if STATE.exists() else {'issues':{},'commits':{},'prs':{},'projects':{}}
def save(s):STATE.write_text(json.dumps(s,indent=2)+'\n')
def branch(member):
    expected=BRANCHES[member]
    if run('git','branch','--show-current')!=expected:raise SystemExit(f'Run init {member} to switch to {expected} first.')
def account(member):
    u=json.loads(run('gh','api','user'))
    if u['login']!=MEMBERS[member]['login']:raise SystemExit(f'Active GitHub account is {u["login"]}; run identity {member}.')
    return u

def expand(patterns):
    paths=[]
    for pattern in patterns:
        matches=sorted(glob.glob(str(ROOT/pattern)))
        if not matches:raise SystemExit('Missing file/pattern: '+pattern)
        paths.extend(str(Path(p).relative_to(ROOT)) for p in matches if Path(p).is_file())
    return sorted(set(paths))

def init(member):
    expected=BRANCHES[member]
    if member=='m5':
        s=load()
        for batch in [1,2,3]:
            pr=s['prs'].get(f'm2-{batch}')
            if not pr or run('gh','pr','view',pr['url'],'--repo',REPO,'--json','state','--jq','.state')!='MERGED':
                raise SystemExit('Finish and merge all three Rishiikesh PRs before creating Adhikkesh’s branch.')
        run('git','fetch','origin',capture=False)
    exists=subprocess.run(['git','show-ref','--verify','--quiet','refs/heads/'+expected],cwd=ROOT).returncode==0
    if exists:run('git','switch',expected,capture=False)
    else:
        # Adhikkesh starts from main AFTER the Rishiikesh PRs, so only M5 work appears in its diff.
        run('git','switch','-c',expected,*( ['origin/main'] if member=='m5' else []),capture=False)
    run('gh','auth','setup-git','--hostname','github.com',capture=False)
    run('git','remote','set-url','origin',f'https://github.com/{REPO}.git')
    print('Branch ready; HTTPS pushes use the active gh account. No commit made.')

def identity(member):
    branch(member)
    run('gh','auth','switch','--hostname','github.com','--user',MEMBERS[member]['login'],capture=False)
    u=account(member)
    run('git','config','--local','user.name',MEMBERS[member]['name'])
    run('git','config','--local','user.email',f'{u["id"]}+{u["login"]}@users.noreply.github.com')
    print(f'Git and gh identity set to {u["login"]}.')

def field(url,name,**value):
    args=['gh','project','item-edit',PROJECT,'--owner',OWNER,'--url',url,'--field',name]
    for k,v in value.items():args+=['--'+k,str(v)]
    run(*args)

def issues(member):
    branch(member);account(member);s=load();mine=s['issues'].setdefault(member,{})
    for n,(title,desc,rubric) in enumerate(ISSUES[member],1):
        if str(n) in mine:continue
        body=f'Owner: {MEMBERS[member]["name"]}\nReviewer: {MEMBERS[member]["reviewer"]}\nReview: 2\nPlan tasks: {PLAN_TASKS[member][n]}\n\n## Scope\n{desc}\n\n## Evidence\nImplementation is prepared on `{BRANCHES[member]}`. Commits and PR links will be added during publication. This issue was created after implementation; creation dates are not backdated. Project due dates are the original plan deadlines.\n\n## Remaining work\nHuman validation/joint inputs are disclosed in the scope and handoff notes. Do not mark pending checks complete merely because implementation PRs merge.\n'
        with tempfile.TemporaryDirectory(prefix='review2-issue-') as tmp:
            p=Path(tmp)/'body.md';p.write_text(body)
            url=run('gh','issue','create','--repo',REPO,'--title',f'[Review 2][{member.upper()}-G{n}] {title}','--body-file',p,'--assignee','@me')
        number=int(url.rstrip('/').split('/')[-1]);mine[str(n)]={'url':url,'number':number,'title':title,'rubric':rubric};save(s)
    for n in PROJECT_ISSUES[member]:
        key=f'{member}-{n}';i=mine[str(n)]
        if key not in s['projects']:
            item=json.loads(run('gh','project','item-add',PROJECT,'--owner',OWNER,'--url',i['url'],'--format','json'))
            s['projects'][key]=item.get('id');save(s)
        field(i['url'],'Status',value='In Progress' if n==PENDING[member] else 'Review/Testing')
        field(i['url'],'Task Reviewer',text=MEMBERS[member]['reviewer'])
        field(i['url'],'Rubric component',value=i['rubric'])
        field(i['url'],'Phase',value='Phase 5' if n==5 else 'Phase 4')
        due='2026-10-09' if n==1 else ('2026-10-10' if n==3 else '2026-10-11')
        field(i['url'],'Due date',date=due)
    print(f'{member}: 5 issues and exactly 3 issue-backed project tasks recorded.')

def commit(member,n):
    branch(member);u=account(member);s=load();key=f'{member}-{n}'
    if key in s['commits']:raise SystemExit('Already recorded: '+s['commits'][key])
    if run('git','diff','--cached','--name-only'):raise SystemExit('Index has existing staged changes; review them before proceeding.')
    opened=json.loads(run('gh','pr','list','--repo',REPO,'--head',BRANCHES[member],'--base','main','--state','open','--json','url'))
    if opened:raise SystemExit('Merge the open PR before adding more commits to this same branch: '+opened[0]['url'])
    if n>1 and f'{member}-{n-1}' not in s['commits']:raise SystemExit('Commit the preceding numbered batch first.')
    prior=0 if n<=2 else (1 if n<=4 else 2)
    if prior:
        pr=s['prs'].get(f'{member}-{prior}')
        if not pr or run('gh','pr','view',pr['url'],'--repo',REPO,'--json','state','--jq','.state')!='MERGED':raise SystemExit('Merge and sync the preceding PR first.')
    issue_index,message,patterns=COMMITS[member][n]
    if member not in s['issues']:raise SystemExit('Create this member’s issues first.')
    issue=s['issues'][member][str(issue_index)]['number']
    expected=MEMBERS[member]['name']
    if run('git','config','user.name')!=expected:raise SystemExit('Git author is not the expected member; run identity again.')
    author=run('git','var','GIT_AUTHOR_IDENT')
    if not author.startswith(f'{expected} <{u["id"]}+{u["login"]}@users.noreply.github.com>'):
        raise SystemExit('Effective Git author differs from the selected account; check GIT_AUTHOR_NAME/GIT_AUTHOR_EMAIL environment overrides.')
    paths=expand(patterns)
    run('git','add','--',*paths,capture=False)
    run('git','diff','--cached','--stat',capture=False)
    run('git','commit','-m',f'#{issue} {message}',capture=False)
    s['commits'][key]=run('git','rev-parse','HEAD');save(s)

def pr(member,batch):
    branch(member);account(member);s=load();key=f'{member}-{batch}'
    if key in s['prs']:print(s['prs'][key]['url']);return
    if any(f'{member}-{n}' not in s['commits'] for n in BATCHES[batch]):raise SystemExit('Finish this batch’s commits first.')
    open_prs=json.loads(run('gh','pr','list','--repo',REPO,'--head',BRANCHES[member],'--base','main','--state','open','--json','number,url'))
    if open_prs:raise SystemExit('An open PR already exists for this head/base: '+open_prs[0]['url'])
    run('git','push','-u','origin',BRANCHES[member],capture=False)
    links=[]
    for n in CLOSE[member][batch]:links.append('Closes #'+str(s['issues'][member][str(n)]['number']))
    for n in REFS[member][batch]:links.append('Refs #'+str(s['issues'][member][str(n)]['number'])+' — human/joint checks remain open.')
    validation={('m2',1):'Full corpus was processed locally; committed sample, metadata and statistics were checked. Text/sentiment contracts arrive in the following tone PR.',
        ('m2',2):'Four text/sentiment contract tests pass locally. Tone scores cover 302,026 questions. Human labels, kappa and VADER evaluation remain pending.',
        ('m2',3):'Complexity used 1,000 question bootstrap resamples. Method 2 Part A ran through nbconvert with zero errors; slides passed file checks and were rendered.',
        ('m5',1):'Three synthetic forecasting tests pass, including no future-data use and matched-origin baseline skill. Weekly inputs cover 14 complete 400-week series.',
        ('m5',2):'Prediction timestamps, endpoint horizons, matched comparisons, convergence failures and residual checks were verified from saved outputs.',
        ('m5',3):'Both member notebooks executed without errors, seven contract tests pass, and four slides passed file checks and visual inspection. Forecast intervals are nested and end 2027-02-23.'}[(member,batch)]
    body='## Result\n'+PR_TITLES[member][batch]+'.\n\n'+ '\n'.join(links)+'\n\n## Validation\n'+validation+'\n\n## Dependencies\nTone labels and independent topic names remain human inputs. Integrated ITS interpretation awaits M3. Optional GRU and classifier extension are not represented as completed.\n'
    with tempfile.TemporaryDirectory(prefix='review2-pr-') as tmp:
        p=Path(tmp)/'body.md';p.write_text(body)
        url=run('gh','pr','create','--repo',REPO,'--head',BRANCHES[member],'--base','main','--title',f'[Review 2][{member.upper()}] {PR_TITLES[member][batch]}','--body-file',p,'--reviewer',MEMBERS[member]['reviewer'])
    s['prs'][key]={'url':url,'closed_issues':CLOSE[member][batch],'referenced_issues':REFS[member][batch]};save(s)
    for n in sorted(set(CLOSE[member][batch]+REFS[member][batch])):
        i=s['issues'][member][str(n)]
        if n in PROJECT_ISSUES[member]:field(i['url'],'Evidence',text=url)
    print('Review requested; merge after the reviewer checks the PR: '+url)

def merge(member,batch):
    branch(member);account(member);s=load();p=s['prs'][f'{member}-{batch}'];url=p['url']
    current=run('gh','pr','view',url,'--repo',REPO,'--json','state','--jq','.state')
    if current=='OPEN':run('gh','pr','merge',url,'--repo',REPO,'--merge','--delete-branch=false',capture=False)
    elif current!='MERGED':raise SystemExit('PR is not open or merged.')
    for n in CLOSE[member][batch]:
        if n in PROJECT_ISSUES[member]:field(s['issues'][member][str(n)]['url'],'Status',value='Completed')
    # Never reset, stash or force-push local work.
    run('git','fetch','origin',capture=False)
    run('git','merge','--ff-only','origin/main',capture=False)
    print('Merged using a merge commit; branch retained and synced for the next PR.')

def plan():
    paths=[]
    for m in ['m2','m5']:
        print(f'\n{m}: 7 work commits; PR groups 1–2, 3–4, 5–7')
        for n,(_,title,patterns) in COMMITS[m].items():
            files=expand(patterns);paths+=files
            print(f'  {n}. {title}: '+', '.join(files))
    assert len(paths)==len(set(paths)),'Overlapping commit file groups'
    changed=run('git','ls-files','--others','--exclude-standard').splitlines()+run('git','diff','--name-only').splitlines()
    missing=sorted(set(changed)-set(paths))
    if missing:raise SystemExit('Unassigned changes: '+', '.join(missing))
    print('\nAll current changed/untracked files are assigned once. No git mutation performed.')

def summary():
    s=load();print(json.dumps({'branches':BRANCHES,'issues':s['issues'],'work_commits':s['commits'],'pull_requests':s['prs'],'project_tasks':s['projects']},indent=2))

def batch(member,number):
    for n in BATCHES[number]:
        if f'{member}-{n}' not in load()['commits']:commit(member,n)
    pr(member,number)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['init','identity','issues','commit','pr','batch','merge','plan','status']);p.add_argument('member',nargs='?',choices=['m2','m5']);p.add_argument('number',nargs='?',type=int);a=p.parse_args()
    if a.command in ['plan','status']:{'plan':plan,'status':summary}[a.command]()
    elif a.member is None:p.error('member is required')
    elif a.command in ['init','identity','issues']:{'init':init,'identity':identity,'issues':issues}[a.command](a.member)
    elif a.number is None:p.error('number is required')
    elif a.command=='commit':
        if not 1<=a.number<=7:p.error('commit number must be 1–7')
        commit(a.member,a.number)
    else:
        if not 1<=a.number<=3:p.error('PR batch must be 1–3')
        {'pr':pr,'batch':batch,'merge':merge}[a.command](a.member,a.number)
