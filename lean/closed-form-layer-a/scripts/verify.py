#!/usr/bin/env python3
"""Reproduce the production cloud build and compare the theorem and axiom text."""
import argparse
import difflib
import os
from pathlib import Path
import signal
import subprocess
import sys

from sources import check

ROOT = Path(__file__).resolve().parent.parent
THEOREM = 'ClosedForm.closed_form_of_covers'


def compare(label, actual, root=ROOT):
    expected = (root / 'expected' / (label + '.txt')).read_text()
    if actual != expected:
        sys.stderr.writelines(difflib.unified_diff(
            expected.splitlines(True), actual.splitlines(True),
            fromfile='expected/' + label + '.txt', tofile='produced/' + label + '.txt'))
        raise ValueError(label + ' does not match')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--jobs', type=int, default=1, help='compiler processes (default: 1)')
    args = ap.parse_args()
    if args.jobs < 1:
        ap.error('--jobs must be positive')
    check()
    subprocess.run([sys.executable, 'scripts/run_cloud.py', '--jobs', str(args.jobs)],
                   cwd=ROOT, check=True)
    state = ROOT / 'BUILD.step7-state'
    # This log was freshly built or hash-validated by the scheduler above.
    audit = (state / 'logs/ClosedForm.FinalAudit.log').read_text()
    lines = [line for line in audit.splitlines()
             if line.startswith("'" + THEOREM + "' depends on axioms:")]
    if len(lines) != 1:
        raise ValueError('Expected exactly one main theorem axiom report')
    compare('axioms', lines[0] + '\n')
    query = state / 'PrintStatement.lean'
    query.write_text('import ClosedForm.Cloud.Statement\n'
                     'set_option pp.maxSteps 100000\n'
                     '#check ' + THEOREM + '\n')
    env = dict(os.environ, LEAN_NUM_THREADS='4')
    logpath = state / 'statement.log'
    lock = ROOT / '.lake/step1-build.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        with logpath.open('w') as log, (state / 'statement-stderr.log').open('w') as err:
            child = subprocess.Popen(['nice', '-n', '10', 'lake', 'env', 'lean',
                                      str(query.relative_to(ROOT))],
                                     cwd=ROOT, env=env, stdout=log,
                                     stderr=err, start_new_session=True)
            try:
                child.wait(timeout=600)
            except subprocess.TimeoutExpired:
                (state / 'TIMEOUT').write_text('PrintStatement\n')
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
                raise ValueError('Statement printing exceeded 600 seconds; stopped')
            except BaseException:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
                raise
        if child.returncode:
            raise ValueError('Statement printing failed; see BUILD.step7-state/statement.log')
        compare('statement', logpath.read_text())
    finally:
        lock.unlink()
    print('VERIFIED')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print('Verification failed: ' + str(exc), file=sys.stderr)
        sys.exit(1)
