class HealingBudgetController:
    def __init__(self):
        self.budget = 3  # max heals per cycle

    def allow(self):
        if self.budget <= 0:
            return False

        self.budget -= 1
        return True
