class RuleMatcher:

    def match(self,
              rule,
              role,
              action,
              system_state):

        if rule.action != action:
            return False

        if rule.required_role:
            if rule.required_role != role:
                return False

        if rule.required_state:
            if rule.required_state != system_state:
                return False

        return True
