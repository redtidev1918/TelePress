# 自动化发版

**Language / 语言:** [中文](releasing.md) · [English](../en/development/releasing.md)

TelePress 使用 release-please + ReleaseGraph 自动发版：

```text
Conventional commits
        ↓
Release Please pull request
        ↓ maintainer review and merge
Git tag + GitHub Release
        ↓
Build and metadata verification
        ↓
PyPI Trusted Publishing + GitHub assets
        ↓
post-release-docs（自动刷新下载页 + 重建 Pages）
```

## 一次发版流程

1. 用 Conventional Commits 合入 `master`。
2. Release workflow 创建/更新 release PR。
3. 审查版本号与 `CHANGELOG.md`，合并 release PR。
4. Release Please 创建 `vX.Y.Z` tag 与 GitHub Release。
5. workflow 构建 wheel + sdist、验证元数据、发布 PyPI。
6. `post-release-docs` 刷新 `docs/download.md` / `docs/en/download.md`，并重建 Pages。

不需要本地 `git tag` 或 `twine upload`。

## 一次性仓库设置

- GitHub Actions 允许创建 PR 与请求写权限。
- 创建名为 `pypi` 的 GitHub environment。
- 在 PyPI 配置 GitHub Trusted Publisher：owner `redtidev1918`、repo `telepress`、
  workflow `release.yml`、environment `pypi`。
- 可选 `RELEASE_PLEASE_TOKEN` 保证 release PR 的 CI 正常触发。

## 版本策略

| Commit | 版本效果 |
| --- | --- |
| `fix:` | patch（`0.14.0 → 0.14.1`） |
| `feat:` | minor（`0.14.x → 0.15.0`） |
| `feat!:` / `BREAKING CHANGE:` | 1.0 前 minor，1.0 后 major |
| `docs:` / `test:` / `chore:` | 不单独发版 |

异常版本可加 `Release-As:` footer。

## 失败恢复

- 合并前 CI 失败：修复 PR，等待更新。
- Release 已创建但 build/PyPI 失败：修复配置后重跑失败 job。
- PyPI 版本不可变：不要删除复用已发布版本，发新的 patch。
- 不要手动移动或覆盖 release-please 生成的 tag。

## 自动化文件

- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `.github/workflows/update-download-page.yml`
- `.github/workflows/static.yml`
- `release-please-config.json`、`.release-please-manifest.json`
