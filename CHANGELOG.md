# Changelog

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
