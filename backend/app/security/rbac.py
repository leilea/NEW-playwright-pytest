from fastapi import HTTPException
from sqlalchemy import select
from app.models.auth import User, ResourceACL


async def assert_can(user: User, action: str, resource: tuple[str, str | int], db) -> None:
    role_names = {r.role.name for r in user.roles}
    if "admin" in role_names:
        return
    rt, rid = resource
    q = select(ResourceACL).where(
        ResourceACL.resource_type == rt,
        ResourceACL.resource_id == str(rid),
        ResourceACL.principal_id.in_([str(user.id), *role_names]),
        ResourceACL.permission == action,
    )
    res = (await db.execute(q)).scalars().first()
    if not res and action in ("read", "write") and "editor" in role_names:
        return
    if not res:
        raise HTTPException(403, f"forbidden: {action} {rt}:{rid}")
