"""Controller gates and orchestration tested with fake CLI commands, never a model."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'prompts/scripts'
spec = importlib.util.spec_from_file_location('codex_pipeline', SCRIPTS / 'codex_pipeline.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)
SCHEMA = json.loads((SCRIPTS / 'codex_stage_result_schema.json').read_text())


def sample_result(root, stage):
    return {'stage_id': stage['id'], 'status': 'success', 'next_stage_safe': True, 'summary': 'Fixture only',
            'tests': [{'command': 'pytest', 'result': 'passed', 'required': True, 'notes': 'fixture only'}],
            'acceptance_checks': [{'gate': g, 'test_nodeids': ['tests/test_phase.py::test_positive']} for g in stage['gates']],
            'changed_files': ['STATUS.md'], 'evidence_paths': ['STATUS.md'], 'unresolved_items': ['O1 remains open'],
            'blocking_issue': None}


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / 'checkout with spaces'
    root.mkdir()
    shutil.copytree(ROOT / 'prompts', root / 'prompts')
    (root / 'tests').mkdir()
    (root / 'tests/test_reference.py').write_text('def test_reference():\n    assert True\n')
    (root / 'tests/test_phase.py').write_text('def test_positive():\n    assert True\n')
    (root / 'reference').mkdir()
    (root / 'reference/fixture.json').write_text('{}\n')
    (root / 'AGENTS.md').write_text('Fixture instructions only\n')
    (root / 'STATUS.md').write_text('Fixture baseline\n')
    (root / '.gitignore').write_text('.codex-pipeline/\n__pycache__/\n.pytest_cache/\n')
    for name in ['docs/BACKEND_AUDIT.md', 'locks/source-lock.json']:
        path = root / name
        path.parent.mkdir(exist_ok=True)
        path.write_text('fixture\n')
    for command in [['git', 'init', '-b', 'main'], ['git', 'config', 'user.name', 'Test'], ['git', 'config', 'user.email', 'test@example.invalid'], ['git', 'add', '.'],
                    ['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'fixture']]:
        subprocess.run(command, cwd=root, check=True, capture_output=True)
    remote = tmp_path / 'origin.git'
    subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
    subprocess.run(['git', 'remote', 'add', 'origin', str(remote)], cwd=root, check=True, capture_output=True)
    subprocess.run(['git', 'push', '-u', 'origin', 'main'], cwd=root, check=True, capture_output=True)
    return root


def submission_file(root):
    return root / pipeline.STATE / 'submitted.txt'


def pending_workspace(root):
    return Path(pipeline.read_json(root / pipeline.STATE / 'current-feature.json')['worktree'])


def commit_manual_main_edit(root):
    subprocess.run(['git', 'add', '--all'], cwd=root, check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'User reviewed main edit'], cwd=root, check=True, capture_output=True)
    subprocess.run(['git', 'push', 'origin', 'main'], cwd=root, check=True, capture_output=True)


def test_manifest_and_stage_selection():
    manifest = pipeline.load_manifest(ROOT)
    assert len(manifest['stages']) == 14
    assert pipeline.stage_index(manifest['stages'], '00_source_audit.md') == 0
    assert pipeline.stage_index(manifest['stages'], '11') == 11
    with pytest.raises(pipeline.PipelineError):
        pipeline.stage_index(manifest['stages'], '99')


@pytest.mark.parametrize('change', ['missing_field', 'unknown_field', 'wrong_stage', 'not_run', 'failed',
                                   'empty_gates', 'duplicate_gate', 'unknown_node', 'missing_evidence',
                                   'path_escape', 'blocked', 'wrong_bool', 'empty_nodes', 'optional_only'])
def test_invalid_success_rejected(repository, change):
    stage = pipeline.load_manifest(repository)['stages'][0]
    result = sample_result(repository, stage)
    if change == 'missing_field': del result['tests']
    elif change == 'unknown_field': result['invented'] = True
    elif change == 'wrong_stage': result['stage_id'] = '01'
    elif change == 'not_run': result['tests'][0]['result'] = 'not_run'
    elif change == 'failed': result['tests'][0]['result'] = 'failed'
    elif change == 'empty_gates': result['acceptance_checks'] = []
    elif change == 'duplicate_gate': result['acceptance_checks'][1] = result['acceptance_checks'][0]
    elif change == 'unknown_node': result['acceptance_checks'][0]['test_nodeids'] = ['tests/missing.py::test_x']
    elif change == 'missing_evidence': result['evidence_paths'] = ['missing.txt']
    elif change == 'path_escape': result['evidence_paths'] = ['../escape.txt']
    elif change == 'blocked': result['status'] = 'blocked'
    elif change == 'wrong_bool': result['next_stage_safe'] = 1
    elif change == 'empty_nodes': result['acceptance_checks'][0]['test_nodeids'] = []
    elif change == 'optional_only': result['tests'][0]['required'] = False
    with pytest.raises(pipeline.PipelineError):
        pipeline.validate_result(repository, stage, result, SCHEMA)


def test_open_paper_items_allow_scoped_success(repository):
    stage = pipeline.load_manifest(repository)['stages'][0]
    result = sample_result(repository, stage)
    result['tests'].append({'command': 'Future Stim tests', 'result': 'not_run', 'required': False,
                            'notes': 'Outside this fixture scope'})
    assert pipeline.validate_result(repository, stage, result, SCHEMA) == ['tests/test_phase.py::test_positive']


@pytest.mark.parametrize('outcome', ['skipped', 'xfail', 'failed', 'missing', 'teardown_failure'])
def test_skipped_or_missing_actual_test_rejected(outcome):
    phases = {'setup': 'passed', 'call': 'passed', 'teardown': 'passed'}
    if outcome == 'missing': phases.pop('call')
    elif outcome == 'teardown_failure': phases['teardown'] = 'failed'
    else: phases['call'] = outcome
    with pytest.raises(pipeline.PipelineError):
        pipeline.validate_test_report({'exit_code': 0, 'tests': {'node': phases}}, ['node'])


def test_pilot_and_campaign_require_budget():
    import argparse
    stages = pipeline.load_manifest(ROOT)['stages']
    args = argparse.Namespace(allow_pilot=False, campaign_budget=None)
    with pytest.raises(pipeline.PipelineError, match='allow-pilot'):
        pipeline.validate_budget(args, stages, 12, 12)
    args.allow_pilot = True
    assert pipeline.validate_budget(args, stages, 12, 12) is None
    with pytest.raises(pipeline.PipelineError, match='campaign-budget'):
        pipeline.validate_budget(args, stages, 13, 13)


@pytest.fixture
def fake_tools(tmp_path):
    bin_dir = tmp_path / 'fake-bin'
    bin_dir.mkdir()
    conda = bin_dir / 'conda'
    conda.write_text('#!' + sys.executable + '\nimport os,sys\na=sys.argv[1:]\nassert a[:4]==["run","--no-capture-output","-n","tour_de_gross"]\nos.execv(sys.executable,[sys.executable]+a[5:])\n')
    codex = bin_dir / 'codex'
    codex.write_text('#!' + sys.executable + '''
import json,os,pathlib,re,subprocess,sys,time
args=sys.argv[1:]
if args==['login','status']:
    print('Fixture login');sys.exit(0)
if args==['exec','--help']:
    print('--output-schema --output-last-message --sandbox --config');sys.exit(0)
prompt=sys.stdin.read()
root=pathlib.Path(args[args.index('-C')+1])
phase=re.search(r'Complete only phase (\\d\\d)',prompt).group(1)
mode=os.environ.get('FAKE_MODE','success')
common=pathlib.Path(subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=root,text=True).strip()).resolve()
(common.parent/'.codex-pipeline/tour-de-gross/last-codex-args.json').write_text(json.dumps(args))
with (common.parent/'.codex-pipeline/tour-de-gross/submitted.txt').open('a') as f:f.write(phase+'\\n')
if mode=='nonzero':sys.exit(7)
if mode=='timeout':time.sleep(10)
result=pathlib.Path(args[args.index('--output-last-message')+1])
if mode=='malformed':result.write_text('{bad');sys.exit(0)
if mode!='no_status':
    with (root/'STATUS.md').open('a') as f:f.write('Fixture phase '+phase+' complete\\n')
gates=json.loads(re.search(r'gate IDs \\(within this phase scope\\): (\\[.*?\\])\\.',prompt).group(1))
if mode=='skip':(root/'tests/test_phase.py').write_text('import pytest\\n@pytest.mark.skip(reason="fixture")\\ndef test_positive(): pass\\n')
if mode=='fail_test':(root/'tests/test_phase.py').write_text('def test_positive(): assert False\\n')
if mode=='control_edit':
    with (root/'AGENTS.md').open('a') as f:f.write('edited\\n')
if mode=='fixture_edit':(root/'reference/fixture.json').write_text('{"changed":true}')
value={'stage_id':phase,'status':'success','next_stage_safe':True,'summary':'Fake CLI test only',
       'tests':[{'command':'pytest','result':'not_run' if mode=='not_run' else 'passed','required':True,'notes':'fixture'}],
       'acceptance_checks':[{'gate':g,'test_nodeids':['tests/test_phase.py::test_positive']} for g in gates],
       'changed_files':['STATUS.md'],'evidence_paths':['STATUS.md'],'unresolved_items':['O1'],'blocking_issue':None}
result.write_text(json.dumps(value))
''')
    for file in (conda, codex): file.chmod(0o755)
    return {**os.environ, 'PATH': str(bin_dir) + os.pathsep + os.environ['PATH']}


def invoke(root, env, *args):
    return subprocess.run([sys.executable, str(root / 'prompts/scripts/codex_pipeline.py'), '--root', str(root), *args],
                          capture_output=True, text=True, env=env, timeout=30)


def test_sequential_sessions_and_resume(repository, fake_tools):
    first = invoke(repository, fake_tools, '--through', '00')
    assert first.returncode == 0, first.stderr + first.stdout
    second = invoke(repository, fake_tools, '--through', '01')
    assert second.returncode == 0, second.stderr + second.stdout
    assert submission_file(repository).read_text().splitlines() == ['00', '01']
    accepted = pipeline.read_json(repository / pipeline.STATE / 'accepted.json')
    assert [e['stage_id'] for e in accepted] == ['00', '01']
    assert all(Path(e['pytest_report']).is_file() for e in accepted)
    assert all(e['published'] and e['branch'].startswith('feature/') and Path(e['worktree']).is_dir() for e in accepted)
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=repository, text=True).strip() == 'main'
    assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=repository, text=True).strip() == ''
    remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=repository, text=True).split()[0]
    assert remote == accepted[-1]['merge_commit']
    assert (repository / 'validation/phase_00.json').is_file() and (repository / 'validation/phase_01.json').is_file()


@pytest.mark.parametrize('mode', ['nonzero', 'malformed', 'not_run', 'skip', 'fail_test', 'no_status',
                                 'control_edit', 'fixture_edit', 'timeout'])
def test_failure_stops_before_next_session(repository, fake_tools, mode):
    result = invoke(repository, {**fake_tools, 'FAKE_MODE': mode}, '--through', '01', '--stage-timeout', '1' if mode=='timeout' else '30')
    assert result.returncode == 1, result.stdout
    assert submission_file(repository).read_text().splitlines() == ['00']
    assert not (repository / pipeline.STATE / 'accepted.json').exists()
    assert pipeline.read_json(repository / pipeline.STATE / 'active.json')['state'] == 'stopped'
    assert list((repository / pipeline.STATE / 'runs').glob('*/00/codex.log'))
    worktree = pending_workspace(repository)
    assert worktree.is_dir()
    assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=repository, text=True).strip() == ''
    local = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repository, text=True).strip()
    remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=repository, text=True).split()[0]
    assert local == remote
    assert not subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/feature/*'], cwd=repository, text=True)


def test_resume_rejects_workspace_changes(repository, fake_tools):
    assert invoke(repository, fake_tools, '--through', '00').returncode == 0
    (repository / 'STATUS.md').write_text('Changed independently\n')
    result = invoke(repository, fake_tools, '--through', '01')
    assert result.returncode == 1 and 'Workspace changed' in result.stderr
    assert submission_file(repository).read_text().splitlines() == ['00']


def test_prerequisite_skipping_and_budget_denied_before_codex(repository, fake_tools):
    result = invoke(repository, fake_tools, '--from', '01', '--through', '01')
    assert result.returncode == 1 and 'skip prerequisites' in result.stderr
    result = invoke(repository, fake_tools, '--through', '12')
    assert result.returncode == 1 and 'allow-pilot' in result.stderr
    assert not submission_file(repository).exists()


def test_dry_run_is_read_only(repository):
    result = invoke(repository, os.environ, '--dry-run', '--through', '13')
    assert result.returncode == 0 and '13 prompts/13_' in result.stdout
    assert not (repository / pipeline.STATE).exists()


def test_repository_lock_blocks_second_runner(repository, fake_tools):
    import fcntl
    state = repository / pipeline.STATE
    state.mkdir(parents=True)
    with (state / 'runner.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = invoke(repository, fake_tools, '--through', '00')
        assert result.returncode == 1 and 'already running' in result.stderr
        assert not (state / 'active.json').exists()


def test_actual_report_records_skip_and_xfail(repository):
    test = repository / 'tests/test_reporting.py'
    test.write_text('import pytest\ndef test_pass(): pass\n@pytest.mark.skip(reason="fixture")\ndef test_skip(): pass\n@pytest.mark.xfail(reason="fixture")\ndef test_xfail(): assert False\n')
    output = repository / 'report.json'
    result = subprocess.run([sys.executable, str(repository / 'prompts/scripts/pipeline_check_tests.py'),
                             str(output), str(test)], cwd=repository, capture_output=True, text=True)
    assert result.returncode == 0
    report = pipeline.read_json(output)
    assert report['tests']['tests/test_reporting.py::test_pass']['call'] == 'passed'
    assert report['tests']['tests/test_reporting.py::test_skip']['setup'] == 'skipped'
    assert report['tests']['tests/test_reporting.py::test_xfail']['call'] == 'xfail'


def test_tmux_launcher_keeps_completed_pane(repository, fake_tools, tmp_path):
    import time
    import uuid
    tmux = shutil.which('tmux')
    if not tmux:
        pytest.skip('Local tmux is unavailable')
    socket = 'tour-pipeline-test-' + uuid.uuid4().hex
    session = 'fixture-tour'
    wrapper = Path(fake_tools['PATH'].split(os.pathsep)[0]) / 'tmux'
    wrapper.write_text('#!' + sys.executable + '\nimport os,sys\nos.execv(' + repr(tmux) + ',[' + repr(tmux) + ',"-L",' + repr(socket) + ']+sys.argv[1:])\n')
    wrapper.chmod(0o755)
    env = {**fake_tools, 'CODEX_TMUX_SESSION': session}
    try:
        started = subprocess.run(['bash', str(repository / 'prompts/scripts/start_codex_pipeline_tmux.sh'),
                                  '--through', '00'], env=env, capture_output=True, text=True, timeout=30)
        assert started.returncode == 0, started.stdout + started.stderr
        exit_file = repository / pipeline.STATE / 'exit-code'
        deadline = time.monotonic() + 15
        while not exit_file.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        assert exit_file.exists(), (repository / pipeline.STATE / 'pipeline.log').read_text()
        assert exit_file.read_text().strip() == '0', (repository / pipeline.STATE / 'pipeline.log').read_text()
        # Runner can finish just before tmux records the dead-pane state.
        while time.monotonic() < deadline:
            status = subprocess.check_output([tmux, '-L', socket, 'list-panes', '-t', session,
                                              '-F', '#{pane_dead}'], text=True).strip()
            if status == '1': break
            time.sleep(0.1)
        assert status == '1'
        duplicate = subprocess.run(['bash', str(repository / 'prompts/scripts/start_codex_pipeline_tmux.sh'),
                                    '--through', '00'], env=env, capture_output=True, text=True, timeout=30)
        assert duplicate.returncode == 1 and 'already exists' in duplicate.stderr
        assert submission_file(repository).read_text().splitlines() == ['00']
    finally:
        subprocess.run([tmux, '-L', socket, 'kill-server'], capture_output=True)


def test_revalidate_allows_resume_after_pending_edits(repository, fake_tools):
    assert invoke(repository, fake_tools, '--through', '00').returncode == 0
    with (repository / 'STATUS.md').open('a') as f:
        f.write('Pending work edited after phase 00\n')
    commit_manual_main_edit(repository)
    resumed = invoke(repository, fake_tools, '--through', '01', '--revalidate')
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert submission_file(repository).read_text().splitlines() == ['00', '01']
    accepted = pipeline.read_json(repository / pipeline.STATE / 'accepted.json')
    assert Path(accepted[0]['revalidation_report']).is_file()


def test_revalidate_rejects_old_gate_regression(repository, fake_tools):
    assert invoke(repository, fake_tools, '--through', '00').returncode == 0
    (repository / 'tests/test_phase.py').write_text('def test_positive(): assert False\n')
    commit_manual_main_edit(repository)
    resumed = invoke(repository, fake_tools, '--through', '01', '--revalidate')
    assert resumed.returncode == 1 and 'revalidation failed' in resumed.stderr
    assert submission_file(repository).read_text().splitlines() == ['00']


def test_interrupt_terminates_child_group_and_records_stop(repository, fake_tools):
    import signal
    import time
    env = {**fake_tools, 'FAKE_MODE': 'timeout'}
    process = subprocess.Popen([sys.executable, str(repository / 'prompts/scripts/codex_pipeline.py'),
                                '--root', str(repository), '--through', '00'], env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 10
        while not submission_file(repository).exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert submission_file(repository).exists()
        process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 1, stdout + stderr
        assert 'interrupted' in stderr
        assert pipeline.read_json(repository / pipeline.STATE / 'active.json')['state'] == 'stopped'
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def test_campaign_budget_rejects_unbounded_or_unknown_fields(tmp_path):
    import argparse
    stages = pipeline.load_manifest(ROOT)['stages']
    path = tmp_path / 'budget.json'
    args = argparse.Namespace(allow_pilot=True, campaign_budget=path)
    valid = {'max_shots': 100, 'max_wall_seconds': 30, 'profile': 'fixture', 'series': ['fixture']}
    path.write_text(json.dumps(valid))
    assert pipeline.validate_budget(args, stages, 13, 13) == valid
    for invalid in [dict(valid, max_shots=0), dict(valid, max_wall_seconds=True),
                    dict(valid, invented=True), dict(valid, series=[])]:
        path.write_text(json.dumps(invalid))
        with pytest.raises(pipeline.PipelineError):
            pipeline.validate_budget(args, stages, 13, 13)


def test_dirty_main_is_preserved_without_codex(repository, fake_tools):
    (repository / 'STATUS.md').write_text('Preexisting user edit\n')
    result = invoke(repository, fake_tools, '--through', '00')
    assert result.returncode == 1 and 'Main checkout must be clean' in result.stderr
    assert (repository / 'STATUS.md').read_text() == 'Preexisting user edit\n'
    assert not submission_file(repository).exists()


def test_failed_feature_requires_explicit_resume(repository, fake_tools):
    failed = invoke(repository, {**fake_tools, 'FAKE_MODE': 'nonzero'}, '--through', '00')
    assert failed.returncode == 1
    workspace = pending_workspace(repository)
    blocked = invoke(repository, fake_tools, '--through', '00')
    assert blocked.returncode == 1 and '--resume-feature' in blocked.stderr
    resumed = invoke(repository, fake_tools, '--through', '00', '--resume-feature')
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert workspace.exists()
    assert submission_file(repository).read_text().splitlines() == ['00', '00']
    assert not (repository / pipeline.STATE / 'current-feature.json').exists()


def test_atomic_push_failure_and_retry_do_not_repeat_implementation(repository, fake_tools):
    remote_path = Path(subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=repository, text=True).strip())
    hook = remote_path / 'hooks/pre-receive'
    hook.write_text('#!/bin/sh\nexit 1\n')
    hook.chmod(0o755)
    before = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repository, text=True).strip()
    failed = invoke(repository, fake_tools, '--through', '01')
    assert failed.returncode == 1 and 'Git operation failed: push' in failed.stderr
    assert submission_file(repository).read_text().splitlines() == ['00']
    assert not (repository / pipeline.STATE / 'accepted.json').exists()
    assert (repository / pipeline.STATE / 'pending-publication.json').exists()
    assert subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=repository, text=True).split()[0] == before
    assert not subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/feature/*'], cwd=repository, text=True)
    hook.unlink()
    published = invoke(repository, fake_tools, '--retry-publish')
    assert published.returncode == 0, published.stdout + published.stderr
    assert submission_file(repository).read_text().splitlines() == ['00']
    accepted = pipeline.read_json(repository / pipeline.STATE / 'accepted.json')
    assert accepted[0]['published'] and accepted[0]['stage_id'] == '00'
    assert not (repository / pipeline.STATE / 'pending-publication.json').exists()


def test_remote_advancement_blocks_candidate_merge(repository):
    from pipeline_git import GitWorkflow, WorkflowError
    state = repository / pipeline.STATE
    state.mkdir(parents=True)
    workflow = GitWorkflow(repository, state, pipeline.load_manifest(repository)['git_workflow'])
    feature = workflow.prepare(pipeline.load_manifest(repository)['stages'][0])
    upstream = repository.parent / 'other-clone'
    remote = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=repository, text=True).strip()
    subprocess.run(['git', 'clone', '--branch', 'main', remote, str(upstream)], check=True, capture_output=True)
    (upstream / 'user.txt').write_text('Independent upstream change\n')
    subprocess.run(['git', 'add', '.'], cwd=upstream, check=True, capture_output=True)
    subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'Advance upstream'], cwd=upstream, check=True, capture_output=True)
    subprocess.run(['git', 'push', 'origin', 'main'], cwd=upstream, check=True, capture_output=True)
    with pytest.raises(WorkflowError, match='main.*differ'):
        workflow.commit_candidate(feature, {}, {}, {})
    assert Path(feature['worktree']).exists()
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repository, text=True).strip() == feature['base_commit']


def test_commit_hook_mutation_is_not_merged(repository, fake_tools):
    hook = repository / '.git/hooks/pre-commit'
    hook.write_text('#!/bin/sh\nprintf "hook mutation\\n" >> STATUS.md\ngit add STATUS.md\n')
    hook.chmod(0o755)
    result = invoke(repository, fake_tools, '--through', '00')
    assert result.returncode == 1 and 'Commit hooks changed' in result.stderr
    assert not (repository / pipeline.STATE / 'accepted.json').exists()
    assert not subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/feature/*'], cwd=repository, text=True)


def test_sol_high_reasoning_forwarded_and_recorded(repository, fake_tools):
    result = invoke(repository, fake_tools, '--through', '00', '--model', 'gpt-6.1-sol', '--reasoning-effort', 'high')
    assert result.returncode == 0, result.stdout + result.stderr
    args = pipeline.read_json(repository / pipeline.STATE / 'last-codex-args.json')
    assert args[args.index('--model') + 1] == 'gpt-6.1-sol'
    assert 'model_reasoning_effort="high"' in args
    manifest = pipeline.read_json(next((repository / pipeline.STATE / 'runs').glob('*/run.json')))
    assert manifest['model_override'] == 'gpt-6.1-sol'
    assert manifest['reasoning_effort_override'] == 'high'


def test_hard_reasoning_rejected_before_launch(repository, fake_tools):
    result = invoke(repository, fake_tools, '--reasoning-effort', 'hard', '--through', '00')
    assert result.returncode == 2 and 'invalid choice' in result.stderr
    assert not submission_file(repository).exists()
