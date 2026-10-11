# Personal fork maintenance

This document describes the personal fork's branches, not an upstream release policy.

## Branches

- `main`: an unmodified mirror of `NousResearch/hermes-agent:main`. Sync it with
  `gh repo sync toolazytoname/hermes-agent --branch main --source NousResearch/hermes-agent`.
- `develop_air`: the integration branch for personal fixes and upstream updates.
  Its initial upstream baseline is `7bc05085f09ee9bfa9cecaaa3cf44758bdff96a6`
  (2026-10-11). This is a source candidate, not proof of a deployed Air upgrade.
- `feat/codex-progress-aware-goals`: the preserved historical PR source; do not
  force-push it when updating the integration branch.
- `feat/codex-native-goals-refreshed`: the clean Codex-only replacement PR source
  for upstream PR #136620. It starts from official `97a9ae8e` and replaces the
  closed #134260 and #134539 without deleting their source branches.
- `air/deployed-snapshot-20261011`: the archived source actually running on Air
  before the upgrade. It is based on an older upstream version and is not the
  recommended development baseline. This archive contains source and tests only.

## Normal workflow

1. Create a `fix/…` or `feat/…` branch for one bounded change. Keep its tests with it.
2. Check for an existing upstream fix or PR before implementing or opening another PR.
3. Run the relevant tests through `scripts/run_tests.sh` in an isolated test home,
   and run `python scripts/check`. Do not weaken assertions to hide failures.
4. Commit and push the topic branch. Integrate it into `develop_air` after review.
5. Submit focused upstream PRs from topic branches, not the whole integration branch.
   Keep the existing Goal PR separate from Feishu attachment and cold-start fixes.

## Upstream refresh and deployment

Fetch upstream and merge its selected revision into `develop_air` without rewriting
published branch history. Record the selected SHA and the verification results.
Rebuild the test environment from the updated lock file when dependencies change.
Refresh routinely and before starting significant new work; do not chase every
upstream commit during a single verification run.

A source update is not a production deployment. Before switching the Air runtime:

- pause active work and confirm the gateway is idle;
- back up source, deployment metadata and private state separately;
- preserve session routing, native Goal identity, progress and token accounting;
- check Intel macOS compatibility and run isolated gateway/Codex integration tests;
- verify real Feishu ingress and delivery, with no business or device side effects;
- retain a rollback revision and environment; record the actually deployed SHA.

Do not resume a user-paused Goal as a side effect of an upgrade. Credentials,
private model settings, personal SOUL/config files, session databases and Goal
ledgers must never be committed to this public fork.

## Latest verified refresh (2026-10-11)

`develop_air` merged upstream `97a9ae8ee55d31bebce49f1fb6b5ef775323976a`
without conflict or published-history rewriting. Integration regression: 14 files,
138 passed; all 11 source checks passed. The Codex-only replacement PR separately
passed 71 files / 877 tests, with one Linux-only skip on macOS, and all 11 source
checks. GitHub reported it mergeable without conflicts; upstream CI and maintainer
approval are separate from this result. No production runtime upgrade is implied.
