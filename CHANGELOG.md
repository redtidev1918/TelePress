# Changelog

All notable changes to TelePress are documented in this file. The project uses
[Semantic Versioning](https://semver.org/) and the changelog is maintained by
Release Please from Conventional Commits.

## [0.14.1](https://github.com/redtidev1918/telepress/compare/v0.14.0...v0.14.1) (2026-09-19)


### Documentation

* refresh download page (manual) ([cfa612a](https://github.com/redtidev1918/telepress/commit/cfa612a2372a605d5ea576fcb507f9cfe689b03f))

## [0.14.0](https://github.com/redtidev1918/telepress/compare/v0.13.1...v0.14.0) (2026-09-19)


### Features

* **api:** decouple media proxy from Pixiv, opt-in remote gallery media ([#47](https://github.com/redtidev1918/telepress/issues/47)) ([f6a6a51](https://github.com/redtidev1918/telepress/commit/f6a6a51aec665bd9e9baef355fba59d6e9da9c58))

## [0.13.1](https://github.com/redtidev1918/telepress/compare/v0.13.0...v0.13.1) (2026-09-19)


### Reverts

* **publish:** drop remote MediaReference fetch for /publish/gallery ([#45](https://github.com/redtidev1918/telepress/issues/45)) ([f8ac147](https://github.com/redtidev1918/telepress/commit/f8ac147ec1c5f8b86f63be23de89a1f2078d86ae))

## [0.13.0](https://github.com/redtidev1918/telepress/compare/v0.12.1...v0.13.0) (2026-09-19)


### Features

* **publish:** accept remote MediaReference[] manifest for gallery ([#42](https://github.com/redtidev1918/telepress/issues/42)) ([e93cf77](https://github.com/redtidev1918/telepress/commit/e93cf772aa98e10972fcca4163db43ddb7ad8624))

## [0.12.1](https://github.com/redtidev1918/telepress/compare/v0.12.0...v0.12.1) (2026-09-19)


### Bug Fixes

* **rich-novel:** expose assetId in RichNovelAsset response model ([#40](https://github.com/redtidev1918/telepress/issues/40)) ([66e58a9](https://github.com/redtidev1918/telepress/commit/66e58a9407e2d2f5bccec6c42b18dc7c2a43dfe2))

## [0.12.0](https://github.com/redtidev1918/telepress/compare/v0.11.0...v0.12.0) (2026-09-19)


### Features

* **rich-novel:** accept MediaReference manifest (assetId/sourceUrl) ([#38](https://github.com/redtidev1918/telepress/issues/38)) ([051a449](https://github.com/redtidev1918/telepress/commit/051a44904143eaeed0ee49d5a9b1b4b3fb99d7d3))

## [0.11.0](https://github.com/redtidev1918/telepress/compare/v0.10.0...v0.11.0) (2026-09-19)


### Features

* **rich-novel:** Pixiv proxy rewrite via optional manifest ([#37](https://github.com/redtidev1918/telepress/issues/37)) ([baa5309](https://github.com/redtidev1918/telepress/commit/baa5309a61d8d5b317c0c71eb51ded2b2da13ac6))


### Documentation

* **agent:** add AGENTS.md for the publishing plane boundary ([#35](https://github.com/redtidev1918/telepress/issues/35)) ([1a8f1b0](https://github.com/redtidev1918/telepress/commit/1a8f1b0a284a59d2a303dc70cb2b0ed7b5e87963))
* **agent:** point telepress AGENTS.md at cross-repo ecosystem authority ([76e97d5](https://github.com/redtidev1918/telepress/commit/76e97d56e3e6d6ce7a0d337a862308b228e6974b))
* **agent:** reference CONTRACT.md and fix Telegraph spelling ([53a14ca](https://github.com/redtidev1918/telepress/commit/53a14ca80e4a3ae5fed9f892cdcf9dad6faae44b))

## [0.10.0](https://github.com/redtidev1918/telepress/compare/v0.9.0...v0.10.0) (2026-09-17)


### Features

* **publish:** rich-novel HTTP endpoint with asset mapping (RFC Phase 4) ([e9fea03b3a2884fdcd855f06e36202a16ac6bc52](https://github.com/redtidev1918/telepress/commit/e9fea03b3a2884fdcd855f06e36202a16ac6bc52))

## [0.9.0](https://github.com/redtidev1918/telepress/compare/v0.8.1...v0.9.0) (2026-09-17)


### Features

* **publish:** rich novel pipeline (local image upload + Telegraph nodes) ([320afef](https://github.com/redtidev1918/telepress/commit/320afef4896a06f5c333675d93a6e9a62625aff8))
* **publish:** rich NovelMarkdownRenderer for Telegraph nodes (RFC Phase 2) ([9d99d90](https://github.com/redtidev1918/telepress/commit/9d99d904f32f163d1d0e7da5d179aa43c608cdb8))
* **publish:** upload and inline local markdown images (RFC Phase 1) ([5ef27d9](https://github.com/redtidev1918/telepress/commit/5ef27d97d8c6e4628cf4489a8cb89e0e4c850701))

## [0.8.1](https://github.com/redtidev1918/telepress/compare/v0.8.0...v0.8.1) (2026-09-16)


### Bug Fixes

* match should_publish_pypi output and dispatch dry_run check ([446711b](https://github.com/redtidev1918/telepress/commit/446711bab47714cd5b3ef196411a9c5d09462cbc))

## [0.8.0](https://github.com/redtidev1918/telepress/compare/v0.7.0...v0.8.0) (2026-09-16)


### Features

* expand hosting providers and caller-owned PyPI publishing ([#26](https://github.com/redtidev1918/telepress/issues/26)) ([d141bce](https://github.com/redtidev1918/telepress/commit/d141bce489e0f632125b9464516ca27548dd7870))


### Bug Fixes

* correct repair workflow_dispatch input comparison ([bd75fba](https://github.com/redtidev1918/telepress/commit/bd75fbab599da19efdfcda7a6c859e12158e9fc8))
* stage only wheel and sdist for PyPI upload ([4cced44](https://github.com/redtidev1918/telepress/commit/4cced44b1f23553b2fbae9d1167a52ee9cf5b0f0))

## [0.7.0](https://github.com/redtidev1918/telepress/compare/v0.6.2...v0.7.0) (2026-09-16)


### Features

* add native Catbox upload support ([#24](https://github.com/redtidev1918/telepress/issues/24)) ([ca1b00c](https://github.com/redtidev1918/telepress/commit/ca1b00c6bca9ee2454a3893116be2671b98b5a15))

## [0.6.2](https://github.com/redtidev1918/telepress/compare/v0.6.1...v0.6.2) (2026-09-12)


### Documentation

* 中文设为默认语言，统一双语命名与侧边栏，补齐下载页与英文文档 ([#20](https://github.com/redtidev1918/telepress/issues/20)) ([8221934](https://github.com/redtidev1918/telepress/commit/82219346f9aebe08f5edac0d20573b619bb80570))
* 显式声明 CDN 壳站点的导航例外 ([#22](https://github.com/redtidev1918/telepress/issues/22)) ([16617e9](https://github.com/redtidev1918/telepress/commit/16617e9a2d0b8f263a12f327059c3e994ff6fb86))
* 英文发版文档中的中文句子改为英文 ([74e9a59](https://github.com/redtidev1918/telepress/commit/74e9a59c31bc0df0f085feb85c206116401f2f21))

## [0.6.1](https://github.com/redtidev1918/telepress/compare/v0.6.0...v0.6.1) (2026-09-08)


### Documentation

* publish documentation site ([c5a88a6](https://github.com/redtidev1918/telepress/commit/c5a88a6f6ff4d05f2e2a3ff83af666d34af7ec97))

## [0.6.0](https://github.com/redtidev1918/telepress/compare/v0.5.0...v0.6.0) (2026-09-07)


### Features

* **server:** /publish/* 可选请求级 API key 鉴权（Bearer / X-TelePress-Key） ([4078e61](https://github.com/redtidev1918/telepress/commit/4078e613cc43a8d66eab2aece848b28415939af1))

## [0.5.0](https://github.com/redtidev1918/telepress/compare/v0.4.0...v0.5.0) (2026-08-30)


### Features

* **core:** support optional footer nodes in gallery publishing ([4efcf12](https://github.com/redtidev1918/telepress/commit/4efcf12df60a9fdb49ebb6e104fe28d3eddb6aca))
* **server:** add /publish/gallery endpoint for multi-image galleries ([545e0fb](https://github.com/redtidev1918/telepress/commit/545e0fbe08413e84a5a33f5629078e96f7722675))


### Documentation

* document /publish/gallery REST endpoint ([cd03d83](https://github.com/redtidev1918/telepress/commit/cd03d83d0883a0dd671cd9352d70b3ba320f43d2))

## [0.4.0](https://github.com/redtidev1918/telepress/compare/v0.3.5...v0.4.0) (2026-08-27)


### Features

* defer image host initialization until first upload use ([44445e1](https://github.com/redtidev1918/telepress/commit/44445e1784a513fc0811b9d73e9937a30f12871c))
* keep API server blocking work off the event loop ([ee43828](https://github.com/redtidev1918/telepress/commit/ee43828fdda29e49f663a87d9abdd7e3c897eb5b))


### Bug Fixes

* block zip-slip sibling paths and harden compression search ([d5d4661](https://github.com/redtidev1918/telepress/commit/d5d4661d119fab9a516d3bae7796685dc0b8f806))
* raise a clear error when telepress-server lacks the api extra ([08b6fac](https://github.com/redtidev1918/telepress/commit/08b6facf3d0acb6a4cb6e29d4038d5bfa105006a))


### Documentation

* rewrite READMEs and add contribution and release guides ([b433122](https://github.com/redtidev1918/telepress/commit/b4331220f8868acc215f2680f7fd547998b831bc))

## [0.3.5] - 2025-12-09

### Added

- Added `--api-url` support for Telegraph-compatible API endpoints.

### Changed

- Made image-upload worker count configurable.
- Improved external image-host configuration and documentation.

## [0.3.0] - 2025-12-08

### Added

- Added Rclone batch uploads and S3-compatible storage support.
- Added automatic image compression and concurrent batch uploads.
- Added plain-text chapter detection and automatic pagination.
- Added configuration checks, progress output, and comprehensive tests.

## [0.1.0] - 2025-12-07

### Added

- Initial Markdown and plain-text publishing support for Telegraph.
