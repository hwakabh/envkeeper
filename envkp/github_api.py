import json
from urllib.request import urlopen
from urllib.request import Request


GITHUB_API_BASE = 'https://api.github.com'


def build_repo_url(repo, *path_segments):
    """Construct a GitHub API URL for a given repo and path segments.

    Example: build_repo_url('owner/name', 'deployments', '123')
      -> 'https://api.github.com/repos/owner/name/deployments/123'
    """
    base = f'{GITHUB_API_BASE}/repos/{repo}'
    if path_segments:
        base += '/' + '/'.join(str(s) for s in path_segments)
    return base


def api_get(url, headers):
    """Perform GET request and return parsed JSON response and raw response object."""
    with urlopen(Request(method='GET', url=url, headers=headers)) as r:
        res = r.read().decode('utf-8')
    return json.loads(res), r


def api_delete(url, headers):
    """Perform DELETE request and return the HTTP status code."""
    with urlopen(Request(method='DELETE', url=url, headers=headers)) as r:
        r.read().decode('utf-8')
    return r.getcode()


def check_delete_result(status_code, entity_desc):
    """Print success/error message for a DELETE operation."""
    if status_code != 204:
        print(f'Error deleting {entity_desc}')
    else:
        print(f'Done, {status_code}')
