# envkeeper


## What is Envkeeper?
Coming from Environment Housekeeper

***

## envkeeper-actions
Custom Composit GitHub Actions to run `Envkeeper` (`envkp`) for housekeeping GitHub Environment. \
<https://github.com/marketplace/actions/envkeeper-actions>

### Usage
Create workflows (ex. `.github/workflows/envkeeper.yaml`) for using GitHub Actions of envkeeper with contexts:

```yaml
name: Purge staled environment
on:
  schedule:
    # Runs on 19:00 JST every day, note that cron syntax applied as UTC
    - cron: '0 10 * * *'
  workflow_dispatch:

jobs:
  cleanup-env:
    steps:
      - name: Clean up Environments
        uses: hwakabh/envkeeper@main
        with:
          token: ${{ github.token }}
          repo: ${{ github.repository }}
```

### Inputs
Inputs have been defined in [`action.yml`](./action.yml):

| Name | Required | Description |
| --- | --- | --- |
| `token` | true | Token to use to authorize. Typically the GITHUB_TOKEN secrets. |
| `repo` | true | Target repository to check issue title. |

Note that GitHub Actions of envkeeper will delete Deployments in the repository, the token has the scope for `repo_deployment`.

### Outputs
TBD

***

## envkp CLI
TBA for brief descriptions of `envkp`

### CLI Install
`envkp` can be installed from PyPI with `pip`, `poetry`, `uv`, ...etc

or, Directly from Git with `pip`

### Local Setup
- Using setuptools
Instead of using package manager, you can download the sourcse and setup locally using `setuptools` (setup.py)
Environmental variables, Makefile, docker-compose, ...etc

- Using .whl files
Download from releases and install via pip

### Usage

```shell
% envkp --repo ${reponame} clean
% envkp --repo ${reponame} seek
```

### Environmental Variables

| Name | Required | Description |
| --- | --- | --- |
| `GH_TOKEN` | true | Token to use to authorize. Typically the GITHUB_TOKEN secrets. |
| `GH_REPONAME` | false | equivalent with the input for `--repo` |

***

## Good to know / Caveats
Anything if you have

