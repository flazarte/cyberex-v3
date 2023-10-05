import functools

from flask import abort

from CTFd.utils import get_config
from CTFd.utils.modes import TEAMS_MODE, USERS_MODE
from CTFd.plugins.custom.utils import ctk_users_mode, ctk_teams_mode


def require_team_mode(f):
    @functools.wraps(f)
    def _require_team_mode(*args, **kwargs):
        if ctk_users_mode():
            abort(404)
        return f(*args, **kwargs)

    return _require_team_mode


def require_user_mode(f):
    @functools.wraps(f)
    def _require_user_mode(*args, **kwargs):
        if ctk_teams_mode():
            abort(404)
        return f(*args, **kwargs)

    return _require_user_mode