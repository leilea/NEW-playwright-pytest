"""套件相关业务编排。

未来 API 对应：
- load_suite_list_with_count → GET   /api/suites
- create_suite_form_data     → POST  /api/suites
- update_suite_form_data     → PATCH /api/suites/:id
- delete_suite_with_confirm  → DELETE /api/suites/:id
"""
from typing import List, Tuple

from streamlit_app.services import suite_service
from streamlit_app.services.suite_service import SuiteDuplicateError


def load_suite_list_with_count() -> List[dict]:
    """直接转发 service 层结果（含 case_count 字段）。"""
    return suite_service.list_suites()


def create_suite_form_data(name: str, version: str, created_by: str) -> Tuple[bool, str, dict | None]:
    """新增套件：成功 → (True, "", suite)；失败 → (False, msg, None)。"""
    try:
        suite = suite_service.create_suite(name, version, created_by=created_by)
        return True, "", suite
    except SuiteDuplicateError as e:
        return False, str(e), None
    except ValueError as e:
        return False, str(e), None


def update_suite_form_data(suite_id: str, name: str, version: str) -> Tuple[bool, str, dict | None]:
    """修改套件。"""
    try:
        suite = suite_service.update_suite(suite_id, name, version)
        if suite is None:
            return False, "套件不存在", None
        return True, "", suite
    except SuiteDuplicateError as e:
        return False, str(e), None
    except ValueError as e:
        return False, str(e), None


def delete_suite_with_confirm(suite_id: str) -> Tuple[bool, str]:
    """删除套件（仅当为空）。返回 (success, msg)。"""
    return suite_service.delete_suite_if_empty(suite_id)
