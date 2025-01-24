# envkeeper


## What is Envkeeper?
Coming from Environment Housekeeper

***

## as a GitHub Actions
Custom Composit GitHub Actions to run `Envkeeper` (`envkp`) for housekeeping GitHub Environment.

### Usage

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
        uses: hwakabh/envkeeper@v0.1.0
```

### Inputs


### Outputs

***

## envkp
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
% envkp clean --repo ${reponame}
% envkp seek --repo ${reponame}
```

### Environmental Variables
`GH_TOKEN`

***

## envkp-dump
TBA for brief descriptions of `envkp-dump`

### Usage

```shell
% envkp-dump --repo ${reponame}
% envkp-dump --repo ${reponame} --verbose
```

### Environmental Variables


***


## Good to know / Caveats
Anything if you have

