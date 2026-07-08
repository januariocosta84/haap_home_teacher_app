"""
Audit logging helpers.

Usage:
    from core.audit import log_action

    log_action(
        request=request,
        action='create',
        module='Users',
        description='Created user John Doe',
        record_id=str(user.id),
        record_name=user.get_full_name(),
    )

All exceptions are caught internally so a logging failure never breaks the
main application flow.
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def get_client_ip(request) -> Optional[str]:
    """Return the real client IP, respecting common proxy headers."""
    for header in ('HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP', 'REMOTE_ADDR'):
        val = request.META.get(header)
        if val:
            return val.split(',')[0].strip()
    return None


def parse_user_agent(ua: str):
    """Return (browser, os_info) from a User-Agent string."""
    lo = ua.lower()

    if 'edg/' in lo or 'edge/' in lo:
        browser = 'Microsoft Edge'
    elif 'opr/' in lo or 'opera' in lo:
        browser = 'Opera'
    elif 'chrome/' in lo and 'chromium' not in lo:
        browser = 'Google Chrome'
    elif 'firefox/' in lo:
        browser = 'Mozilla Firefox'
    elif 'safari/' in lo and 'chrome' not in lo:
        browser = 'Safari'
    elif 'msie' in lo or 'trident/' in lo:
        browser = 'Internet Explorer'
    elif 'curl' in lo:
        browser = 'cURL'
    else:
        browser = 'Unknown'

    if 'iphone' in lo:
        os_info = 'iOS (iPhone)'
    elif 'ipad' in lo:
        os_info = 'iOS (iPad)'
    elif 'android' in lo:
        os_info = 'Android'
    elif 'windows nt 10' in lo:
        os_info = 'Windows 10/11'
    elif 'windows' in lo:
        os_info = 'Windows'
    elif 'macintosh' in lo or 'mac os x' in lo:
        os_info = 'macOS'
    elif 'linux' in lo:
        os_info = 'Linux'
    else:
        os_info = 'Unknown'

    return browser, os_info


def log_action(
    request=None,
    user=None,
    action: str = 'other',
    module: str = '',
    description: str = '',
    record_id: str = '',
    record_name: str = '',
    previous_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    status: str = 'success',
    username: str = '',
) -> None:
    """
    Create one AuditLog record.  Never raises — failures are logged only.
    """
    try:
        from core.models import AuditLog  # local import avoids circular deps

        ip = None
        ua_str = ''
        browser = ''
        os_info = ''

        if request is not None:
            ip = get_client_ip(request)
            ua_str = request.META.get('HTTP_USER_AGENT', '')
            browser, os_info = parse_user_agent(ua_str)
            if user is None and hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user

        if not username and user:
            username = (
                getattr(user, 'get_full_name', lambda: '')() or
                getattr(user, 'whatsapp_number', '') or
                getattr(user, 'username', '') or
                str(user)
            )

        AuditLog.objects.create(
            user=user if (user and user.pk) else None,
            username=username,
            action=action,
            module=module,
            description=description,
            record_id=str(record_id),
            record_name=str(record_name),
            previous_value=previous_value,
            new_value=new_value,
            ip_address=ip,
            user_agent=ua_str[:1000],
            browser=browser,
            os_info=os_info,
            status=status,
        )
    except Exception:
        logger.exception('AuditLog.create failed (action=%s)', action)
