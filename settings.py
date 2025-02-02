# -*- coding: utf-8 -*-
"""Functions for user settings."""

__copyright__ = 'Copyright (c) 2021, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

from genquery import Query

from util import *

__all__ = ['api_settings_load',
           'api_settings_save']

# Allowed settings should be synchronised with policies and portal:
# Policies: uuUserPolicyCanUserModify in yoda-ruleset/uuGroupPolicyChecks.r
# Portal: settings in yoda-portal/user/user.py
USER_SETTINGS = {"mail_notifications": {"default": "OFF", "values": ["OFF", "IMMEDIATE", "DAILY", "WEEKLY"]}}

SETTINGS_KEY = constants.UUORGMETADATAPREFIX + "settings_"


def load(ctx, setting, username=None):
    """Load user setting.

    :param ctx:      Combined type of a callback and rei struct
    :param setting:  Name of setting to retrieve
    :param username: Optional username to retrieve setting from

    :returns: User setting or setting default
    """
    if username is None:
        username = user.name(ctx)

    settings = {a.replace(SETTINGS_KEY, ""): v for a, v
                in Query(ctx, "META_USER_ATTR_NAME, META_USER_ATTR_VALUE",
                              "USER_NAME = '{}' AND USER_TYPE != 'rodsgroup' AND META_USER_ATTR_NAME like '{}%%'".format(username, SETTINGS_KEY))}

    if setting in settings:
        return settings[setting]
    else:
        return USER_SETTINGS[setting]["default"]


@api.make()
def api_settings_load(ctx):
    """Load user settings.

    :param ctx: Combined type of a callback and rei struct

    :returns: Dict with all settings
    """
    settings = {a.replace(SETTINGS_KEY, ""): v for a, v
                in Query(ctx, "META_USER_ATTR_NAME, META_USER_ATTR_VALUE",
                              "USER_NAME = '{}' AND USER_TYPE != 'rodsgroup' AND META_USER_ATTR_NAME like '{}%%'".format(user.name(ctx), SETTINGS_KEY))}

    # Add defaults for missing settings.
    for setting in USER_SETTINGS:
        if setting not in settings:
            settings[setting] = USER_SETTINGS[setting]["default"]

    return settings


@api.make()
def api_settings_save(ctx, settings):
    """Save user settings.

    :param ctx:      Combined type of a callback and rei struct
    :param settings: Dict with settings to be saved

    :returns: API status
    """
    for a, v in settings.items():
        if a in USER_SETTINGS and v in USER_SETTINGS[a]["values"]:
            try:
                ctx.uuUserModify(user.full_name(ctx), "{}{}".format(SETTINGS_KEY, a), str(v), '', '')
            except Exception:
                return api.Error('internal', 'Saving settings failed. If the problem persists after a few tries, please contact a Yoda administrator.')
    return api.Result.ok()
