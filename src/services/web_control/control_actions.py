class ControlActions:
    def __init__(self, control_plane):
        self.control_plane = control_plane

    def pause_healing(self):
        # Prevent the AI from auto-optimizing further
        return getattr(self.control_plane, "pause_healing", lambda: {"status": "HEALING_PAUSED"})()

    def resume_healing(self):
        # Allow the AI to continue auto-optimizing
        return getattr(self.control_plane, "resume_healing", lambda: {"status": "HEALING_RESUMED"})()

    def rollback(self, version):
        # Revert the system logic to a previous stable state
        return getattr(self.control_plane, "rollback", lambda v: {"status": "ROLLED_BACK", "version": v})(version)
