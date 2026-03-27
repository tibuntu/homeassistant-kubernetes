# Changelog

## [1.1.2](https://github.com/tibuntu/homeassistant-kubernetes/compare/v1.1.1...v1.1.2) (2026-03-27)


### Bug Fixes

* **deps:** group pytest-cov with homeassistant dependencies in Renovate ([675d420](https://github.com/tibuntu/homeassistant-kubernetes/commit/675d420681f7d8e60bd4e7ccca4022874d62805b))
* **deps:** group typescript with typescript-eslint in Renovate ([1001445](https://github.com/tibuntu/homeassistant-kubernetes/commit/10014454b2d15a8a2d0c7f4512d5ada6ea2528ed))
* **deps:** use npm install in Renovate postUpgradeTasks for lock file sync ([4c862f8](https://github.com/tibuntu/homeassistant-kubernetes/commit/4c862f8f84e8b9fde95cf5da340d329f852c1a9f))


### Other

* **deps-frontend:** update dependency vite to v8.0.2 ([22683f2](https://github.com/tibuntu/homeassistant-kubernetes/commit/22683f213e7561006f16e538300ecf948e528b0a))
* **deps-frontend:** update dependency vite to v8.0.3 ([7145dca](https://github.com/tibuntu/homeassistant-kubernetes/commit/7145dcae2d73e839b7c06fd69c140dd726d45e9a))
* **deps-frontend:** update frontend dependencies to v8.57.2 ([e3c9eba](https://github.com/tibuntu/homeassistant-kubernetes/commit/e3c9eba2be96b2f4f777ee5a88dd8a5fad84227b))
* **deps:** update actions/configure-pages action to v6 ([efb8e2a](https://github.com/tibuntu/homeassistant-kubernetes/commit/efb8e2aa1a91629b0c539b850345ee41509e73a6))
* **deps:** update actions/deploy-pages action to v5 ([746fed9](https://github.com/tibuntu/homeassistant-kubernetes/commit/746fed96823cafc7093532301286575a77b94ab1))
* **deps:** update codecov/codecov-action action to v6 ([f340f72](https://github.com/tibuntu/homeassistant-kubernetes/commit/f340f72532745db6254952ad46efdbb936ed189c))
* **deps:** update dependency pytest-homeassistant-custom-component to v0.13.320 ([b314d15](https://github.com/tibuntu/homeassistant-kubernetes/commit/b314d15443dd22be85b9f482e68706bcf7e297b2))
* **deps:** update dependency ruff to v0.15.8 ([8a86a20](https://github.com/tibuntu/homeassistant-kubernetes/commit/8a86a20340fd9e84fea5b6dced58b52eed9eba69))
* **deps:** update pre-commit hook astral-sh/ruff-pre-commit to v0.15.8 ([ac7c785](https://github.com/tibuntu/homeassistant-kubernetes/commit/ac7c785a4d94fc77d0eb6cd6b513d8b980db7225))

## [1.1.1](https://github.com/tibuntu/homeassistant-kubernetes/compare/v1.1.0...v1.1.1) (2026-03-21)


### Bug Fixes

* ensure delete button column is visible in pods table ([535f8b5](https://github.com/tibuntu/homeassistant-kubernetes/commit/535f8b5297fa28b8ba1121e5c7fba8de43ca34a9))

## [1.1.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/v1.0.0...v1.1.0) (2026-03-21)


### Features

* add pod deletion from sidebar panel ([bb2baeb](https://github.com/tibuntu/homeassistant-kubernetes/commit/bb2baeb758089ad28d7d85f241a3939584fb1346))


### Other

* **deps-frontend:** update frontend dependencies ([0b92458](https://github.com/tibuntu/homeassistant-kubernetes/commit/0b92458b79df86ab174ccef53d2723e84b8f67c1))
* **deps-frontend:** update frontend dependencies to v8.57.1 ([fedbb82](https://github.com/tibuntu/homeassistant-kubernetes/commit/fedbb82e39abad54f9117e76766a834e6e6592f4))
* **deps:** update dependency pytest-homeassistant-custom-component to v0.13.318 ([f3d7385](https://github.com/tibuntu/homeassistant-kubernetes/commit/f3d73858bb81a49d0f2a5a6beef14d2ec2ecd93a))
* **deps:** update dependency pytest-homeassistant-custom-component to v0.13.319 ([13f8465](https://github.com/tibuntu/homeassistant-kubernetes/commit/13f8465a63d20a4fc79c7837530e42fd214d1e80))
* **deps:** update ruff to v0.15.7 ([1da97f6](https://github.com/tibuntu/homeassistant-kubernetes/commit/1da97f602349579f892dc61ee990227e814886f8))
* update .gitignore ([16b6e83](https://github.com/tibuntu/homeassistant-kubernetes/commit/16b6e8315ff6563eb0df13cfd6b9285a800cc80a))

## [1.0.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.12.0...v1.0.0) (2026-03-14)


### Features

* add dynamic node discovery for binary sensors ([bf2858d](https://github.com/tibuntu/homeassistant-kubernetes/commit/bf2858dabf8a4c4b29996f6025480ef0493d3fe0))


### Bug Fixes

* add data lock to coordinator to prevent watch/poll race condition ([53e3c42](https://github.com/tibuntu/homeassistant-kubernetes/commit/53e3c429b71f7cf341a5839304968085f450ed82))
* add missing daemonset prefix handler in entity cleanup ([40f19a8](https://github.com/tibuntu/homeassistant-kubernetes/commit/40f19a88bad3c40bb63f649862ebae02225e5997))
* change SSL verification default to True for secure-by-default behavior ([e338ff0](https://github.com/tibuntu/homeassistant-kubernetes/commit/e338ff0bb3ef5966d5bce381f9b020c3ed92b67c))
* guard against None coordinator.data in sensor setup ([04cef70](https://github.com/tibuntu/homeassistant-kubernetes/commit/04cef705d6d212205093e35969bf38195678fe50))
* remove redundant coordinator refresh in sensor and binary_sensor setup ([a4126d2](https://github.com/tibuntu/homeassistant-kubernetes/commit/a4126d290157516abd027851bd02710d9e98faaa))
* return None instead of 0.0 when workload metrics are unavailable ([c2745f8](https://github.com/tibuntu/homeassistant-kubernetes/commit/c2745f87f156168fae2a299f5be65db1637b1419))


### Documentation

* add license, tests, coverage, release, and ko-fi badges to README ([3a10b32](https://github.com/tibuntu/homeassistant-kubernetes/commit/3a10b3210f6cfd538e10b299f1703bf8c6b3d2ab))
* update CLAUDE.md for coordinator data lock and switch refactoring ([da87c8f](https://github.com/tibuntu/homeassistant-kubernetes/commit/da87c8f1ade2d6351f651fccd56ac2a3d8c525de))
* update CLAUDE.md for kubernetes_client, services, and config_flow refactoring ([aba6b55](https://github.com/tibuntu/homeassistant-kubernetes/commit/aba6b55bdab4eb776b962737f675396b906918c5))


### Other

* add generic fetch infrastructure in kubernetes_client.py ([1bded64](https://github.com/tibuntu/homeassistant-kubernetes/commit/1bded64fea5e83385c40c1189da2e58458d05ced))
* add tests for coordinator watch loop, populate, and apply_watch_event ([7246057](https://github.com/tibuntu/homeassistant-kubernetes/commit/72460577b448391d357b1d1b39d54ec7a73ef41f))
* add tests for CronJob switch suspend/resume/update operations ([391772f](https://github.com/tibuntu/homeassistant-kubernetes/commit/391772f332f46f9d17daf53c2eec481a44b96fa8))
* add thread-safe lazy import in config_flow.py ([a7f0a30](https://github.com/tibuntu/homeassistant-kubernetes/commit/a7f0a3070cb8f8acda75c68055bd39cc8ebe62eb))
* consolidate deployment and statefulset switch classes into parameterized base ([6bfe74f](https://github.com/tibuntu/homeassistant-kubernetes/commit/6bfe74f6e247fa97250e1af79a954e6f35c22c52))
* **deps-frontend:** update dependency vite to v8 ([132debf](https://github.com/tibuntu/homeassistant-kubernetes/commit/132debff3bf1a3512523889551fe8baf588b982f))
* **deps-frontend:** update frontend dependencies to v8.57.0 ([176cac0](https://github.com/tibuntu/homeassistant-kubernetes/commit/176cac07b5e6f6ddef5fd0a658d13bad5c5fa8bb))
* **deps:** update ruff to v0.15.6 ([69f3349](https://github.com/tibuntu/homeassistant-kubernetes/commit/69f334914276849335014c4b15d193fd3b18d0b5))
* improve test coverage across all modules for &gt;90% target ([edc4eb2](https://github.com/tibuntu/homeassistant-kubernetes/commit/edc4eb2f9f0abb564d341f46d2953ef123a18852))
* move test_kubernetes_client.py to tests/unit/ ([b3f4acc](https://github.com/tibuntu/homeassistant-kubernetes/commit/b3f4accc1a6f2f4eb5f023e86d3756c86ef2d5e1))
* release 1.0.0 ([d97abfa](https://github.com/tibuntu/homeassistant-kubernetes/commit/d97abfa0eadb23b9d8bbcfa892ec019bd67b6a8f))
* replace fragile unique_id parsing with set-based lookup in entity cleanup ([64e4eb2](https://github.com/tibuntu/homeassistant-kubernetes/commit/64e4eb2f12d785029246e60797a8bcd227b9b8ad))
* simplify workload extraction in services.py ([9f9d056](https://github.com/tibuntu/homeassistant-kubernetes/commit/9f9d0562d137b624030ed35a2250f17d8a0c565f))

## [0.12.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.11.0...v0.12.0) (2026-03-07)


### Features

* add real-time node CPU/memory usage to sidebar panel ([9dd0f01](https://github.com/tibuntu/homeassistant-kubernetes/commit/9dd0f01895634f996d750870e7486b4e39691764))


### Bug Fixes

* **frontend:** type hass as HomeAssistant instead of any ([#124](https://github.com/tibuntu/homeassistant-kubernetes/issues/124)) ([178202c](https://github.com/tibuntu/homeassistant-kubernetes/commit/178202cf2025f6641519e6b6f87d4148bf11d530))
* prevent duplicate entity registration on coordinator updates ([7b49b43](https://github.com/tibuntu/homeassistant-kubernetes/commit/7b49b43186424ef3ebc80398d3471119c276f9cb))
* reuse coordinator's KubernetesClient in service handlers ([#135](https://github.com/tibuntu/homeassistant-kubernetes/issues/135)) ([504d8a1](https://github.com/tibuntu/homeassistant-kubernetes/commit/504d8a15c186ddfc10f94abcae52cc9012360f0f))


### Documentation

* document future test directory structure and update migration status ([6f26a62](https://github.com/tibuntu/homeassistant-kubernetes/commit/6f26a62c1eb18adf8406ec1c41925e029f8b604e))


### Other

* add pytest-homeassistant-custom-component and clean up conftest ([3b93b3a](https://github.com/tibuntu/homeassistant-kubernetes/commit/3b93b3ad38b51b903f5368a066a60a1287233551)), closes [#116](https://github.com/tibuntu/homeassistant-kubernetes/issues/116)
* **deps:** drop redundant pytest pin ([f643634](https://github.com/tibuntu/homeassistant-kubernetes/commit/f6436347f6cb0e0a320180e0dd81d9c2a9e5bc14))
* **deps:** update actions/cache action to v5 ([daba3fb](https://github.com/tibuntu/homeassistant-kubernetes/commit/daba3fb62f0e8e048368165e1d8d3b7a814a5ba9))
* migrate entity platform tests to real HA fixtures ([#120](https://github.com/tibuntu/homeassistant-kubernetes/issues/120)) ([6eb2fee](https://github.com/tibuntu/homeassistant-kubernetes/commit/6eb2fee60496419d1e2c438f3b67ed73e1793b98))
* migrate test_config_flow.py to real HA config flow fixtures ([80d808e](https://github.com/tibuntu/homeassistant-kubernetes/commit/80d808e1c575da609378c9b8af82d4dc9e4883ea)), closes [#118](https://github.com/tibuntu/homeassistant-kubernetes/issues/118)
* migrate test_coordinator.py and test_services.py to real HA fixtures ([5d60568](https://github.com/tibuntu/homeassistant-kubernetes/commit/5d605685fef1117b0bb8b6f86dae1918e198ae86))
* migrate test_init.py and test_device.py to real HA fixtures ([19a0dc5](https://github.com/tibuntu/homeassistant-kubernetes/commit/19a0dc58b9ac049989c8cd93dc24209c430aa5d9)), closes [#117](https://github.com/tibuntu/homeassistant-kubernetes/issues/117)

## [0.11.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.10.0...v0.11.0) (2026-03-07)


### Features

* add WebSocket API and sidebar panel with overview tab ([132fea3](https://github.com/tibuntu/homeassistant-kubernetes/commit/132fea34872026f70c38d19414100c827ca43eee)), closes [#112](https://github.com/tibuntu/homeassistant-kubernetes/issues/112)
* **panel:** add nodes and pods tabs ([38a578a](https://github.com/tibuntu/homeassistant-kubernetes/commit/38a578a993ec381605779f92e01bd0c2720ab764)), closes [#112](https://github.com/tibuntu/homeassistant-kubernetes/issues/112)
* **panel:** add settings tab and enable_panel toggle ([a7e5a88](https://github.com/tibuntu/homeassistant-kubernetes/commit/a7e5a88ae50d73a32668d5b5ef2ce651000563b6)), closes [#112](https://github.com/tibuntu/homeassistant-kubernetes/issues/112)
* **panel:** add workloads tab with management controls ([512edcd](https://github.com/tibuntu/homeassistant-kubernetes/commit/512edcdefe668d1756f0fed7a619378c73d54eb8)), closes [#112](https://github.com/tibuntu/homeassistant-kubernetes/issues/112)


### Bug Fixes

* **panel:** polish UI, fix timestamps, and address review feedback ([343e936](https://github.com/tibuntu/homeassistant-kubernetes/commit/343e9362f0d072bbde2fa3bd6d686073418d9f7e)), closes [#112](https://github.com/tibuntu/homeassistant-kubernetes/issues/112)


### Other

* **deps-frontend:** update dependency eslint to v9.39.4 ([#125](https://github.com/tibuntu/homeassistant-kubernetes/issues/125)) ([1b6a047](https://github.com/tibuntu/homeassistant-kubernetes/commit/1b6a0478b213f99a106e96e0e5965cda165f6807))
* **deps-frontend:** update frontend dependencies ([ce75f27](https://github.com/tibuntu/homeassistant-kubernetes/commit/ce75f273334a5145bf8250658cc1220b713cecee))
* **deps:** update actions/setup-node action to v6 ([ab9f9ae](https://github.com/tibuntu/homeassistant-kubernetes/commit/ab9f9ae54b59a6279a49a87349dd2164574f2e00))
* **deps:** update dependency homeassistant to v2026.3.1 ([95f5290](https://github.com/tibuntu/homeassistant-kubernetes/commit/95f529070c5e795521612d95bdd2d99a1a29a360))
* **deps:** update dependency node to v24 ([88e1440](https://github.com/tibuntu/homeassistant-kubernetes/commit/88e1440398ecad22e2af9e0c1f15e9a550bc96b8))
* **deps:** update ruff to v0.15.5 ([#121](https://github.com/tibuntu/homeassistant-kubernetes/issues/121)) ([f6a71c1](https://github.com/tibuntu/homeassistant-kubernetes/commit/f6a71c1ef96640ceeed16d257fa7b19fca9e5bb0))
* **frontend:** rebuild panel bundle with vite 7.3.1 ([31a1f01](https://github.com/tibuntu/homeassistant-kubernetes/commit/31a1f012c06ab9f174cdbc8ac39ad3a08de90892))

## [0.10.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.9.0...v0.10.0) (2026-03-02)


### Features

* add experimental Watch API with opt-in options flow ([55e1528](https://github.com/tibuntu/homeassistant-kubernetes/commit/55e1528483d50213aa7c724ad81f01a2203b6fdd))
* add reconfigure flow for modifying existing integration entries ([82f4d4b](https://github.com/tibuntu/homeassistant-kubernetes/commit/82f4d4b20f6b8363655861c8cd9d5fbc8411615c))


### Bug Fixes

* **devcontainer:** replace default_config with individual components in devcontainer ([5cdc802](https://github.com/tibuntu/homeassistant-kubernetes/commit/5cdc80241b416b18bb9fdeb0a2bb37392c25395b))
* **tests:** resolve options flow and coordinator test fixtures ([6743343](https://github.com/tibuntu/homeassistant-kubernetes/commit/6743343152506cecb1c0ed6e1dc916529dc0c858))


### Other

* add Watch API coverage ([ac90d46](https://github.com/tibuntu/homeassistant-kubernetes/commit/ac90d46cdb93bf455778d4b0e2b72be7807b0534))
* **deps:** update ruff to v0.15.4 ([#108](https://github.com/tibuntu/homeassistant-kubernetes/issues/108)) ([6fbb137](https://github.com/tibuntu/homeassistant-kubernetes/commit/6fbb1379541512d08647d3387d9de9a554d999c6))
* restructure manifests and update docs ([ac13d41](https://github.com/tibuntu/homeassistant-kubernetes/commit/ac13d413a8d74af27092d0e5e2c3fff620aa1b72))

## [0.9.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.8.0...v0.9.0) (2026-02-26)


### Features

* add individual CronJob status sensors ([f37814a](https://github.com/tibuntu/homeassistant-kubernetes/commit/f37814a386a1607738e41df8cdb3eecb70c49939)), closes [#99](https://github.com/tibuntu/homeassistant-kubernetes/issues/99)
* add Kubernetes Jobs monitoring ([543384f](https://github.com/tibuntu/homeassistant-kubernetes/commit/543384f64cf4dcf37e22ad45d6930d515c9b6e0c)), closes [#100](https://github.com/tibuntu/homeassistant-kubernetes/issues/100)
* add node condition binary sensors ([2c35999](https://github.com/tibuntu/homeassistant-kubernetes/commit/2c359991149268b23696ce5a03cbf119d4b70c6e)), closes [#101](https://github.com/tibuntu/homeassistant-kubernetes/issues/101)


### Other

* boost coverage to 80% threshold ([e7bef57](https://github.com/tibuntu/homeassistant-kubernetes/commit/e7bef5783c7b26ba06bbfb734938106eb3e0dc97))
* **deps:** fix pre-commit hook grouping for ruff, mypy and bandit ([a4808cd](https://github.com/tibuntu/homeassistant-kubernetes/commit/a4808cdd589f27064496f9d2d3d9d1ddaaf8aa97))
* **deps:** group ruff pip and pre-commit updates together ([725faa9](https://github.com/tibuntu/homeassistant-kubernetes/commit/725faa99248712dd965bc4ea7ba66d36153cd1f1))
* **deps:** update dependency bandit to v1.9.4 ([#103](https://github.com/tibuntu/homeassistant-kubernetes/issues/103)) ([6a654be](https://github.com/tibuntu/homeassistant-kubernetes/commit/6a654be8ffc6dc7c0377335080e1e2f7bc24824f))
* **deps:** update dependency ruff to v0.15.3 ([54a6431](https://github.com/tibuntu/homeassistant-kubernetes/commit/54a643114d4236f1249bfa0b82b129049c798c4f))
* **deps:** update pre-commit hook astral-sh/ruff-pre-commit to v0.15.3 ([#106](https://github.com/tibuntu/homeassistant-kubernetes/issues/106)) ([b9bb934](https://github.com/tibuntu/homeassistant-kubernetes/commit/b9bb9341376e820eca8d287c47523add8a9be434))
* **deps:** update pre-commit hook pycqa/bandit to v1.9.4 ([#104](https://github.com/tibuntu/homeassistant-kubernetes/issues/104)) ([74af939](https://github.com/tibuntu/homeassistant-kubernetes/commit/74af939ec371cda5ca138079714748c74c0b11a5))
* **docs:** migrate from mkdocs to zensical ([6d28093](https://github.com/tibuntu/homeassistant-kubernetes/commit/6d2809302e41d3215262630b648ec69e0287ca0e))

## [0.8.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.7.2...v0.8.0) (2026-02-22)


### Features

* add CPU and memory usage sensors for deployments and statefulsets ([5219a5b](https://github.com/tibuntu/homeassistant-kubernetes/commit/5219a5b7b7b43387044901e29955e9d7360dc5d2))
* add individual DaemonSet status sensors ([71b05bd](https://github.com/tibuntu/homeassistant-kubernetes/commit/71b05bd181f3b1d7c5e96c78a9e4ecc7bd82f787))
* add readiness status sensors for deployments and statefulsets ([be8bf2c](https://github.com/tibuntu/homeassistant-kubernetes/commit/be8bf2c56b7d4a671abd60e4e79c0d82ff1d7897))


### Bug Fixes

* resolve all mypy type errors ([04a189f](https://github.com/tibuntu/homeassistant-kubernetes/commit/04a189f91a3f176ed1baf67a65ea5863fc015671))


### Documentation

* add missing pages to navigation ([e904be3](https://github.com/tibuntu/homeassistant-kubernetes/commit/e904be3d5a4013f355e67712e4bb6ba8e8c6e728))
* clean up README ([1118f9d](https://github.com/tibuntu/homeassistant-kubernetes/commit/1118f9d4225772a6e2f21e933c1d5dccc3cd16d8))


### Other

* add instruction to auto-update CLAUDE.md ([a0be942](https://github.com/tibuntu/homeassistant-kubernetes/commit/a0be942881324298c3a44850a1a94cb86be6d256))
* add test coverage instruction to CLAUDE.md ([5fb885b](https://github.com/tibuntu/homeassistant-kubernetes/commit/5fb885b05a1d3573bf9cbd8989a0eb26044a99d5))
* add version management and documentation instructions ([f42c587](https://github.com/tibuntu/homeassistant-kubernetes/commit/f42c5873132d706a9eec4eb902c5206da69bb693))
* **config:** enable pre-commit manager, group updates ([ae956ee](https://github.com/tibuntu/homeassistant-kubernetes/commit/ae956ee5f5377bddbd651a17e16c92bfdee97761))
* **deps:** align kubernetes version with manifest.json ([56eb90c](https://github.com/tibuntu/homeassistant-kubernetes/commit/56eb90c6b4ac41b83684f5bcaf07f271a15e9879))
* **deps:** update dependency homeassistant to v2026.2.3 ([3f335f5](https://github.com/tibuntu/homeassistant-kubernetes/commit/3f335f5303e0363b1e567e03a17b69a2c19907a6))
* **deps:** update pre-commit hook pre-commit/pre-commit-hooks to v6 ([bbb92f2](https://github.com/tibuntu/homeassistant-kubernetes/commit/bbb92f2e03f6300b0c6b4dd841572c5833f3007d))
* **deps:** update pre-commit hooks ([58e4e53](https://github.com/tibuntu/homeassistant-kubernetes/commit/58e4e53365425717e9db710b9a8f90a16bd98db5))
* remove unused flake8 config ([79cae7d](https://github.com/tibuntu/homeassistant-kubernetes/commit/79cae7d0678f643e90b19bddc6f411833b1f8d7b))
* **Renovate:** automerge patch updates from pyproject.toml ([e861914](https://github.com/tibuntu/homeassistant-kubernetes/commit/e8619144e678bdd51a758d03e5e47a0599825dd5))
* **Renovate:** enforce build(deps) prefix for pyproject.toml updates ([4173c40](https://github.com/tibuntu/homeassistant-kubernetes/commit/4173c40b83fbd34aa1138c5c5055cee92348e816))

## [0.7.2](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.7.1...v0.7.2) (2026-02-20)


### Bug Fixes

* **deps:** update dependency bandit to v1.9.3 ([48fdc5f](https://github.com/tibuntu/homeassistant-kubernetes/commit/48fdc5f4297637bfd599ea387158e5d883ec9ea9))
* **deps:** update dependency mkdocs-material to v9.7.2 ([2a1b047](https://github.com/tibuntu/homeassistant-kubernetes/commit/2a1b047c38ffca2214d58d32341f649ade741345))
* **deps:** update dependency mypy to v1.19.1 ([ab80cf4](https://github.com/tibuntu/homeassistant-kubernetes/commit/ab80cf4a69b79946c84f22e061a7bb9e8ace4a5a))
* **deps:** update dependency pre-commit to v4.5.1 ([2569c61](https://github.com/tibuntu/homeassistant-kubernetes/commit/2569c6190f41e18f990cebb1f26cbf71eb6bd890))
* **deps:** update dependency pytest to v8.4.2 ([3abac7d](https://github.com/tibuntu/homeassistant-kubernetes/commit/3abac7d6d15462acaa29b21d8d21f9b65d5728b1))
* **deps:** update dependency pytest to v9 ([5aab780](https://github.com/tibuntu/homeassistant-kubernetes/commit/5aab78067fc730df572f777dd1a9f1900de00815))
* **deps:** update dependency pytest-asyncio to v1.3.0 ([18d8b08](https://github.com/tibuntu/homeassistant-kubernetes/commit/18d8b084974f4f5cb70de0910a047076d6a7c0e9))
* **deps:** update dependency pytest-cov to v7 ([9d8d33b](https://github.com/tibuntu/homeassistant-kubernetes/commit/9d8d33bb191eaab0b3b776fc52b787f43bbe9147))
* **deps:** update dependency ruff to v0.15.2 ([7ae996a](https://github.com/tibuntu/homeassistant-kubernetes/commit/7ae996a7bf8d04b155674452d070b5f016a39143))


### Other

* add .claude/ to gitignore ([4a2c3fa](https://github.com/tibuntu/homeassistant-kubernetes/commit/4a2c3fab56815a7586fb3d19bb142f6172302f4a))
* **ci:** add Claude PR Assistant workflow ([3be7e9c](https://github.com/tibuntu/homeassistant-kubernetes/commit/3be7e9c87702ad46af9a219c470cc689474ef722))
* **ci:** only trigger claude on-demand and with specific permissions ([91eca28](https://github.com/tibuntu/homeassistant-kubernetes/commit/91eca2893e61b7f747a82c90840a9895babd958e))
* **config:** migrate config renovate.json ([729800f](https://github.com/tibuntu/homeassistant-kubernetes/commit/729800f2a7227817c839b5ecb402639a3d5cc42c))
* **deps:** update actions/checkout action to v6 ([cb5c4a9](https://github.com/tibuntu/homeassistant-kubernetes/commit/cb5c4a9a20be13118dcd89ef5777f5fbe9d36b1b))
* **deps:** update dependency kubernetes to v35 ([3f47940](https://github.com/tibuntu/homeassistant-kubernetes/commit/3f4794024fde804169652ec4d54b7d25b32604dd))
* migrate to ruff, clean up dependencies, and improve Renovate tracking ([a868b68](https://github.com/tibuntu/homeassistant-kubernetes/commit/a868b68c966ee44c351c0c5256a8ac6fa9caaba9))
* **Renovate:** do not longer create fix commits for any kind of updates ([3972f58](https://github.com/tibuntu/homeassistant-kubernetes/commit/3972f58709acba56bc5320a5ccdd742d3de16adc))

## [0.7.1](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.7.0...v0.7.1) (2026-02-11)


### Bug Fixes

* service data not being parsed and thus called correctly selecting multiple workloads ([7ff332b](https://github.com/tibuntu/homeassistant-kubernetes/commit/7ff332b0a45d6495e8772dab7efedf868cf3d97a))


### Documentation

* update README to improve contribution section ([0f43109](https://github.com/tibuntu/homeassistant-kubernetes/commit/0f43109476305b4165980497b4724d26bd7bd410))


### Other

* add test for service calls with multiple entities (workloads) ([cbf6511](https://github.com/tibuntu/homeassistant-kubernetes/commit/cbf6511c71bddfbeab7fec0b156fbe99969b1ce6))

## [0.7.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.6.0...v0.7.0) (2026-01-02)


### Features

* enhance integration setup process ([8a3a93c](https://github.com/tibuntu/homeassistant-kubernetes/commit/8a3a93c2b90a90ceff69685ce2f610e34ae71699)), closes [#71](https://github.com/tibuntu/homeassistant-kubernetes/issues/71)
* ensure consistency in workload type attribute usage across components ([a9dd208](https://github.com/tibuntu/homeassistant-kubernetes/commit/a9dd208058eb86e7d5837b2167f25f2935199d98))
* group all entities, sensors, etc. by devices wich represent k8s clusters and their namespaces for better organization ([6dd2286](https://github.com/tibuntu/homeassistant-kubernetes/commit/6dd2286bb3e28d972e3d146c7e07f1de6fc71190)), closes [#66](https://github.com/tibuntu/homeassistant-kubernetes/issues/66)

## [0.6.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.5.0...v0.6.0) (2025-12-31)


### Features

* add counter for DaemonSets ([864e7a1](https://github.com/tibuntu/homeassistant-kubernetes/commit/864e7a1172032616af4b4007df5878dcc5a21ea6)), closes [#70](https://github.com/tibuntu/homeassistant-kubernetes/issues/70)
* add metrics support for deployments to get cpu usage & memory usage per deployment ([35267f7](https://github.com/tibuntu/homeassistant-kubernetes/commit/35267f7392a65060f52c66c80341ac2c3714a220))
* add metrics support for statefulsets (cpu and memory usage) ([44811ac](https://github.com/tibuntu/homeassistant-kubernetes/commit/44811ac4d0b6f4560b72fcf8aef3e8ab9b3e86dc))
* add pod entities support ([285211b](https://github.com/tibuntu/homeassistant-kubernetes/commit/285211b8789a9da0dc3575e826d0d608fd2d5184)), closes [#59](https://github.com/tibuntu/homeassistant-kubernetes/issues/59)


### Bug Fixes

* ensure pod metrics are fetched from all namespaces ([05f7036](https://github.com/tibuntu/homeassistant-kubernetes/commit/05f70360cd9fb012bb183fa1d9eb8ad265914a90))
* remove device_info property from Kubernetes switch entities ([c70a85d](https://github.com/tibuntu/homeassistant-kubernetes/commit/c70a85db8df05f9cc30dfd551ea6184ae0fb27e4))


### Other

* add configuration schema for Kubernetes integration ([154b924](https://github.com/tibuntu/homeassistant-kubernetes/commit/154b924f7c7737925a5966e3c06ca1d143c2c9e5))
* add daemonset counter and reflect pod icon changes ([5125967](https://github.com/tibuntu/homeassistant-kubernetes/commit/5125967ead2dc6d80a0f0c18b5c32ae5d4ddb286))
* consolidate Kubernetes service operations under a unified workload model ([80302e6](https://github.com/tibuntu/homeassistant-kubernetes/commit/80302e6823b786e0194eb981590854eb3e43af23)), closes [#61](https://github.com/tibuntu/homeassistant-kubernetes/issues/61)
* **deps:** update actions/checkout action to v6 ([aac02c6](https://github.com/tibuntu/homeassistant-kubernetes/commit/aac02c6e5805f4017f2cf26e039c262002a0bca8))
* **deps:** update dependency python to 3.14 ([23b27b1](https://github.com/tibuntu/homeassistant-kubernetes/commit/23b27b1d646451dedc4012b55f7653a7cc5f1e8d))
* **deps:** update mcr.microsoft.com/devcontainers/python docker tag to v3.14 ([267bde6](https://github.com/tibuntu/homeassistant-kubernetes/commit/267bde6c5433ee3802a367bec9f7a4d62edeab97))
* ensure pod entity tests match current sensor attributes ([a53b5c5](https://github.com/tibuntu/homeassistant-kubernetes/commit/a53b5c558fbe397a447c9f30d9b7494411ce61cb))
* reflect update to Python 3.14 ([9525c22](https://github.com/tibuntu/homeassistant-kubernetes/commit/9525c22c74ba3d356964c6eb7569d6a5505e8c50))
* remove uid and label attributes from pod entities ([bc917f2](https://github.com/tibuntu/homeassistant-kubernetes/commit/bc917f29dae152261e848be4c823923a234056db))
* use Kubernetes logo for pod entities ([727e2a5](https://github.com/tibuntu/homeassistant-kubernetes/commit/727e2a5e7a45d8368532218ca0fa24b2aee09203))

## [0.5.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.4.1...v0.5.0) (2025-10-05)


### Features

* add detailed kubernetes node information functionality ([e148276](https://github.com/tibuntu/homeassistant-kubernetes/commit/e1482762d91b6b90de45a79bcbe9ea9beb733f24))
* enhance Kubernetes sensor functionality with dynamic discovery and recovery tests ([4b597ad](https://github.com/tibuntu/homeassistant-kubernetes/commit/4b597ad1458ce9017617569f6717f81af3e8b99b))


### Bug Fixes

* streamline logging in get_nodes() and enhance type hinting ([5385488](https://github.com/tibuntu/homeassistant-kubernetes/commit/53854886e747e2065dbd9b759a02f6313db7d692))


### Documentation

* improve RBAC configuration to allow usage of manifests without cloning the repo ([52e959b](https://github.com/tibuntu/homeassistant-kubernetes/commit/52e959b443273aa0343980415a11f94ed5fd6dcd))


### Other

* add network host argument to devcontainer configuration ([764f57f](https://github.com/tibuntu/homeassistant-kubernetes/commit/764f57f934a834320d379a0aa99df46a4713c891))
* **deps:** update actions/setup-python action to v6 ([6ea39f9](https://github.com/tibuntu/homeassistant-kubernetes/commit/6ea39f9cd338569be96f3dd71ea9ef38f1f9e7fe))
* improve KubernetesNodeSensor and tests for better readability ([276bd04](https://github.com/tibuntu/homeassistant-kubernetes/commit/276bd04c41d7a064f8d7a587f9ac9065337f1155))
* remove debug logging from coordinator and sensor ([e86451e](https://github.com/tibuntu/homeassistant-kubernetes/commit/e86451e76d4986bb8065dc210e8e29aa8f10ebea))

## [0.4.1](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.4.0...v0.4.1) (2025-09-12)


### Bug Fixes

* restore pyproject.toml after accidental replacement ([6202d2f](https://github.com/tibuntu/homeassistant-kubernetes/commit/6202d2f664e257eaaa42c12fbaad84e17f3c7d01))


### Other

* **ci:** do not longer ignore brands category within HACS action ([0086b94](https://github.com/tibuntu/homeassistant-kubernetes/commit/0086b94ee596e5e0ffa047ae6d2c713a3680326c))
* **deps:** update dependency python to 3.13 ([2019644](https://github.com/tibuntu/homeassistant-kubernetes/commit/20196449448be4ce0683f742c59946b7fd6b90f6))
* ensure pyproject.toml is updated during releases ([5ed2d62](https://github.com/tibuntu/homeassistant-kubernetes/commit/5ed2d62c7414a3c959911213fae568a810450f14))
* revert to release please release-type python ([18f52f7](https://github.com/tibuntu/homeassistant-kubernetes/commit/18f52f715e87fd0608cded9a8c516b2862346132))

## [0.4.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.3.0...v0.4.0) (2025-08-30)


### Features

* enhance workload type validation and error handling in Kubernetes services ([a6c9901](https://github.com/tibuntu/homeassistant-kubernetes/commit/a6c9901cb754c0e8ac03142d24430e30b4e48883))


### Bug Fixes

* remove direct update logic from sensor classes and skip cleanup for count sensors ([3ab183b](https://github.com/tibuntu/homeassistant-kubernetes/commit/3ab183bfae135caf91f84da480ae3e04d24bbaa2))


### Other

* remove file parameter from codecov action in CI workflow ([90190c4](https://github.com/tibuntu/homeassistant-kubernetes/commit/90190c4d04a1ab846d506b2298f5a74e3bc5f49c))
* update release configuration to enhance changelog structure and visibility ([b38b99c](https://github.com/tibuntu/homeassistant-kubernetes/commit/b38b99c57d2f4ed882765b039df1095d0c9d4e6f))

## [0.3.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.2.5...v0.3.0) (2025-08-24)


### Features

* add support for CronJobs ([2151238](https://github.com/tibuntu/homeassistant-kubernetes/commit/2151238f52ed8b4bc941402e3fd884049ac9a588)), closes [#38](https://github.com/tibuntu/homeassistant-kubernetes/issues/38)


### Documentation

* simplify README.md ([ea0bd9c](https://github.com/tibuntu/homeassistant-kubernetes/commit/ea0bd9c09d2c5f07f6cd86b49aefb3b00bdd26ce))

## [0.2.5](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.2.4...v0.2.5) (2025-08-23)


### Bug Fixes

* improve cleanup of callbacks and services in Kubernetes integration ([d4a8737](https://github.com/tibuntu/homeassistant-kubernetes/commit/d4a87374cbee7547be412679299cc96bde74743a))

## [0.2.4](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.2.3...v0.2.4) (2025-08-23)


### Bug Fixes

* sensors not longer being properly exposed ([32c8cf1](https://github.com/tibuntu/homeassistant-kubernetes/commit/32c8cf1547ff918560d0269d8a5cc541adf0a4c0))

## [0.2.3](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.2.2...v0.2.3) (2025-08-23)


### Bug Fixes

* add async_setup function and improve domain usage in Kubernetes integration ([5463ba6](https://github.com/tibuntu/homeassistant-kubernetes/commit/5463ba69ac1edd5da676061fe12e3be84d64671e))

## [0.2.2](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.2.1...v0.2.2) (2025-08-17)


### Bug Fixes

* import KubernetesConfigFlow in __init__.py for proper configuration flow handling ([a3ec065](https://github.com/tibuntu/homeassistant-kubernetes/commit/a3ec06501a769a5e6b1ded962391876a4859097e))

## [0.2.1](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.2.0...v0.2.1) (2025-08-17)


### Bug Fixes

* update Kubernetes binary sensor and sensor setup to use shared coordinator and client ([7871ec0](https://github.com/tibuntu/homeassistant-kubernetes/commit/7871ec0b7015d3ded40c2fe717db0b2da9bb06b4))

## [0.2.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/0.1.0...v0.2.0) (2025-08-16)

### Features

* implement automatic entity cleanup and dynamic discovery ([5ea04fa](https://github.com/tibuntu/homeassistant-kubernetes/commit/5ea04fa9e061b144085df11bf2583444f763b267))

### Bug Fixes

* **deps:** update dependency mypy to v1.17.1 ([ca3d733](https://github.com/tibuntu/homeassistant-kubernetes/commit/ca3d733192953a00a017cd434bd32e34f64e4021))
