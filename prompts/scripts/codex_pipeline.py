#!/usr/bin/env python3
"""Local phase orchestration; no simulator code or model call during dry runs."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import uuid

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from pipeline_git import GitWorkflow, WorkflowError, refresh_checksums

ROOT = SCRIPT_DIR.parent.parent
STATE = '.codex-pipeline/tour-de-gross'


class PipelineError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise PipelineError(message)


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise PipelineError(f'Cannot read JSON {path}: {exc}') from exc


def write_json(path, value):
    path = Path(path)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local_path(root, name):
    require(isinstance(name, str) and name and not Path(name).is_absolute(), f'Invalid relative path: {name}')
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()), f'Path outside repository: {name}')
    return path


def validate_schema(value, schema, location='result'):
    """Validate the JSON Schema keywords used by our checked-in result contract."""
    types = {'object': dict, 'array': list, 'string': str, 'boolean': bool, 'null': type(None)}
    wanted = schema.get('type')
    if wanted:
        wanted = wanted if isinstance(wanted, list) else [wanted]
        require(any(type(value) is types[t] for t in wanted), f'{location}: wrong type')
    if 'enum' in schema:
        require(value in schema['enum'], f'{location}: invalid enum')
    if isinstance(value, dict):
        require(set(schema.get('required', [])) <= value.keys(), f'{location}: missing fields')
        properties = schema.get('properties', {})
        if schema.get('additionalProperties') is False:
            require(value.keys() <= properties.keys(), f'{location}: unknown fields')
        for key, child in value.items():
            if key in properties:
                validate_schema(child, properties[key], f'{location}.{key}')
    if isinstance(value, list):
        require(len(value) >= schema.get('minItems', 0), f'{location}: empty array')
        for i, child in enumerate(value):
            validate_schema(child, schema.get('items', {}), f'{location}[{i}]')
    if isinstance(value, str):
        require(len(value) >= schema.get('minLength', 0), f'{location}: empty string')


def load_manifest(root):
    manifest = read_json(root / 'prompts/scripts/codex_pipeline_config.json')
    require(set(manifest) == {'version', 'environment', 'stages', 'git_workflow'}, 'Unknown pipeline config fields')
    require(manifest['version'] == 1 and manifest['environment'] == 'tour_de_gross', 'Unsupported pipeline config')
    require(manifest['git_workflow'] == {'base_branch': 'main', 'remote': 'origin', 'branch_prefix': 'feature/'},
            'Unsupported Git branch/worktree workflow')
    stages = manifest['stages']
    require([s['id'] for s in stages] == [f'{i:02}' for i in range(14)], 'Stages must be ordered 00–13')
    for stage in stages:
        require(set(stage) == {'id', 'prompt', 'permission', 'gates', 'required_paths'}, 'Unknown stage config fields')
        expected = 'bounded-pilot' if stage['id'] == '12' else 'campaign-budget' if stage['id'] == '13' else 'implementation'
        require(stage['permission'] == expected, 'Invalid stage permission')
        require(local_path(root, stage['prompt']).is_file(), f'Missing prompt: {stage["prompt"]}')
        require(stage['gates'] and len(set(stage['gates'])) == len(stage['gates']), 'Invalid acceptance gates')
    return manifest


def stage_index(stages, value):
    for i, stage in enumerate(stages):
        if value in (stage['id'], Path(stage['prompt']).name, Path(stage['prompt']).stem):
            return i
    raise PipelineError(f'Unknown stage: {value}')


def validate_result(root, stage, result, schema):
    validate_schema(result, schema)
    require(result['stage_id'] == stage['id'], 'Stage ID mismatch')
    require(result['status'] == 'success' and result['next_stage_safe'] is True,
            result['blocking_issue'] or result['summary'])
    require(result['blocking_issue'] is None, 'Success has a blocking issue')
    require(result['evidence_paths'], 'Success needs nonempty evidence paths')
    require(any(t['required'] for t in result['tests']), 'Success needs an executed required test')
    require(all(t['result'] != 'failed' and (not t['required'] or t['result'] == 'passed')
                for t in result['tests']), 'Required test failed or not run')
    checks = result['acceptance_checks']
    require(len(checks) == len(stage['gates']) and {c['gate'] for c in checks} == set(stage['gates']),
            'Missing, duplicate or unknown acceptance gates')
    nodes = set()
    for check in checks:
        for node in check['test_nodeids']:
            path = node.split('::', 1)[0]
            require(path.startswith('tests/') and '::' in node and local_path(root, path).is_file(),
                    f'Acceptance check needs an existing exact pytest node ID: {node}')
            nodes.add(node)
    for name in result['changed_files']:
        local_path(root, name)
    for name in result['evidence_paths'] + stage['required_paths']:
        path = local_path(root, name)
        require(path.is_file() and path.stat().st_size > 0, f'Missing or empty evidence: {name}')
    return sorted(nodes)


def validate_test_report(report, nodes):
    require(report['exit_code'] == 0, 'Controller acceptance test run failed')
    for node in nodes:
        phases = report['tests'].get(node, {})
        require(phases == {'setup': 'passed', 'call': 'passed', 'teardown': 'passed'},
                f'Acceptance test did not actually pass (skip/xfail/error also rejected): {node}')


def git_output(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True)
    return result.stdout


def fingerprint(root):
    """Detect edits to tracked/untracked, nonignored files between accepted stages."""
    paths = git_output(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z').split(b'\0')
    h = hashlib.sha256()
    for raw in sorted(set(paths) - {b''}):
        name = os.fsdecode(raw)
        path = root / name
        h.update(raw + b'\0')
        if path.is_symlink():
            h.update(os.fsencode(os.readlink(path)))
        elif path.is_file():
            h.update(path.read_bytes())
        else:
            h.update(b'<deleted>')
        h.update(b'\0')
    return h.hexdigest()


def run_command(command, root, log, seconds, stdin=None, env=None):
    """Bound a process group, keeping logs and edits on errors, timeout or Ctrl-C."""
    print('Running:', ' '.join(map(str, command)), flush=True)
    with Path(log).open('w') as output:
        process = subprocess.Popen(command, cwd=root, stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, text=True, start_new_session=True, env=env)
        try:
            process.communicate(stdin, timeout=seconds)
            return process.returncode
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise PipelineError(f'Command interrupted or exceeded {seconds}s; see {log}')


def preflight(root, manifest):
    for cmd in ('conda', 'codex', 'git'):
        require(shutil.which(cmd), f'Missing command: {cmd}')
    git_output(root, 'rev-parse', '--show-toplevel')
    check = subprocess.run(['conda', 'run', '--no-capture-output', '-n', manifest['environment'],
                            'python', '-c', 'import sys, pytest, numpy, scipy; print(sys.prefix)'],
                           cwd=root, capture_output=True, text=True, timeout=60)
    require(check.returncode == 0, f'Conda audit environment unavailable: {check.stderr}')
    prefix = Path(check.stdout.strip().splitlines()[-1])
    require(prefix.is_dir(), 'Conda environment prefix is unavailable')
    print(f'Conda environment prefix: {prefix}')
    auth = subprocess.run(['codex', 'login', 'status'], capture_output=True, text=True, timeout=30)
    require(auth.returncode == 0, 'Codex is not logged in; run codex login')
    print((auth.stdout + auth.stderr).strip())
    help_text = subprocess.run(['codex', 'exec', '--help'], capture_output=True, text=True, timeout=30).stdout
    for flag in ('--output-schema', '--output-last-message', '--sandbox', '--config'):
        require(flag in help_text, f'Installed Codex lacks {flag}')
    return prefix


def pipeline_signature(root):
    files = sorted((root / 'prompts/scripts').glob('*')) + [root / 'AGENTS.md', root / 'tests/test_pipeline.py']
    return hashlib.sha256(b''.join(p.name.encode() + p.read_bytes() for p in files if p.is_file())).hexdigest()


def validate_budget(args, stages, start, end):
    ids = {s['id'] for s in stages[start:end + 1]}
    require('12' not in ids or args.allow_pilot, 'Stage 12 requires --allow-pilot (256 shots/point, 3 points, 120s total pilot)')
    if '13' in ids:
        require(args.campaign_budget, 'Stage 13 requires --campaign-budget PATH with an explicit compute budget')
        budget = read_json(args.campaign_budget)
        require(set(budget) == {'max_shots', 'max_wall_seconds', 'profile', 'series'}, 'Campaign budget fields are invalid')
        require(all(type(budget[k]) is int and budget[k] > 0 for k in ('max_shots', 'max_wall_seconds')),
                'Campaign limits must be positive integers')
        require(isinstance(budget['profile'], str) and budget['profile'] and isinstance(budget['series'], list)
                and budget['series'] and all(isinstance(s, str) and s for s in budget['series']), 'Campaign profile/series missing')
        return budget
    return None


def run_pipeline(args, root, manifest):
    stages = manifest['stages']
    state = root / STATE
    state.mkdir(parents=True, exist_ok=True)
    with (state / 'runner.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise PipelineError('Another pipeline is already running in this repository') from exc
        workflow = GitWorkflow(root, state, manifest['git_workflow'])
        accepted_path = state / 'accepted.json'
        accepted = read_json(accepted_path) if accepted_path.exists() else []
        require(isinstance(accepted, list) and len(accepted) <= len(stages) and [e['stage_id'] for e in accepted] == [f'{i:02}' for i in range(len(accepted))],
                'Accepted state must be a contiguous phase chain')
        signature = pipeline_signature(root)
        if workflow.pending.exists():
            require(args.retry_publish, 'Validated publication is pending; use --retry-publish (no new Codex call)')
            pending = read_json(workflow.pending)
            require(pending['entry']['pipeline_signature'] == signature, 'Controls changed since validation; publication stopped')
            published = workflow.publish(pending)
            published['workspace_sha256'] = fingerprint(root)
            if len(accepted) == int(published['stage_id']):
                accepted.append(published)
                write_json(accepted_path, accepted)
            else:
                require(len(accepted) == int(published['stage_id']) + 1 and accepted[-1]['feature_commit'] == published['feature_commit'],
                        'Pending publication conflicts with accepted state')
            workflow.finish()
            write_json(state / 'active.json', {'stage_id': published['stage_id'], 'state': 'published',
                                             'branch': published['branch'], 'worktree': published['worktree']})
            print('Publication verified; no implementation session was rerun.', flush=True)
            return
        require(not args.retry_publish, 'No publication is pending')
        for entry in accepted:
            require(entry['pipeline_signature'] == signature, 'Pipeline controls changed; review/archive state before restarting')
            require(entry['prompt_sha256'] == digest(root / stages[int(entry['stage_id'])]['prompt']), 'Accepted prompt changed')
        workspace_changed = bool(accepted and accepted[-1]['workspace_sha256'] != fingerprint(root))
        require(not workspace_changed or args.revalidate, 'Workspace changed since last acceptance; use --revalidate to rerun prior acceptance checks or review/archive state')
        start = stage_index(stages, args.from_stage) if args.from_stage else len(accepted)
        end = stage_index(stages, args.through)
        require(start == len(accepted), 'Cannot skip prerequisites or rerun accepted phases; use the next unaccepted phase')
        require(start <= end, 'Requested interval has no pending stages')
        budget = validate_budget(args, stages, start, end)
        workflow.synced_main()
        environment_prefix = preflight(root, manifest)
        run_dir = state / 'runs' / (time.strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8])
        run_dir.mkdir(parents=True)
        write_json(run_dir / 'run.json', {'from': stages[start]['id'], 'through': stages[end]['id'],
                                         'pilot': args.allow_pilot, 'campaign_budget': budget,
                                         'pipeline_signature': signature, 'sandbox': args.sandbox,
                                         'model_override': args.model, 'reasoning_effort_override': args.reasoning_effort,
                                         'stage_timeout_seconds': args.stage_timeout, 'test_timeout_seconds': args.test_timeout})
        schema = read_json(root / 'prompts/scripts/codex_stage_result_schema.json')
        if args.revalidate and accepted:
            nodes = set()
            for entry in accepted:
                nodes.update(validate_result(root, stages[int(entry['stage_id'])], read_json(entry['result_path']), schema))
            report = run_dir / 'revalidate-pytest.json'
            command = ['conda', 'run', '--no-capture-output', '-n', manifest['environment'], 'python',
                       str(root / 'prompts/scripts/pipeline_check_tests.py'), str(report), 'tests/test_reference.py', *sorted(nodes)]
            require(run_command(command, root, run_dir / 'revalidate-pytest.log', args.test_timeout) == 0, 'Prior acceptance revalidation failed')
            validate_test_report(read_json(report), sorted(nodes))
            require(pipeline_signature(root) == signature, 'Revalidation changed pipeline controls')
            protected = accepted[-1]['reference_hashes']
            require({p.name: digest(p) for p in (root / 'reference').glob('*') if p.is_file()} == protected,
                    'Reference fixtures changed since acceptance; stop for source-backed review')
            accepted[-1]['workspace_sha256'] = fingerprint(root)
            accepted[-1]['revalidation_report'] = str(report)
            write_json(accepted_path, accepted)
        for stage in stages[start:end + 1]:
            phase = run_dir / stage['id']
            phase.mkdir()
            feature = workflow.prepare(stage, resume=args.resume_feature)
            workspace = Path(feature['worktree'])
            workspace_env = dict(os.environ, PYTHONPATH=str(workspace / 'src') + os.pathsep + os.environ.get('PYTHONPATH', ''))
            result_path = phase / 'result.json'
            before_status = digest(workspace / 'STATUS.md')
            before_head = git_output(workspace, 'rev-parse', 'HEAD')
            initial_references = {p.name: digest(p) for p in (workspace / 'reference').glob('*') if p.is_file()}
            context = (f'Complete only phase {stage["id"]} in {workspace}. Worktree branch: {feature["branch"]}; main checkout: {root}. The user has authorized the outer controller to submit '
                       f'phases through {stages[end]["id"]} sequentially; you must stop after this one. Read AGENTS.md, STATUS.md '
                       'and the scientific contracts. Preserve existing edits. Stay in this feature worktree and branch. '
                       'The controller will commit, merge to main and atomically push both refs only after validation. '
                       f'Shared external source directory: {root / "external_libs"}. Use that canonical directory for external checkouts. '
                       'Do not perform Git publication yourself. Use tour_de_gross. '
                       'No long sampling, solver jobs, cluster submission or upstream writes. Source reads and downloads are allowed; '
                       'fork under the user account before external-source modifications. Do not change reference fixtures in unattended mode; '
                       'report a source-backed proposed correction and stop for review.\n'
                       f'Required acceptance gate IDs (within this phase scope): {json.dumps(stage["gates"])}. '
                       f'Required file paths: {json.dumps(stage["required_paths"])}. '
                       'Map each gate to exact pytest node IDs of meaningful positive/negative tests. All mapped tests will be rerun. '
                       'Do not claim future/optional backends as tested. Record O1–O5; unresolved paper-exact items need not block '
                       'independent construction, but an assumption required for this phase must stop it.\n')
            if stage['id'] == '12':
                context += 'Pilot authorized: at most 256 shots per point, at most 3 accessible points, at most 120s total pilot wall time; enforce these in the sampler.\n'
            if stage['id'] == '13':
                context += f'User campaign compute budget (hard maxima; require validated prerequisites): {json.dumps(budget)}\n'
            prompt = context + '\n' + (root / stage['prompt']).read_text() + '\n' + (root / 'prompts/scripts/codex_stage_footer.md').read_text()
            (phase / 'prompt.md').write_text(prompt)
            write_json(state / 'active.json', {'stage_id': stage['id'], 'run_dir': str(run_dir), 'state': 'running', **feature})
            command = ['codex', 'exec', '--sandbox', args.sandbox, '--config', 'approval_policy="never"',
                       '--config', 'sandbox_workspace_write.network_access=true', '--add-dir', str(environment_prefix),
                       '--add-dir', str(root / 'external_libs'), '--add-dir', str(phase),
                       '--color', 'never', '-C', str(workspace), '--output-schema', str(root / 'prompts/scripts/codex_stage_result_schema.json'),
                       '--output-last-message', str(result_path)]
            if args.model:
                command += ['--model', args.model]
            if args.reasoning_effort:
                command += ['--config', f'model_reasoning_effort="{args.reasoning_effort}"']
            command += ['-']
            require(run_command(command, workspace, phase / 'codex.log', min(args.stage_timeout, budget['max_wall_seconds']) if stage['id'] == '13' else args.stage_timeout, stdin=prompt, env=workspace_env) == 0,
                    f'Codex failed in phase {stage["id"]}; see {phase}')
            require(git_output(workspace, 'rev-parse', 'HEAD') == before_head, 'Agent changed Git history')
            require(pipeline_signature(workspace) == signature, 'Agent changed pipeline controls; stop for review')
            require({p.name: digest(p) for p in (workspace / 'reference').glob('*') if p.is_file()} == initial_references,
                    'Reference fixtures changed; stop for source-backed review')
            require(digest(workspace / 'STATUS.md') != before_status, 'STATUS.md was not updated for this phase')
            result = read_json(result_path)
            nodes = validate_result(workspace, stage, result, schema)
            report = phase / 'pytest.json'
            command = ['conda', 'run', '--no-capture-output', '-n', manifest['environment'], 'python',
                       str(root / 'prompts/scripts/pipeline_check_tests.py'), str(report),
                       'tests/test_reference.py']
            if (workspace / 'tests/test_pipeline.py').is_file():
                command.append('tests/test_pipeline.py')
            command += nodes
            code = run_command(command, workspace, phase / 'pytest.log', args.test_timeout, env=workspace_env)
            require(code == 0, f'Acceptance tests failed in phase {stage["id"]}; see {phase / "pytest.log"}')
            validate_test_report(read_json(report), nodes)
            require(git_output(workspace, 'rev-parse', 'HEAD') == before_head, 'Tests changed Git history')
            require(pipeline_signature(workspace) == signature, 'Tests changed pipeline controls')
            require({p.name: digest(p) for p in (workspace / 'reference').glob('*') if p.is_file()} == initial_references,
                    'Tests changed reference fixtures')
            entry = {'stage_id': stage['id'], 'result_path': str(result_path), 'pytest_report': str(report),
                     'prompt_sha256': digest(root / stage['prompt']), 'pipeline_signature': signature,
                     'reference_hashes': initial_references}
            pending = workflow.commit_candidate(feature, entry, result, read_json(report))
            entry = workflow.publish(pending)
            entry['workspace_sha256'] = fingerprint(root)
            accepted.append(entry)
            write_json(accepted_path, accepted)
            workflow.finish()
            write_json(state / 'active.json', {'stage_id': stage['id'], 'run_dir': str(run_dir), 'state': 'published', **feature})
            print(f'VALIDATED, MERGED AND PUSHED phase {stage["id"]}; result: {result_path}', flush=True)
        print(f'Completed requested phases through {stages[end]["id"]}.', flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='Repository checkout root')
    parser.add_argument('--from', dest='from_stage', help='Next pending stage ID, stem or filename')
    parser.add_argument('--through', default='11', help='Last authorized phase (default: 11)')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--dry-run', action='store_true', help='Validate configuration and print plan; no Codex or tests')
    parser.add_argument('--preflight', action='store_true', help='Check local CLI/auth/environment only; no model request')
    parser.add_argument('--status', action='store_true')
    parser.add_argument('--revalidate', action='store_true', help='Rerun prior accepted gates after workspace edits, without new Codex calls for those phases')
    parser.add_argument('--resume-feature', action='store_true', help='Resume a preserved failed feature worktree after review')
    parser.add_argument('--retry-publish', action='store_true', help='Retry a validated merge/push without invoking Codex; stop afterwards')
    parser.add_argument('--allow-pilot', action='store_true')
    parser.add_argument('--campaign-budget', type=Path)
    parser.add_argument('--stage-timeout', type=int, default=3600)
    parser.add_argument('--test-timeout', type=int, default=600)
    parser.add_argument('--sandbox', choices=['workspace-write', 'read-only', 'danger-full-access'], default='workspace-write')
    parser.add_argument('--model', help='Optional model override; otherwise use installed Codex configuration')
    parser.add_argument('--reasoning-effort', choices=['low', 'medium', 'high', 'xhigh', 'max'],
                        help='Per-run Codex model_reasoning_effort override; otherwise inherit installed configuration')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        manifest = load_manifest(root)
        if args.status:
            for name in ('active.json', 'current-feature.json', 'pending-publication.json', 'accepted.json', 'exit-code'):
                path = root / STATE / name
                print(f'{name}:\n{path.read_text() if path.exists() else "(none)"}')
            return 0
        if args.list or args.dry_run:
            start = stage_index(manifest['stages'], args.from_stage or '00')
            end = stage_index(manifest['stages'], args.through)
            require(start <= end, 'Invalid stage interval')
            for stage in manifest['stages'][start:end + 1]:
                print(f'{stage["id"]} {stage["prompt"]} [{stage["permission"]}] gates={",".join(stage["gates"])}')
            print(f'Model override: {args.model or "inherit Codex config"}; reasoning effort: {args.reasoning_effort or "inherit Codex config"}')
            print('No stages launched. Pilot 12 requires --allow-pilot; campaign 13 requires --campaign-budget.')
            return 0
        require(args.stage_timeout > 0 and args.test_timeout > 0, 'Timeouts must be positive')
        if args.preflight:
            preflight(root, manifest)
        else:
            run_pipeline(args, root, manifest)
            (root / STATE / 'exit-code').write_text('0\n')
        return 0
    except (PipelineError, WorkflowError, OSError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as exc:
        print(f'PIPELINE STOPPED: {exc}', file=sys.stderr)
        if not (args.list or args.dry_run or args.preflight or args.status):
            state = root / STATE
            # The lock owner alone may update shared status; a duplicate runner must not.
            if state.exists():
                with (state / 'runner.lock').open('a') as lock:
                    try:
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        active_path = state / 'active.json'
                        active = read_json(active_path) if active_path.exists() else {}
                        active.update(state='stopped', error=str(exc))
                        write_json(active_path, active)
                        (state / 'exit-code').write_text('1\n')
                    except BlockingIOError:
                        pass
        return 1


def interrupted(signum, frame):
    raise KeyboardInterrupt(f'Interrupted by signal {signum}')


if __name__ == '__main__':
    for signum in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, interrupted)
    sys.exit(main())
