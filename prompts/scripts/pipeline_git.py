"""Branch/worktree lifecycle owned by the controller, including retryable publication."""
import hashlib
import json
from pathlib import Path
import subprocess


class WorkflowError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise WorkflowError(message)


def save(path, value):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def refresh_checksums(root):
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                            check=True, capture_output=True)
    names = sorted(set(result.stdout.decode().split('\0')) - {''})
    (root / 'SHA256SUMS.txt').write_text(''.join(
        f'{hashlib.sha256((root / name).read_bytes()).hexdigest()}  {name}\n'
        for name in names if not name.startswith('SHA256SUMS') and (root / name).is_file()))


class GitWorkflow:
    def __init__(self, root, state, config):
        self.root, self.state, self.config = Path(root), Path(state), config
        self.pending = self.state / 'pending-publication.json'
        self.current = self.state / 'current-feature.json'
        self.log = self.state / 'git.log'

    def git(self, root, *args):
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, timeout=60)
        with self.log.open('ab') as log:
            log.write(('git ' + ' '.join(args) + '\n').encode() + result.stdout + result.stderr)
        if result.returncode:
            raise WorkflowError(f'Git operation failed: {args[0]}: {result.stderr.decode().strip()}; see {self.log}')
        return result.stdout.decode().strip()

    def clean_main(self):
        require(self.git(self.root, 'branch', '--show-current') == self.config['base_branch'],
                'Controller checkout must be on main')
        require(not self.git(self.root, 'status', '--porcelain'), 'Main checkout must be clean; preserve and commit local edits first')

    def synced_main(self):
        self.clean_main()
        remote, base = self.config['remote'], self.config['base_branch']
        self.git(self.root, 'remote', 'get-url', remote)
        self.git(self.root, 'config', 'user.name')
        self.git(self.root, 'config', 'user.email')
        self.git(self.root, 'fetch', '--no-tags', remote, base)
        head = self.git(self.root, 'rev-parse', base)
        remote_head = self.git(self.root, 'rev-parse', f'{remote}/{base}')
        require(head == remote_head, 'Local main and remote main differ; reconcile them before implementation')
        return head

    def prepare(self, stage, resume=False):
        require(not self.pending.exists(), 'Publication is pending; use --retry-publish before any new implementation')
        base = self.synced_main()
        if self.current.exists():
            current = json.loads(self.current.read_text())
            require(resume, 'A feature worktree is pending; inspect it and use --resume-feature to continue')
            require(current['stage_id'] == stage['id'] and current['base_commit'] == base,
                    'Pending worktree stage/base no longer matches main; review before resuming')
            worktree = Path(current['worktree'])
            require(self.git(worktree, 'branch', '--show-current') == current['branch'], 'Pending worktree branch changed')
            require(self.git(worktree, 'rev-parse', 'HEAD') == base, 'Pending feature history changed; review before resuming')
            return current
        stem = Path(stage['prompt']).stem
        branch = self.config['branch_prefix'] + stem
        self.git(self.root, 'check-ref-format', '--branch', branch)
        path = self.state / 'worktrees' / stem
        require(not path.exists(), f'Worktree path already exists: {path}')
        remote_branch = self.git(self.root, 'ls-remote', self.config['remote'], f'refs/heads/{branch}')
        require(not remote_branch, f'Remote feature branch already exists: {branch}')
        self.git(self.root, 'worktree', 'add', '-b', branch, str(path), base)
        current = {'stage_id': stage['id'], 'branch': branch, 'worktree': str(path), 'base_commit': base}
        save(self.current, current)
        return current

    def commit_candidate(self, current, entry, result, test_report):
        worktree = Path(current['worktree'])
        require(self.synced_main() == current['base_commit'], 'Main advanced while feature was implemented; stop for review')
        require(self.git(worktree, 'branch', '--show-current') == current['branch'], 'Agent switched feature branch')
        require(self.git(worktree, 'rev-parse', 'HEAD') == current['base_commit'], 'Agent changed feature history')
        # Small, versioned validation evidence travels with the implementation.
        report = worktree / 'validation' / f'phase_{current["stage_id"]}.json'
        report.parent.mkdir(exist_ok=True)
        save(report, {'stage_id': current['stage_id'], 'branch': current['branch'], 'base_commit': current['base_commit'],
                      'result': result, 'controller_pytest': test_report})
        refresh_checksums(worktree)
        self.git(worktree, '-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol', 'diff', '--check')
        self.git(worktree, 'add', '--all')
        validated_tree = self.git(worktree, 'write-tree')
        self.git(worktree, 'commit', '-m', f'Implement and validate phase {current["stage_id"]}: {current["branch"]}')
        require(not self.git(worktree, 'status', '--porcelain'), 'Commit hooks left worktree edits; stop for review')
        feature_commit = self.git(worktree, 'rev-parse', 'HEAD')
        require(self.git(worktree, 'rev-parse', 'HEAD^{tree}') == validated_tree,
                'Commit hooks changed the validated candidate; stop for review')
        entry.update(branch=current['branch'], worktree=str(worktree), base_commit=current['base_commit'],
                     feature_commit=feature_commit, validation_path=str(report.relative_to(worktree)))
        pending = {'feature': current, 'entry': entry, 'feature_commit': feature_commit}
        save(self.pending, pending)
        return pending

    def publish(self, pending):
        """Only immutable, validated commits may merge/push. No force or implicit retry."""
        self.clean_main()
        feature, entry = pending['feature'], pending['entry']
        base, remote = self.config['base_branch'], self.config['remote']
        commit = pending['feature_commit']
        require(self.git(self.root, 'rev-parse', feature['branch']) == commit, 'Validated feature branch changed')
        head = self.git(self.root, 'rev-parse', 'HEAD')
        if head == feature['base_commit']:
            require(self.synced_main() == feature['base_commit'], 'Remote main advanced before merge')
            self.git(self.root, 'merge', '--no-ff', '--no-edit', feature['branch'])
            head = self.git(self.root, 'rev-parse', 'HEAD')
        else:
            # Recover only our exact merge candidate, including a crash after merge.
            parents = self.git(self.root, 'show', '-s', '--format=%P', head).split()
            require(parents == [feature['base_commit'], commit], 'Main contains an unexpected commit; stop for review')
        require(self.git(self.root, 'rev-parse', 'HEAD^{tree}') == self.git(self.root, 'rev-parse', f'{commit}^{{tree}}'),
                'Merged tree differs from the validated feature tree')
        self.clean_main()
        entry['merge_commit'] = head
        save(self.pending, pending)
        # Atomic publication prevents publishing only one of the two refs.
        self.git(self.root, 'push', '--atomic', remote,
                 f'refs/heads/{feature["branch"]}:refs/heads/{feature["branch"]}', f'refs/heads/{base}:refs/heads/{base}')
        refs = self.git(self.root, 'ls-remote', remote, f'refs/heads/{base}', f'refs/heads/{feature["branch"]}')
        observed = {line.split()[1]: line.split()[0] for line in refs.splitlines()}
        require(observed.get(f'refs/heads/{base}') == head and observed.get(f'refs/heads/{feature["branch"]}') == commit,
                'Remote publication could not be verified; keep pending state and inspect')
        entry['published'] = True
        return entry

    def finish(self):
        self.pending.unlink(missing_ok=True)
        self.current.unlink(missing_ok=True)
