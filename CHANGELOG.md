# Changelog

## [0.5.0](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.4.1...v0.5.0) (2025-09-03)


### Features

* add MIT License to the project ([da0c012](https://github.com/tibuntu/homeassistant-kubernetes/commit/da0c012e09bb11a98c5473821e5961e60ae1a47d))
* add script to update documentation links and modify existing links in DEVELOPMENT.md ([8001a5e](https://github.com/tibuntu/homeassistant-kubernetes/commit/8001a5e4b2e659e455ad6bfeac6f10d53b652d85))
* add support for CronJobs ([2151238](https://github.com/tibuntu/homeassistant-kubernetes/commit/2151238f52ed8b4bc941402e3fd884049ac9a588)), closes [#38](https://github.com/tibuntu/homeassistant-kubernetes/issues/38)
* enhance workload type validation and error handling in Kubernetes services ([a6c9901](https://github.com/tibuntu/homeassistant-kubernetes/commit/a6c9901cb754c0e8ac03142d24430e30b4e48883))
* implement automatic entity cleanup and dynamic discovery ([5ea04fa](https://github.com/tibuntu/homeassistant-kubernetes/commit/5ea04fa9e061b144085df11bf2583444f763b267))
* initial commit ([e6fdcd0](https://github.com/tibuntu/homeassistant-kubernetes/commit/e6fdcd01719c4f1f2e5bfa1c8c71ae354bea60a1))
* **kubernetes:** add service definitions for scaling, starting, and stopping deployments ([8c7428d](https://github.com/tibuntu/homeassistant-kubernetes/commit/8c7428d0e573123cdb5b82b6b83f4be4b802e054))
* **kubernetes:** add StatefulSet support with scaling and sensor integration ([1cfca1d](https://github.com/tibuntu/homeassistant-kubernetes/commit/1cfca1d657b71a14834c250b6f5730c05a34dc1b))
* **kubernetes:** add workload type constants and update deployment switch attributes ([a8a0f47](https://github.com/tibuntu/homeassistant-kubernetes/commit/a8a0f472ecc5d4d91476b53949e7cbdc8fd07022))
* **kubernetes:** enhance deployment switch functionality with scaling verification and cooldown ([1c23596](https://github.com/tibuntu/homeassistant-kubernetes/commit/1c2359644796130607563e85b5955019c6cfb773))
* **kubernetes:** enhance integration with advanced polling and state management features ([51fcf02](https://github.com/tibuntu/homeassistant-kubernetes/commit/51fcf02c33a5e6392ab3448343bfb1f8ea82cf56))
* **kubernetes:** enhance scaling logic ([c629f95](https://github.com/tibuntu/homeassistant-kubernetes/commit/c629f95bdf1515e74c920db95b9e74ca7a30d47a))
* **kubernetes:** enhance service account setup and RBAC permissions for Home Assistant integration ([7862307](https://github.com/tibuntu/homeassistant-kubernetes/commit/7862307724ff1da01f8f0e026e2c9072145722af))
* **kubernetes:** expand cluster role permissions for deployments and statefulsets ([0fe8a0f](https://github.com/tibuntu/homeassistant-kubernetes/commit/0fe8a0f727692655d0cd22d2255cf63c3e733991))
* **logging:** enhance error logging and add authentication testing methods ([7a3dc7d](https://github.com/tibuntu/homeassistant-kubernetes/commit/7a3dc7d194d2a9b9d03c8dae4100f2fe4280ab34))
* **service:** enhance deployment and statefulset management with multi-selection support ([c63a0a1](https://github.com/tibuntu/homeassistant-kubernetes/commit/c63a0a1c3233e27ceb37ba912e2a330547508df3))
* **tests:** enhance Kubernetes integration tests with mock coordinator and new configurations ([a83f6ea](https://github.com/tibuntu/homeassistant-kubernetes/commit/a83f6ea9ecade6753a6b140bd35424c12bc7ae1e))


### Bug Fixes

* add async_setup function and improve domain usage in Kubernetes integration ([5463ba6](https://github.com/tibuntu/homeassistant-kubernetes/commit/5463ba69ac1edd5da676061fe12e3be84d64671e))
* deployment and statefulset name extraction and validation ([4625f13](https://github.com/tibuntu/homeassistant-kubernetes/commit/4625f13eac3329258cdd9788821d07a4f20f822b))
* **deps:** update dependency black to v22.12.0 ([266e267](https://github.com/tibuntu/homeassistant-kubernetes/commit/266e267de2eb907e8e4e4e640cef797e0d5f83db))
* **deps:** update dependency black to v25 ([e575ea8](https://github.com/tibuntu/homeassistant-kubernetes/commit/e575ea8f811c1825641ad840ed9ab5be585ff020))
* **deps:** update dependency flake8 to v4.0.1 ([6ec251a](https://github.com/tibuntu/homeassistant-kubernetes/commit/6ec251a3150d62eccf9e6ac614cd96fc3856de23))
* **deps:** update dependency flake8 to v7.3.0 ([106a490](https://github.com/tibuntu/homeassistant-kubernetes/commit/106a49000d2f119dfd73221595bfca887dadb3df))
* **deps:** update dependency homeassistant to v2025.7.3 ([c1a2c06](https://github.com/tibuntu/homeassistant-kubernetes/commit/c1a2c06c22e4065361fc39e2739c29900a8fd57f))
* **deps:** update dependency importlib-metadata to v8 ([386dec3](https://github.com/tibuntu/homeassistant-kubernetes/commit/386dec3daf4172ce1d771873f53c31dc4345f2e9))
* **deps:** update dependency isort to v5.13.2 ([560106a](https://github.com/tibuntu/homeassistant-kubernetes/commit/560106adcf003575f1480dc5ba722314b8c827e0))
* **deps:** update dependency isort to v6 ([8b62e79](https://github.com/tibuntu/homeassistant-kubernetes/commit/8b62e7915c266f5a853c708fbcedf039f0466cfd))
* **deps:** update dependency kubernetes to v33 ([f6c538f](https://github.com/tibuntu/homeassistant-kubernetes/commit/f6c538f0708430eb7078561f1aa3ac8e5c9cd5bc))
* **deps:** update dependency mypy to v1 ([0133663](https://github.com/tibuntu/homeassistant-kubernetes/commit/01336634505809e5d9252400ed69dd25032b4f05))
* **deps:** update dependency mypy to v1.17.1 ([ca3d733](https://github.com/tibuntu/homeassistant-kubernetes/commit/ca3d733192953a00a017cd434bd32e34f64e4021))
* **deps:** update dependency pytest to v7.4.4 ([32dcf60](https://github.com/tibuntu/homeassistant-kubernetes/commit/32dcf60fd6cc76d72838d191f0399b10a99570b3))
* **deps:** update dependency pytest to v8 ([ad98c68](https://github.com/tibuntu/homeassistant-kubernetes/commit/ad98c681d6b9b4ede550f6e514a7d08b37666898))
* **deps:** update dependency pytest-asyncio to v1 ([c1ac26c](https://github.com/tibuntu/homeassistant-kubernetes/commit/c1ac26cae96faa5f0f7d70202a5ef1098e49323d))
* import KubernetesConfigFlow in __init__.py for proper configuration flow handling ([a3ec065](https://github.com/tibuntu/homeassistant-kubernetes/commit/a3ec06501a769a5e6b1ded962391876a4859097e))
* improve cleanup of callbacks and services in Kubernetes integration ([d4a8737](https://github.com/tibuntu/homeassistant-kubernetes/commit/d4a87374cbee7547be412679299cc96bde74743a))
* remove direct update logic from sensor classes and skip cleanup for count sensors ([3ab183b](https://github.com/tibuntu/homeassistant-kubernetes/commit/3ab183bfae135caf91f84da480ae3e04d24bbaa2))
* restore pyproject.toml after accidental replacement ([6202d2f](https://github.com/tibuntu/homeassistant-kubernetes/commit/6202d2f664e257eaaa42c12fbaad84e17f3c7d01))
* sensors not longer being properly exposed ([32c8cf1](https://github.com/tibuntu/homeassistant-kubernetes/commit/32c8cf1547ff918560d0269d8a5cc541adf0a4c0))
* update Kubernetes binary sensor and sensor setup to use shared coordinator and client ([7871ec0](https://github.com/tibuntu/homeassistant-kubernetes/commit/7871ec0b7015d3ded40c2fe717db0b2da9bb06b4))


### Documentation

* add HACS badge to README for easier integration visibility ([e8cc7f2](https://github.com/tibuntu/homeassistant-kubernetes/commit/e8cc7f29941308620ea2c5105129822f23cfce15))
* add hacs.json ([f928063](https://github.com/tibuntu/homeassistant-kubernetes/commit/f92806373efb0b9a906af5a0a1a2c237ea3f5c97))
* add mkdocs setup ([a6f5b97](https://github.com/tibuntu/homeassistant-kubernetes/commit/a6f5b970c4ab74a690d7355c8abff72a116bb914))
* enhance documentation with additional details and formatting improvements ([77e6dc2](https://github.com/tibuntu/homeassistant-kubernetes/commit/77e6dc20f221f2c2f3ba9e5f188f7f1e50e96297))
* restructure README and move detailed documentation to docs directory ([ae54b30](https://github.com/tibuntu/homeassistant-kubernetes/commit/ae54b303f5d2bd7ef940bef53090ca6f52b829d0))
* simplify README.md ([ea0bd9c](https://github.com/tibuntu/homeassistant-kubernetes/commit/ea0bd9c09d2c5f07f6cd86b49aefb3b00bdd26ce))
* update links in README to point to mkdocs ([72f181b](https://github.com/tibuntu/homeassistant-kubernetes/commit/72f181b57e481e5b1440ab0ecf5f305255a366d8))
* update README for improved clarity and organization ([84d4cfa](https://github.com/tibuntu/homeassistant-kubernetes/commit/84d4cfa17917af28cf1e951e75b479f6d8c5c7f2))


### Other

* add .gitignore file to exclude Python artifacts, virtual environments, and sensitive data ([cdcae6c](https://github.com/tibuntu/homeassistant-kubernetes/commit/cdcae6c4e65932fac83cd8641d127c73d7a58186))
* add .node_modules/ to .gitignore ([b8f912a](https://github.com/tibuntu/homeassistant-kubernetes/commit/b8f912a4da2cbf12f5da96decbeb3c640a6ab607))
* add comprehensive unit tests for Kubernetes integration components including config flow, coordinator, client, sensors, and services ([26ac4c7](https://github.com/tibuntu/homeassistant-kubernetes/commit/26ac4c705b0cc5ee3c7752e8935f9c89244b9612))
* add Flake8 configuration for code style enforcement ([b4cf3cd](https://github.com/tibuntu/homeassistant-kubernetes/commit/b4cf3cd0e3f529aa968e5f6befad53c86d408bce))
* add GitHub Actions workflow for managing stale issues and pull requests ([4643018](https://github.com/tibuntu/homeassistant-kubernetes/commit/46430182ef67927a67928622d8b1e66188a3d5b3))
* add initial devcontainer setup for local testing ([82bbf64](https://github.com/tibuntu/homeassistant-kubernetes/commit/82bbf6412dbb099e84f915f84a4460e33a011600))
* add pre-commit configuration for code quality enforcement and validation checks ([5fea407](https://github.com/tibuntu/homeassistant-kubernetes/commit/5fea4075f0706a615f7e29a59d9553ec9fb0db2e))
* **ci:** add GitHub actions ([5a2a85f](https://github.com/tibuntu/homeassistant-kubernetes/commit/5a2a85f0c17d7bd929b123c4a5b9b8ddba05e314))
* **ci:** add HACS validation workflow and update hassfest and validate workflows for consistency ([6d2d0ac](https://github.com/tibuntu/homeassistant-kubernetes/commit/6d2d0ac8755768079143c85a544bcba4780f93ba))
* **ci:** add release please action ([4a8d4a7](https://github.com/tibuntu/homeassistant-kubernetes/commit/4a8d4a7e04ccd006ee0b31edd86d03865541a15f))
* **ci:** add release-please configuration ([927a39c](https://github.com/tibuntu/homeassistant-kubernetes/commit/927a39c4d52c098703fcf40f2d72a0b774389677))
* **ci:** do not longer ignore brands category within HACS action ([0086b94](https://github.com/tibuntu/homeassistant-kubernetes/commit/0086b94ee596e5e0ffa047ae6d2c713a3680326c))
* **ci:** improve test workflow logic ([5d9c93b](https://github.com/tibuntu/homeassistant-kubernetes/commit/5d9c93b2e78706adfe677130d20fa34573b614ed))
* **ci:** remove update_docu_links.py execution from validation workflow ([3d72fa4](https://github.com/tibuntu/homeassistant-kubernetes/commit/3d72fa4f797424e9bfb49353242b44298f0f27dc))
* **deps:** set specific package versions ([f8396cc](https://github.com/tibuntu/homeassistant-kubernetes/commit/f8396ccbe9af47b5d1d92af8071f88115327f996))
* **deps:** update actions/checkout action to v5 ([9a36641](https://github.com/tibuntu/homeassistant-kubernetes/commit/9a366417efecda378cbaad985e25f021d752ec0c))
* **deps:** update actions/configure-pages action to v5 ([6df8ea6](https://github.com/tibuntu/homeassistant-kubernetes/commit/6df8ea6d88854abccc86dd5ae11fd18683575e4f))
* **deps:** update actions/setup-python action to v5 ([c81c282](https://github.com/tibuntu/homeassistant-kubernetes/commit/c81c28285d44a3a1176c43123a0f0e6931ed280d))
* **deps:** update actions/upload-pages-artifact action to v4 ([b45ba02](https://github.com/tibuntu/homeassistant-kubernetes/commit/b45ba024d15765349e8bcec636f4d88c26a7fb6f))
* **deps:** update codecov/codecov-action action to v5 ([dcf01c2](https://github.com/tibuntu/homeassistant-kubernetes/commit/dcf01c22d844d446de1730f58ce73cfc7ff78bda))
* **deps:** update dependency aiohttp to v3.12.14 ([03d9570](https://github.com/tibuntu/homeassistant-kubernetes/commit/03d9570fc80994fcf9327895e812db6ea9c23b48))
* **deps:** update dependency kubernetes to v33 ([f0aee4a](https://github.com/tibuntu/homeassistant-kubernetes/commit/f0aee4a7a975343936e32c8b09568ad1d75455eb))
* **deps:** update dependency python to 3.13 ([2019644](https://github.com/tibuntu/homeassistant-kubernetes/commit/20196449448be4ce0683f742c59946b7fd6b90f6))
* **deps:** update dependency python to 3.13 ([c2dfc07](https://github.com/tibuntu/homeassistant-kubernetes/commit/c2dfc07d6ad1a34652641ba198e983bf241c2479))
* **deps:** update setuptools and aiohttp dependencies, modify project description, and include custom components ([80c55c7](https://github.com/tibuntu/homeassistant-kubernetes/commit/80c55c7c222093f72d308da4458a4af1f7c069b4))
* **docs:** streamline service account setup instructions and remove deprecated development setup script ([6b4046d](https://github.com/tibuntu/homeassistant-kubernetes/commit/6b4046d1e59af33aa02993ae737182d83eb6e422))
* **docs:** update development prerequisites to require Python 3.12 and Home Assistant 2025.7 ([59d7673](https://github.com/tibuntu/homeassistant-kubernetes/commit/59d7673f53402a2641ca8c772c989071c517ebad))
* downgrade safety dependency version in pyproject.toml for compatibility ([5724f26](https://github.com/tibuntu/homeassistant-kubernetes/commit/5724f26bdb2e122710005291a82a7fced6d9839d))
* enhance GitHub Actions workflow for coverage reporting ([476a7ae](https://github.com/tibuntu/homeassistant-kubernetes/commit/476a7aea607ec05c2dd5a8aa46fe45e4f2887635))
* ensure pyproject.toml is updated during releases ([5ed2d62](https://github.com/tibuntu/homeassistant-kubernetes/commit/5ed2d62c7414a3c959911213fae568a810450f14))
* improve code readability and organization across multiple files ([ca069d0](https://github.com/tibuntu/homeassistant-kubernetes/commit/ca069d08a2463c8ed92a418eb3b0513f221d56a6))
* **kubernetes:** remove services count functionality and update documentation ([97ede06](https://github.com/tibuntu/homeassistant-kubernetes/commit/97ede0692235655b26be13b39848e483ee0e2003))
* **kubernetes:** remove update_docu_links.py script and enhance error handling for Kubernetes package import ([835cf78](https://github.com/tibuntu/homeassistant-kubernetes/commit/835cf78356b7f2e63942c174b1905ea1cde06f82))
* **kubernetes:** update manifest for issue tracking and requirements ([09fd92d](https://github.com/tibuntu/homeassistant-kubernetes/commit/09fd92ddab1a6c95146821acec3fada105544084))
* **main:** release 0.2.0 ([05b4aa6](https://github.com/tibuntu/homeassistant-kubernetes/commit/05b4aa6b3327a21192039e47e780b7b66b97a011))
* **main:** release 0.2.1 ([71f0202](https://github.com/tibuntu/homeassistant-kubernetes/commit/71f0202ea26a4d9bddd1a687c2f8bdfb0ebb55b0))
* **main:** release 0.2.2 ([340e312](https://github.com/tibuntu/homeassistant-kubernetes/commit/340e312350b67eff237d06d55cb593ffaf8ddbc5))
* **main:** release 0.2.3 ([4152409](https://github.com/tibuntu/homeassistant-kubernetes/commit/41524093eb0e2be8a9a3a2ba8e045150f4200e79))
* **main:** release 0.2.4 ([d2b4728](https://github.com/tibuntu/homeassistant-kubernetes/commit/d2b4728f871dd4603f28e28698c8896d76d98c1c))
* **main:** release 0.2.5 ([92f1388](https://github.com/tibuntu/homeassistant-kubernetes/commit/92f13889ccde7924b6b10f2051e41c1d18367e00))
* **main:** release 0.3.0 ([aa64d6f](https://github.com/tibuntu/homeassistant-kubernetes/commit/aa64d6f331cac0dd67676f0b61731252ff8d48b0))
* **main:** release 0.4.0 ([8e87782](https://github.com/tibuntu/homeassistant-kubernetes/commit/8e87782372a30e7b386affbac663ad5650ba103c))
* **main:** release 0.4.1 ([15b3463](https://github.com/tibuntu/homeassistant-kubernetes/commit/15b3463488710494c0d20b2fee2f58ac4882a7cb))
* prepare release 0.1.0 ([ca94104](https://github.com/tibuntu/homeassistant-kubernetes/commit/ca94104ab093aaa389bf6c1e874f2ea80b24f8fd))
* remove bump options from release configuration ([59bdea7](https://github.com/tibuntu/homeassistant-kubernetes/commit/59bdea75239947fec2d71b4c5f4437b6a00e1d7a))
* remove falsy symlink ([c600a82](https://github.com/tibuntu/homeassistant-kubernetes/commit/c600a822890190043f9aec08dfca55e9b7fba649))
* remove file parameter from codecov action in CI workflow ([90190c4](https://github.com/tibuntu/homeassistant-kubernetes/commit/90190c4d04a1ab846d506b2298f5a74e3bc5f49c))
* remove non-existing icon from HASS manifest ([5c69de4](https://github.com/tibuntu/homeassistant-kubernetes/commit/5c69de41db77574efe1efe835c9b85d8ee31a662))
* remove stale-issue action ([0af9b48](https://github.com/tibuntu/homeassistant-kubernetes/commit/0af9b4802b6d8c18022fc7b43a91522ec690cf2b))
* simplify formatting in renovate.json and .devcontainer/devcontainer.json for improved readability ([da93074](https://github.com/tibuntu/homeassistant-kubernetes/commit/da9307489877a560393c5a6d6089ea70d6bdbe9e))
* sort keys in manifest.json alphabetically ([09a1a66](https://github.com/tibuntu/homeassistant-kubernetes/commit/09a1a667157e110c0ef38a23a7818f3f9fc20f7a))
* standardize quotes in configuration files and improve formatting in manifests ([42c614b](https://github.com/tibuntu/homeassistant-kubernetes/commit/42c614bf4d15853340ca221f24ad0166345488bc))
* **tests:** replace AsyncMock with MagicMock in Kubernetes integration tests ([fa12f4b](https://github.com/tibuntu/homeassistant-kubernetes/commit/fa12f4b65f35938aef62c0087b7b08b48c387f29))
* typo ([f61a152](https://github.com/tibuntu/homeassistant-kubernetes/commit/f61a152a754cd3c54e7ad94069ef21d3c99ab52d))
* update .gitignore to remove leading dot from node_modules entry ([c7b9e2e](https://github.com/tibuntu/homeassistant-kubernetes/commit/c7b9e2efe3b03379274e9567187c93833f2b762b))
* update GitHub workflows ([aae116f](https://github.com/tibuntu/homeassistant-kubernetes/commit/aae116f2e068c4fc9bfa9c446f769ddc16454927))
* update HACS workflow configuration to ignore brands for now ([7e042c5](https://github.com/tibuntu/homeassistant-kubernetes/commit/7e042c56433b23f1dcacaf67638ceb4da40cdfe8))
* update manifest and translations for Kubernetes component ([e1d8980](https://github.com/tibuntu/homeassistant-kubernetes/commit/e1d898092cc11e8f388489af671267d1edc7b294))
* update pre-commit configuration to limit prettier hook to YAML files only ([387aa2b](https://github.com/tibuntu/homeassistant-kubernetes/commit/387aa2bbe55f88b28f0564e9f8dac6b712b37a22))
* update project metadata and dependencies, change versioning and author information ([0bb8efc](https://github.com/tibuntu/homeassistant-kubernetes/commit/0bb8efc4016e48b2d2a8bd12763172fec59431ec))
* update project version and dependency specifications in pyproject.toml and requirements.txt ([0f78dd5](https://github.com/tibuntu/homeassistant-kubernetes/commit/0f78dd51688e9f55f3a84efcc81bbdb9535eb574))
* update pyproject.toml with enhanced dependency management, including new optional groups for quality, testing, and documentation tools ([2c68039](https://github.com/tibuntu/homeassistant-kubernetes/commit/2c68039823ce4f1bcfef7caf367ca91262ab0714))
* update Python version requirement to 3.13 and homeassistant dependency to 2025.7.2 ([fb828ef](https://github.com/tibuntu/homeassistant-kubernetes/commit/fb828ef952fcf7b78673cd7065b4f395a16cb545))
* update release configuration to enhance changelog structure and visibility ([b38b99c](https://github.com/tibuntu/homeassistant-kubernetes/commit/b38b99c57d2f4ed882765b039df1095d0c9d4e6f))
* update release type in configuration from node to python ([357dbbc](https://github.com/tibuntu/homeassistant-kubernetes/commit/357dbbc2b1dcb8826c61eb436273c18d83fe1565))
* update version to 0.4.1 ([2843b23](https://github.com/tibuntu/homeassistant-kubernetes/commit/2843b239d7a260ea2c44049dce3ad773da5014ea))

## [0.4.1](https://github.com/tibuntu/homeassistant-kubernetes/compare/v0.4.0...v0.4.1) (2025-09-03)


### Bug Fixes

* restore pyproject.toml after accidental replacement ([6202d2f](https://github.com/tibuntu/homeassistant-kubernetes/commit/6202d2f664e257eaaa42c12fbaad84e17f3c7d01))


### Other

* **ci:** do not longer ignore brands category within HACS action ([0086b94](https://github.com/tibuntu/homeassistant-kubernetes/commit/0086b94ee596e5e0ffa047ae6d2c713a3680326c))
* **deps:** update dependency python to 3.13 ([2019644](https://github.com/tibuntu/homeassistant-kubernetes/commit/20196449448be4ce0683f742c59946b7fd6b90f6))
* ensure pyproject.toml is updated during releases ([5ed2d62](https://github.com/tibuntu/homeassistant-kubernetes/commit/5ed2d62c7414a3c959911213fae568a810450f14))

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
