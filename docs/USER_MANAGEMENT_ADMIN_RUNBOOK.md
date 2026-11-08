# User Management — Administrative Runbook

## First Super Admin bootstrap

The first active `super_admin` cannot be created through the ordinary admin API: role assignment requires `roles:manage`, which is intentionally unavailable until a Super Admin exists. Use the offline, explicitly approved bootstrap command once, after the six-role migration has been applied to the intended database.

1. Confirm the exact target account with its owner and verify its account is active.
2. Obtain explicit approval for the database change and record the operator and reason.
3. Confirm the target account UUID and username independently; do not infer the target from account order.
4. Set `SUPER_ADMIN_BOOTSTRAP_APPROVED=YES` only in the approved execution environment.
5. Run the command with the exact account UUID and matching username:

```bash
SUPER_ADMIN_BOOTSTRAP_APPROVED=YES uv run --frozen --group infra python -m scripts.bootstrap_super_admin \
  --user-id <EXACT-USER-UUID> \
  --confirm-username <EXACT-USERNAME> \
  --operator <APPROVED-OPERATOR> \
  --reason <CHANGE-REASON> \
  --confirm-bootstrap
```

The command refuses to run without the environment approval flag, the explicit confirmation flag, an exact username match, an active non-deleted target account, the canonical Super Admin role row, and the absence of any active Super Admin. It replaces the selected account's role set with `super_admin`, revokes that account's existing sessions, and records an audit event with the operator and reason. It does not create a user or grant any additional permissions directly.

Do not run this command in an unapproved environment or against production without separate explicit production-change authorization. Do not execute it as part of routine deployments.

## Role changes

- Only a user with `roles:manage` can assign one of the six canonical roles or edit role permissions.
- Role changes revoke the target account's active sessions and create an audit event.
- Administrators cannot change their own role through the API.
- The last active Super Admin cannot be demoted, deactivated, suspended, archived, or locked through the account access policy.
- Use the in-app password recovery workflow for password changes; administrators never view passwords or password hashes.
