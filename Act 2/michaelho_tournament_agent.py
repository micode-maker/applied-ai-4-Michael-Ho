#!/usr/bin/env python
"""
Tournament Agent: Forgiving Giant
Student: Michael Ho
Generated: 2026-09-28 17:23:51

Evolution Details:
- Generations: 100
- Final Fitness: 140.4
- Trained against: Gradual, Random (0.9), Pavlov, Random (0.5), Always Undercut...

Strategy: Cooperates and forgives often but undercuts those who mostly undercut
"""

from agents import Agent, INVEST, UNDERCUT
import random


class MichaelHoAgent(Agent):
    """
    Forgiving Giant

    Cooperates and forgives often but undercuts those who mostly undercut

    Evolved Genes: [0.921835644531324, 1.0, 0.756996881039874, 0.4189153353768606, 0.9984358600640448, 0.04220153235755486]
    """

    def __init__(self):
        # These genes were evolved through 100 generations
        self.genes = [0.921835644531324, 1.0, 0.756996881039874, 0.4189153353768606, 0.9984358600640448, 0.04220153235755486]

        # Required for tournament compatibility
        self.student_name = "Michael Ho"

        super().__init__(
            name="Forgiving Giant",
            description="Cooperates and forgives often but undercuts those who mostly undercut"
        )

    def choose_action(self) -> bool:
        """
        IMPROVED decision logic - AGGRESSIVE VERSION
        More likely to retaliate, less exploitable
        """        
        # Opening move (gene 0) controls initial cooperation
        if self.round_num == 0:
            return random.random() < self.genes[0]

        # If the opponent almost never cooperates, always undercut.
        memory_length = int(self.genes[3] * 10) + 1
        recent_history = self.history[-memory_length:]
        cooperation_rate = sum(recent_history) / len(recent_history)
        if cooperation_rate < self.genes[4] * 0.5:
            return UNDERCUT

        # Compare how often opponent invests after I invest vs after I undercut.
        if self.round_num >=10:
            after_my_invest = [self.history[i+1] for i in range(len(self.history)-1) 
                               if self.history[i] == INVEST]
            after_my_undercut = [self.history[i+1] for i in range(len(self.history)-1) 
                                 if self.history[i] == UNDERCUT]
            # Only judge once there enough examples of each
            if len(after_my_invest) >= 3 and len(after_my_undercut) >= 3:
                invest_rate_after_invest = sum(after_my_invest) / len(after_my_invest)
                invest_rate_after_undercut = sum(after_my_undercut) / len(after_my_undercut)
                responsiveness = invest_rate_after_invest - invest_rate_after_undercut
                if responsiveness > self.genes[5] * 0.5:
                    return UNDERCUT

        # React to opponent's last move (genes 1 and 2)
        if self.history[-1] == INVEST:
            return random.random() < self.genes[1] # reciprocate
        else:
            return random.random() < self.genes[2] # forgive



# Convenience function for tournament loading
def get_agent():
    """Return an instance of this agent for tournament use"""
    return MichaelHoAgent()


if __name__ == "__main__":
    # Test that the agent can be instantiated
    agent = get_agent()
    print(f"✅ Agent loaded successfully: {agent.name}")
    print(f"   Genes: {agent.genes}")
    print(f"   Description: {agent.description}")
