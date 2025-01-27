import argparse
import json
import os
import sys

from urllib.request import urlopen
from urllib.request import Request


GH_TOKEN = os.environ.get('GH_TOKEN', None)
HEADER = {
    'authorization': 'token ' + GH_TOKEN,
    'accept': 'application/vnd.github.ant-man-preview+json'
}


def get_version():
    return '0.1.0'


def cli():
    p, args = fetch_cli_args()

    # validate subcommand is either: `seek` or `clean`
    # in case we will not use `dest` in subparser, argparse.namespace object is not iterable, need to cast as dict
    if args.subcommand is None:
        print('Missing subcommand arguments\n')
        p.print_help()
        sys.exit(1)

    if args.subcommand == 'help':
        p.print_help()
        sys.exit(1)

    if args.subcommand == 'version':
        print(f'{get_version()}')
        sys.exit(1)


    # validate format of --repo value and GH_TOKEN
    if not cli_precheck(repo=args.repo, token=GH_TOKEN):
        sys.exit(1)


    GH_REPONAME = args.repo

    # Fetch mappings between environment & deployment
    print(f'Get mappings between environments and deployments from repo: {GH_REPONAME}')
    pairs = fetch_pairs(repo=GH_REPONAME)
    print(f'Got {len(pairs)}')
    for p in pairs:
        print(p)

    print('')

    # validation: exit if no deployment there
    if len(pairs) == 0:
        print(f'No environment found in repo: {GH_REPONAME}\n')
        sys.exit(1)

    # Get list of environment
    print('Get list of environments ...')
    environments = fetch_environments(repo=GH_REPONAME)
    for e in environments:
        print(e['name'])

    print('')

    # Get depoyments related to each environment
    print('Get deployments related to each environment ...')
    for env in environments:

        # URL list of deployment
        deploy_urls = get_deployments_by_env(mappings=pairs, env_name=env['name'])
        print(f'Environment [ {env['name']} ] has the following deployments: ')

        # Get the statues linked to each deployment
        for deploy_url in deploy_urls:
            deployment_id = deploy_url.split('/')[-2]
            states = get_deployment_statuses(status_url=deploy_url)
            print(f'\tFound {len(states)} statues in deployment_id [ {deployment_id} ]')
            # for s in states:
            #     print(f'\t\tID: {s[0]}, Status: {s[1]}')

            # Validate deployment can be deleted or not
            is_inactive = is_inactive_deployment(d=deploy_url)
            print(f'\tNo active statuses: {is_inactive}')

            if is_inactive:
                print(f'\tDelete the deployment [ {deployment_id} ] ...')
                url = f'https://api.github.com/repos/{GH_REPONAME}/deployments/{deployment_id}'
                with urlopen(Request(method='DELETE', url=url, headers=HEADER)) as r:
                    r.read().decode('utf-8')
                if r.getcode() != 204:
                    print('Error')
                else:
                    print(f'>>> Done, {r.getcode()}')

            else:
                print('This is active deployment, nothing to do ...')
        print()

    sys.exit(0)


def fetch_cli_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='envkp controls GitHub staled environments',
        epilog='notes: --token option is not recommended for the security perspectives, please use GH_TOKEN variables instead.'
    )
    # TODO: --repo can be overriden by GH_REPONAME, so not required=True
    parser.add_argument('-r', '--repo', required=True, help='target repsitory with \'owner/reponame\' format')
    parser.add_argument('-V', '--version', action='version', version=get_version())
    parser.add_argument('--token', help='provide GitHub Personal access token')

    subparsers = parser.add_subparsers(dest='subcommand')

    parser1 = subparsers.add_parser("clean", help='Purge environments/deployments in repo')
    parser1.add_argument('-f', '--force', action='store_true', help='force delete all environment including active ones')

    parser2 = subparsers.add_parser("seek", help='Fetch list of environments/deployments in repo')
    parser2.add_argument('-v', '--verbose', action='store_true', help='get more details')

    parser3 = subparsers.add_parser("help", help='Print help')
    parser4 = subparsers.add_parser("version", help='Print version')

    return parser, parser.parse_args()


def cli_precheck(repo, token):
    print('Fetching GitHub username & repository name from shell')

    if (len(repo.split('/')) != 2):
        print('  GH_REPONAME format invalid, please set the value with `repo_owner/repo_name` format.\n')
        return False

    print('Fetching GitHub PAT from shell')
    if token is None:
        print('  GH_TOKEN not provides, please set environmental variable with your shell.\n')
        return False

    return True



def fetch_pairs(repo):
    # returns the list such as:
    # {'url': 'https://api.github.com/repos/hwakabh/bennu-official.page/deployments/2116891061/statuses', 'env': 'production'}
    # {'url': 'https://api.github.com/repos/hwakabh/bennu-official.page/deployments/2116882302/statuses', 'env': 'production'}
    # {'url': 'https://api.github.com/repos/hwakabh/bennu-official.page/deployments/2116868983/statuses', 'env': 'bennu-official.page-pr-228'}
    # ...
    # this is the core mappings between env name & deployment

    url = f'https://api.github.com/repos/{repo}/deployments?per_page=100'

    with urlopen(Request(method='GET', url=url, headers=HEADER)) as r:
        res = r.read().decode('utf-8')
    resjson = json.loads(res)

    # TODO: be dynamic with fetching GitHub pagenations
    # currently supports only >= 200 deployments
    if is_pagenated(resp=r):
        url += '&page=2'
        with urlopen(Request(method='GET', url=url, headers=HEADER)) as r:
            res = r.read().decode('utf-8')
        n = json.loads(res)
        for e in n:
            resjson.append(e)

    return [{'url': r.get('statuses_url'), 'env': r.get('environment')} for r in resjson]


def fetch_environments(repo):
    url = f'https://api.github.com/repos/{repo}/environments'

    with urlopen(Request(method='GET', url=url, headers=HEADER)) as r:
        res = r.read().decode('utf-8')
    resjson = json.loads(res)

    return resjson.get('environments')


def get_deployments_by_env(mappings, env_name):
    return [mapping['url'] for mapping in mappings if mapping['env'] == env_name]


def is_pagenated(resp):
    # get Request() response object and check if elements with ('Link', '...') or not
    keys = [h[0] for h in resp.getheaders()]
    return 'Link' in keys


def is_inactive_deployment(d):
    # The active deployment will not have `inactive` status in the statuses list
    # we can consider deployment can be deleted if its status contains `inactive`

    # TODO: consider the pattern if `in_progress` + `failure`
    states = [status[1] for status in get_deployment_statuses(status_url=d)]
    return 'inactive' in states



def get_deployment_statuses(status_url):
    # Get deployment statuses_url and return the list of statuses related to the deployment
    with urlopen(Request(method='GET', url=status_url, headers=HEADER)) as r:
        res = r.read().decode('utf-8')
    resjson = json.loads(res)

    return [(state.get('id'), state.get('state')) for state in resjson]



# def make_inactive(status_url):
#     print('Following Deployements would be deactivated')
#     payload = {'state': 'inactive'}
#     post_payload = json.dumps(payload).encode('utf-8')
#     with urlopen(Request(method='POST', url=target_url, headers=post_header, data=post_payload)) as r:
#         r.read().decode('utf-8')
