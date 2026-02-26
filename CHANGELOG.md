# Changelog

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
