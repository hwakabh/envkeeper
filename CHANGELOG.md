# Changelog

## [0.6.1](https://github.com/hwakabh/envkeeper/compare/v0.6.0...v0.6.1) (2025-03-02)


### Bug Fixes

* conditions to determine deployment status. ([32b0dfe](https://github.com/hwakabh/envkeeper/commit/32b0dfe63389ce957cb0e5644982745564296d3c))
* variables names in delete_inactive_deployment(). ([3824e31](https://github.com/hwakabh/envkeeper/commit/3824e3118407947898b591ed9a827454bb6c6535))


### Continuous Integration

* **deps:** updated Python for build errors with Paketo Python buildpacks. ([b55abb3](https://github.com/hwakabh/envkeeper/commit/b55abb37006a6681da7171d3cda509bb8459939c))

## [0.6.0](https://github.com/hwakabh/envkeeper/compare/v0.5.1...v0.6.0) (2025-03-02)


### Features

* enabled to handle failure deployments. ([ea36f32](https://github.com/hwakabh/envkeeper/commit/ea36f3247170b4d4905d43e12a93dc30b67b435c))


### Code Refactoring

* commented out delete_inactive_deployment(). ([d253f11](https://github.com/hwakabh/envkeeper/commit/d253f11e8f8081ffa3320bbe87b8099b4e5b4beb))

## [0.5.1](https://github.com/hwakabh/envkeeper/compare/v0.5.0...v0.5.1) (2025-02-12)


### Bug Fixes

* added repository options to checkout in being triggered. ([0c5de5e](https://github.com/hwakabh/envkeeper/commit/0c5de5ecc8f0a5d57ad2a03cacc9c6d7efea84d5))

## [0.5.0](https://github.com/hwakabh/envkeeper/compare/v0.4.0...v0.5.0) (2025-02-10)


### Features

* added build pipeline. ([c9d4c05](https://github.com/hwakabh/envkeeper/commit/c9d4c050fe3431d3410fb4f0769a3bed0efad6dd))


### Bug Fixes

* added setup-python and Procfile for builds. ([2733875](https://github.com/hwakabh/envkeeper/commit/2733875aa1b85a5c7b5b22af583702ce9fafe6d3))


### Continuous Integration

* enhanced release-please configs. ([83af186](https://github.com/hwakabh/envkeeper/commit/83af1862df54367919c1b1912336840808b08f1c))

## [0.4.0](https://github.com/hwakabh/envkeeper/compare/v0.3.3...v0.4.0) (2025-01-29)


### Features

* **cli:** added cleanups of blank environments. ([db465ef](https://github.com/hwakabh/envkeeper/commit/db465ef274ec95cd4eb10f3d17b05e119b58b2a3))

## [0.3.3](https://github.com/hwakabh/envkeeper/compare/v0.3.2...v0.3.3) (2025-01-28)


### Bug Fixes

* **cli:** fixed error on unused instantiations. ([76cb2bb](https://github.com/hwakabh/envkeeper/commit/76cb2bbc3ddd112ddc48958c165462145cdbf783))

## [0.3.2](https://github.com/hwakabh/envkeeper/compare/v0.3.1...v0.3.2) (2025-01-28)


### Reverts

* **cli:** async implementations for debug. ([c3814f0](https://github.com/hwakabh/envkeeper/commit/c3814f0e8960a1ed8fbe5b1e5626d298a2d4d581))

## [0.3.1](https://github.com/hwakabh/envkeeper/compare/v0.3.0...v0.3.1) (2025-01-28)


### Bug Fixes

* **actions:** installation process from external repo ([e1e8243](https://github.com/hwakabh/envkeeper/commit/e1e8243a0bfe511da41dfde9aeabedcfa7f91336))

## [0.3.0](https://github.com/hwakabh/envkeeper/compare/v0.2.3...v0.3.0) (2025-01-28)


### Features

* **cli:** implemented asyncio with ProcessPoolExecutor for GitHub API call. ([58b372c](https://github.com/hwakabh/envkeeper/commit/58b372c4719c2337a5f34079b2f0bac0fefa4d4f))
* **cli:** implemented seek subcommands. ([5aa02c9](https://github.com/hwakabh/envkeeper/commit/5aa02c92a4eaa128c5f18c184b515a69995ca160))

## [0.2.3](https://github.com/hwakabh/envkeeper/compare/v0.2.2...v0.2.3) (2025-01-28)


### Bug Fixes

* **ci:** removed duplications in triggers ([e5b549d](https://github.com/hwakabh/envkeeper/commit/e5b549d32ec18030ce9a4b186dbc3f1e13b520b0))

## [0.2.2](https://github.com/hwakabh/envkeeper/compare/v0.2.1...v0.2.2) (2025-01-28)


### Bug Fixes

* **ci:** used PAT instead of GITHUB_TOKEN for release-please-action ([00e911a](https://github.com/hwakabh/envkeeper/commit/00e911aaeacaef72d8e9038fc51fde8d49a3cd4c))

## [0.2.1](https://github.com/hwakabh/envkeeper/compare/v0.2.0...v0.2.1) (2025-01-28)


### Bug Fixes

* **ci:** updated triggers for release. ([8d259b6](https://github.com/hwakabh/envkeeper/commit/8d259b67369bdb9aba3c46a442f36f25893b9792))

## [0.2.0](https://github.com/hwakabh/envkeeper/compare/v0.1.0...v0.2.0) (2025-01-28)


### Features

* **actions:** added core logics of envkeeper-action. ([987e32f](https://github.com/hwakabh/envkeeper/commit/987e32fc7fde68532bc2b801d76ef66d68fca71e))
* **ci:** applied latest codes in topic PRs for e2e validation. ([c800282](https://github.com/hwakabh/envkeeper/commit/c800282ac0fb1b4808aaa2456b03700fd631b24d))
* **ci:** included package version file to release-please. ([efce45f](https://github.com/hwakabh/envkeeper/commit/efce45f2fb1e79b17e05a9f6c0b14f99f067b266))
* **cli:** enabled to parse CLI arguments. ([e348b20](https://github.com/hwakabh/envkeeper/commit/e348b20f456cb747d9ff5c198e36fd9d94770d54))
* enabled to override value of --repo with GH_REPONAME ([97a4325](https://github.com/hwakabh/envkeeper/commit/97a4325f8c2d3f7129afe20648ad865178ab91b2))
* enhanced CLI args. ([070ce32](https://github.com/hwakabh/envkeeper/commit/070ce325d572267fdefdc490b1ba13d9ee1f6242))
* fetched package version. ([7cc2202](https://github.com/hwakabh/envkeeper/commit/7cc2202b68de602022986f3df60d4105d3af1ea1))
* implemented core logics based on Gist. ([3ed7e10](https://github.com/hwakabh/envkeeper/commit/3ed7e10ce1533b477eb874705ebca64a3e02176c))


### Bug Fixes

* **cli:** added missing args for headers. ([52c96ba](https://github.com/hwakabh/envkeeper/commit/52c96ba173e0bbbc8654c581a4923a4aea4cb9c4))

## [0.1.0](https://github.com/hwakabh/envkeeper/compare/v0.0.1...v0.1.0) (2025-01-24)


### Features

* added required files for packagings. ([e41eb0a](https://github.com/hwakabh/envkeeper/commit/e41eb0a86502bfddec65e08fb4d6c02c17f576ed))
* pinned Python version. ([7bd1d93](https://github.com/hwakabh/envkeeper/commit/7bd1d93a6a3235d3b2cf79bf7db5c35b918e6532))
* project initialization. ([e43f5cb](https://github.com/hwakabh/envkeeper/commit/e43f5cba8b6a1397035073ce5fe598b30f2bbc9d))


### Documentation

* added descriptions of application overview. ([ee222a0](https://github.com/hwakabh/envkeeper/commit/ee222a0ec9861f4517816c4feacaf9e7fa746d36))
