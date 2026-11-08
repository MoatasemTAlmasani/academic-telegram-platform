# Unified Branch and Single-Deployment Release Strategy

## Goal

Develop all platform modules on one long-lived integration branch and avoid consuming Vercel deployment quota during implementation. Release only one reviewed production deployment after the agreed modules and acceptance checks are complete.

## Branch policy

- Unified implementation branch: `feature/admin-dashboard-enhancements`.
- All module work, fixes, tests, and documentation remain on this branch; do not create a branch per module.
- Do not push this branch during normal implementation. Vercel Git integration can create Preview deployments for pushes to non-production branches, consuming deployment quota.
- Do not create module-specific pull requests or intermediate release branches.
- Keep the production branch (`main`) unchanged until release approval.

## Single-release procedure

1. Finish the agreed modules and acceptance criteria on the unified branch.
2. Run the complete test suite, type checks, production build, security checks, and available isolated integration/E2E tests.
3. Review the complete diff, verify no secrets or local artifacts, and confirm database/migration safety.
4. Prepare one release candidate commit on the unified branch only after explicit approval to commit.
5. At release time, merge the unified branch into the production branch locally and push only the production branch once, after explicit approval to push. Do not push the feature branch first.
6. Allow the configured Vercel Git integration to create the single production deployment from that production-branch update. Do not separately run `vercel deploy`, `vercel --prod`, promote, or create a preview deployment for the same release.
7. Verify the resulting deployment URL, commit SHA, readiness, aliases, and smoke tests. Do not redeploy to fix a failed release without reviewing quota and obtaining approval.

## Quota safeguards

- No deployment, preview, promotion, rollback, or Vercel configuration changes during development.
- No GitHub push, PR creation, or merge until the release gate is met and the user explicitly authorizes it.
- If a deployment is needed for testing before release, stop and ask first; prefer local/isolated test environments.
- The single-deployment target depends on Vercel being configured to deploy production from `main` and on no other automation independently creating deployments. Verify those settings read-only before the release; do not change them without approval.

## Current state

- Unified working branch: `feature/admin-dashboard-enhancements`.
- Production branch expected from the repository workflow: `main` (must be verified read-only before release).
- No push, merge, deployment, promotion, rollback, or Vercel project setting change is authorized by this document.
