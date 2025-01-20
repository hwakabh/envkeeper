# {{ repository_name }}
Note: This file is expected to generate from template. See [.github wiki](https://github.com/hwakabh/.github/wiki) for detailed instructions.

## Templating checklists
- [ ] Replace `{{ repository_name }}` as placeholder text above with your repository name
- [ ] Initialize default labels with `github-label-setup` command
- [ ] Adjust `CODEOWNERS`
- [ ] Update `release-type` in [`.github/config/release-please-config.json`](./.github/config/release-please-config.json) (default: `python`)
  - See more in documents of [release-please](https://github.com/googleapis/release-please?tab=readme-ov-file#strategy-language-types-supported)
- [ ] Replace `GH_USERNAME` and `GH_REPONAME` in [CONTRIBUTING.md](./CONTRIBUTING.md)
- [ ] Replace `GH_USERNAME` and `GH_REPONAME` for [`semantic-issue-action`](https://github.com/hwakabh/semantic-issue-action) in [`.github/workflows/semantic-issue.yaml`](./.github/workflows/semantic-issue.yaml)
- [ ] Validate repository access of [semantic-prs](https://github.com/Ezard/semantic-prs) GitHub Apps, whose configurations exists [`.github/semantic.yml`](./.github/semantic.yml)
- [ ] Enable `Allow GitHub Actions to create and approve pull requests` as Workflow Permision in repository settings
  - release-please requires permission to raise PR with your repository and for this you need to update workflow permission in your repository settings
  - Refer to the capture below and enable GitHub Actions to raise PR to your repository

![Workflow Permissions](https://github.com/user-attachments/assets/8018b45c-571d-4245-a71e-1c5ec678baff)

Then, you can clean texts above in this section and update with any of descriptions for your project!
The following headers are skeletons of basic README.

## Local Setup
Environmental variables, Makefile, docker-compose, ...etc

## Good to know / Caveats
Anything if you have

## License
Choose licenses for your project, see more details in [GitHub Official Docs](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-a-license-to-a-repository)
