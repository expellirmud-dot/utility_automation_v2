PERMISSIONS = {
    "admin": {
        "override_decision": True,
        "pause_healing": True,
        "rollback": True,
        "adjust_threshold": True
    },
    "operator": {
        "override_decision": True,
        "pause_healing": True,
        "rollback": False,
        "adjust_threshold": True
    },
    "viewer": {
        "override_decision": False,
        "pause_healing": False,
        "rollback": False,
        "adjust_threshold": False
    },
    "ai": {
        "override_decision": False,
        "pause_healing": False,
        "rollback": False,
        "adjust_threshold": False
    }
}
