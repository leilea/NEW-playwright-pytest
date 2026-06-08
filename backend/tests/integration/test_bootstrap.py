import pytest


@pytest.mark.asyncio
async def test_bootstrap_creates_admin_when_users_empty(db_session):
    from sqlalchemy import select, func

    from app.bootstrap import bootstrap_admin
    from app.models.auth import User, Role, UserRole

    await db_session.execute(
        UserRole.__table__.delete()
    )
    await db_session.execute(
        User.__table__.delete()
    )
    await db_session.execute(
        Role.__table__.delete()
    )
    await db_session.commit()

    await bootstrap_admin()

    user = (
        await db_session.execute(
            select(User).where(User.email == "admin@local")
        )
    ).scalar_one_or_none()
    assert user is not None
    assert user.is_active

    role = (
        await db_session.execute(
            select(Role).where(Role.name == "admin")
        )
    ).scalar_one_or_none()
    assert role is not None

    user_role = (
        await db_session.execute(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
            )
        )
    ).scalar_one_or_none()
    assert user_role is not None

    editor_role = (
        await db_session.execute(
            select(Role).where(Role.name == "editor")
        )
    ).scalar_one_or_none()
    assert editor_role is not None

    viewer_role = (
        await db_session.execute(
            select(Role).where(Role.name == "viewer")
        )
    ).scalar_one_or_none()
    assert viewer_role is not None


@pytest.mark.asyncio
async def test_bootstrap_idempotent(db_session):
    from app.bootstrap import bootstrap_admin
    from app.models.auth import User

    await bootstrap_admin()

    from sqlalchemy import select, func
    count_before = (
        await db_session.scalar(select(func.count()).select_from(User))
    )

    await bootstrap_admin()
    count_after = (
        await db_session.scalar(select(func.count()).select_from(User))
    )
    assert count_before == count_after
