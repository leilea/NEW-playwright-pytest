def test_models_import():
    from app.models.auth import User, Role, UserRole, ResourceACL
    from app.models.catalog import Suite, Case
    from app.models.runtime import Run, Schedule
    from app.models.audit import AuditEvent
    assert all([User, Role, UserRole, ResourceACL, Suite, Case, Run, Schedule, AuditEvent])
