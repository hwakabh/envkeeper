# envkeeper

<!-- *** -->
## What is Envkeeper?
`Envkeeper`, coming from "Environment Housekeeper", is a custom [composite GitHub Actions](https://docs.github.com/en/actions/sharing-automations/creating-actions/about-custom-actions#composite-actions) to manage GitHub Deployments and its Environment associated. \
Thanks to this great features of GitHub, we can realize [Continuous Delivery by GitHub Actions](https://docs.github.com/en/actions/about-github-actions/about-continuous-deployment-with-github-actions), and you can use GitHub Envionments for the applications [integrated](https://docs.github.com/en/actions/use-cases-and-examples/deploying/deploying-with-github-actions#using-environments) its repo.

As many of application platforms (PaaS) have PR environments, where it can automatically create GitHub Environment/Deployments and associated acutal deploys on the platforms with linking to Pull Requests, but several services will NOT clean up after the PRs will be merged. \
So you might see many of staled environements/deployments have been associated to your repository, and for resolving these kind of caveats we need to have any solutions to purge staled objects in GitHub ([StackOverflow's ref](https://stackoverflow.com/questions/53452910/how-to-remove-a-github-environment)).

With using `envkp` CLI, which will be available with Envkeeper, you can completely purge these staled deployments and linked environments.

<!-- *** -->
## envkeeper-actions
As you can use Envkeeper with several forms of implementations according to your requirements, one of the best way is to use as GitHub Actions. \
Since we developed Custom Composit GitHub Actions to run `Envkeeper` (`envkp`) for housekeeping GitHub Environment, it can be available in [GitHub Marketplace](https://github.com/marketplace/actions/envkeeper-actions).

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
    runs-on: ubuntu-24.04

    permissions:
      deployments: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          ref: ${{ github.head_ref }}

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
| `token` | true | Token to use to authorize. Typically the [GITHUB_TOKEN](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication#about-the-github_token-secret) secrets. |
| `repo` | true | Target repository to check issue title. |

Note that GitHub Actions of envkeeper will delete Deployments in the repository, the token has the scope for `repo_deployment`.

### Outputs
TBU, under development.

| Name | Required | Description |
| --- | --- | --- |
| `result` | false | The results of operations |


<!-- *** -->
## envkp CLI
As well as envkeeper-actions, you can also use `envkp` on your local environment as client tools. \
Since `envkp` has been developed purely as Python package, it can be available in [PyPI repository](https://pypi.org/project/envkp/).

### CLI Install
As mentioned, `envkp` can be installed from PyPI, so you can easily install it with your favorite Python package manager (such as [`pip`](https://pip.pypa.io/en/stable/), [`poetry`](https://python-poetry.org/docs/), [`uv`](https://docs.astral.sh/uv/), ...etc). \
Please follow its documents for installation of the package manager first, and be sure that enable `venv` if you need to have isolated environments.

```shell
# pip
% pip install envkp

# poetry
% poetry add envkp

# uv
% uv add envkp
```

With `pip` case you can also download it directly from GitHub looked like below, or of course you can download each formats of Python packages files (`.tar.gz` or `.whl` formats) from [here](https://pypi.org/project/envkp/#files), and install directly from each file according to your requirements.

```shell
# Git
% pip install git+https://github.com/hwakabh/envkeeper.git
```

Though it has been [deprecated way](https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html), where we will use `setuptools` (`setup.py`) for package installations, you can use one of the options using it if you have already had `setuptools` in your environments:

```shell
% python setup.py install
```

### Usage
`envkp` has two main subcommands: `clean` and `seek`, and both of them will expect repository name as its arguments. \
Please note that the value for `--repo` should be formed as `owner/reponame`, for example `hwakabh/envkeeper`.

```shell
% envkp --repo ${reponame} clean
% envkp --repo ${reponame} seek
```

`envkp clean` will
- delete all deployments of repo whose status is `inactive`. This means active deployments, where upstream/latest application code basis are deployed, will NOT be deleted for secure operations.
- delete all environments of repo, where no deployment has been associated to any deployments

`envkp seek` will
- print information of deployments/environments in the repository


### Environmental Variables

| Name | Required | Description |
| --- | --- | --- |
| `GH_TOKEN` | true | Token to use to authorize. Typically the GITHUB_TOKEN secrets. |
| `GH_REPONAME` | false | equivalent with the input for `--repo` |


<!-- *** -->
## Good to know / Caveats
Similar solutions it can be available on GitHub:
- <https://github.com/strumwolf/delete-deployment-environment>
- <https://github.com/int128/delete-deployments-action>

