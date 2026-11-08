"""One-time, explicitly approved bootstrap for the first active Super Admin.

This command is intentionally separate from the public API. It must never be
run against a database without explicit operator approval.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.modules.authentication.roles import RoleName
from database.models.audit import AuditLog
from database.models.identity import Role, User, UserSession
from database.session import SessionLocal


async def bootstrap_super_admin(
    session: AsyncSession,
    *,
    user_id: UUID,
    confirmed_username: str,
    operator: str,
    reason: str,
) -> dict[str, object]:
    """Assign the first Super Admin to one explicitly confirmed active account."""
    user_result = await session.execute(
        select(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
        .options(selectinload(User.roles))
        .with_for_update()
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise ValueError("The selected active account does not exist.")
    if not user.username or not confirmed_username.strip():
        raise ValueError("The selected account must have a non-empty username confirmation.")
    if user.username.casefold() != confirmed_username.strip().casefold():
        raise ValueError("The confirmation username does not match the selected account.")
    if not operator.strip() or len(reason.strip()) < 5:
        raise ValueError("An operator name and a reason of at least five characters are required.")
    if str(user.status).upper() != "ACTIVE":
        raise ValueError("Only an active account can receive the initial Super Admin role.")

    role_result = await session.execute(
        select(Role)
        .where(Role.name == RoleName.SUPER_ADMIN.value)
        .with_for_update()
    )
    super_admin_role = role_result.scalar_one_or_none()
    if super_admin_role is None:
        raise RuntimeError("The six-role RBAC migration must be applied before bootstrap.")

    existing_result = await session.execute(
        select(func.count(User.id)).where(
            func.upper(User.status) == "ACTIVE",
            User.deleted_at.is_(None),
            User.roles.any(Role.name == RoleName.SUPER_ADMIN.value),
        )
    )
    if (existing_result.scalar_one() or 0) > 0:
        raise ValueError("An active Super Admin already exists; bootstrap is no longer available.")

    before_roles = sorted(role.name for role in user.roles)
    user.roles = [super_admin_role]
    now = datetime.now(timezone.utc)
    revoked_result = await session.execute(
        update(UserSession)
        .where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
        .values(revoked_at=now, revoked_reason="initial_super_admin_bootstrap")
    )
    revoked_count = max(0, revoked_result.rowcount or 0)
    session.add(
        AuditLog(
            actor_id=None,
            action="user.role_bootstrapped",
            resource_type="user",
            resource_id=user.id,
            description=f"Initial Super Admin role bootstrapped for '{user.username}'.",
            event_metadata={
                "operator": operator.strip(),
                "reason": reason.strip(),
                "before_roles": before_roles,
                "after_roles": [RoleName.SUPER_ADMIN.value],
                "sessions_revoked": revoked_count,
            },
            created_at=now,
        )
    )
    await session.commit()
    return {
        "user_id": user.id,
        "username": user.username,
        "before_roles": before_roles,
        "after_roles": [RoleName.SUPER_ADMIN.value],
        "sessions_revoked": revoked_count,
    }


async def _run(args: argparse.Namespace) -> None:
    if os.getenv("SUPER_ADMIN_BOOTSTRAP_APPROVED") != "YES":
        raise SystemExit("Set SUPER_ADMIN_BOOTSTRAP_APPROVED=YES only after explicit change approval.")
    if not args.confirm_bootstrap:
        raise SystemExit("Pass --confirm-bootstrap to confirm this one-time privileged operation.")
    async with SessionLocal() as session:
        result = await bootstrap_super_admin(
            session,
            user_id=args.user_id,
            confirmed_username=args.confirm_username,
            operator=args.operator,
            reason=args.reason,
        )
    print(
        "Initial Super Admin assigned: "
        f"{result['username']} ({result['user_id']}); "
        f"revoked sessions: {result['sessions_revoked']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-id", required=True, type=UUID)
    parser.add_argument("--confirm-username", required=True)
    parser.add_argument("--operator", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--confirm-bootstrap", action="store_true")
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
