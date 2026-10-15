#!/usr/bin/env python3
"""
Skeleton Optimization Agent - Template for students to implement optimization algorithms

IMPORTANT: This is NOT an RL agent - it's a template for 
students to implement their own optimization algorithms (greedy, Hungarian, etc.)

This agent currently makes terrible decisions:
- Random staffing decisions
- No layout optimization 
- Ignores order priorities
- No intelligent assignment logic

Students should replace the naive methods with proper optimization algorithms.
"""

import numpy as np
from typing import Dict, Optional
from .standardized_agents import BaselineAgent

class SkeletonOptimizationAgent(BaselineAgent):
    """
    Template for students to implement their own optimization algorithms.
    
    Students should replace the naive methods with:
    - Economic models for staffing decisions
    - Hungarian algorithm for order assignment  
    - Greedy search for layout optimization
    - Multi-objective optimization techniques
    """
    
    def __init__(self, env):
        super().__init__(env)
        self.name = "StudentOptimization"
        
        # Enable unlimited hiring for true economic optimization
        self.env._unlimited_hiring = True
        
        # Students can add their own state tracking here
        self.performance_metrics = []
        self.decision_history = []
        
        # Students can add algorithm parameters here
        # Example: Hungarian algorithm matrices, greedy search parameters, etc.
        self.staffing_parameters = {
            'hire_threshold_ratio': 3.0,
            'fire_threshold_ratio': 2.0,
            'profit_threshold': 0
        }
        
        # Students can implement adaptive parameters that change based on performance
        self.adaptive_optimization_enabled = False
        
    def reset(self):
        """Reset agent state - students should expand this"""
        self.action_history = []
        self.reward_history = []
        self.layout_metrics = []          # Step 4: per-episode layout tracking
        self.frequency_swap_count = 0     # Phase 1 swaps this episode
        self.cooccurrence_swap_count = 0  # Phase 2 swaps this episode
        # TODO: Reset any neural network states, replay buffers, etc.
    
    def get_action(self, observation: Dict) -> Dict:
        """
        Generate action based on observation.
        Current implementation is intentionally terrible - students should improve!
        """
        
        # Extract basic info from observation
        current_timestep = observation['time'][0]
        # DEBUG (Step 5.2)
        # if current_timestep % 100 == 0:
        #     managers = sum(e.is_manager for e in self.env.employees)
        #     print(f"[t={current_timestep}] employees={len(self.env.employees)} "
        #           f"managers={managers} queue={len(self.env.order_queue.orders)} "
        #           f"profit={self.env.cumulative_profit:.0f} "
        #           f"efficiency={self._calculate_layout_efficiency():.3f}")
        # Track layout performance every 100 steps
        if observation['time'][0] % 100 == 0:
            self.track_layout_performance()
        financial_state = observation['financial']  # [profit, revenue, costs, burn_rate]
        queue_info = observation['order_queue']
        employee_info = observation['employees']
        
        action = {
            'staffing_action': self._get_naive_staffing_action(financial_state, employee_info),
            'layout_swap': self._get_naive_layout_action(current_timestep),
            'order_assignments': self._get_naive_order_assignments(queue_info, employee_info)
        }
        
        # TODO: Students should implement proper action recording for optimization
        self.action_history.append(action.copy())
        
        return action
    
    def _get_naive_staffing_action(self, financial_state, employee_info) -> int:
        """
        WEEK 2 STEP 1: Staffing decisions - students should improve this!
        
        Current problems:
        - Ignores queue length and workload
        - Random decisions regardless of profit
        - No consideration of employee efficiency
        """
        
        # TODO WEEK 2 STEP 1: Students should implement intelligent staffing logic
        # Current approach: Make random decisions based on "vibes"
        
        current_profit = financial_state[0]
        num_employees = np.sum(employee_info[:, 0] > 0)  # Count active employees
        
        # Terrible logic: Random decisions with slight bias
        # BUT: Hire managers more frequently so layout optimization can work
        has_manager = np.any(employee_info[:, 5] == 1)  # Check if we have a manager
        
        if np.random.random() < 0.3:  # 30% chance to hire
            if num_employees < 20:  # Don't go completely overboard
                return 1  # Hire worker
        elif np.random.random() < 0.1:  # 10% chance to fire
            if num_employees > 1:  # Don't fire everyone
                return 2  # Fire worker
        elif np.random.random() < 0.2:  # 20% chance to hire manager (increased from 5%)
            if not has_manager or num_employees > 10:  # Hire manager if we don't have one, or if we have lots of workers
                return 3  # Hire manager
        
        return 0  # No action
    
    def _get_naive_layout_action(self, current_timestep) -> list:
        """
        WEEK 1 STEP 1: Frequency-based layout optimization
        Move frequently accessed items closer to delivery areas
        """
        
        # Only optimize every 100 steps to avoid disrupting operations
        if current_timestep % 100 != 0:
            return [0, 0]
        
        # TODO: Get item frequency data from environment
        # HINT: Use self.env.warehouse_grid.item_access_frequency
        # HINT: Check if frequency data exists before proceeding
        grid = self.env.warehouse_grid
        item_frequencies = grid.item_access_frequency
        if item_frequencies is None or np.sum(item_frequencies) == 0:
            return [0, 0]
        
        # TODO: Identify "hot" items (frequently accessed)
        # TODO: Filter to only items that have been accessed (frequency > 0)
        active_frequencies = item_frequencies[item_frequencies > 0]
        # TODO: Calculate 75th percentile threshold for "hot" items
        # HINT: Use np.percentile(active_frequencies, 75)
        self.hot_threshold = np.percentile(active_frequencies, 75)
        # TODO: Find all items above this threshold
        hot_items = np.where(item_frequencies >= self.hot_threshold)[0]

        # TODO: Find delivery positions
        # HINT: Use getattr(grid, 'truck_bay_positions', [(grid.width//2, grid.height//2)])
        delivery_positions = getattr(grid, 'truck_bay_positions', [(grid.width//2, grid.height//2)])

        # Step 2.4 parameter: Minimum Improvement
        minimum_improvement = 1

        # TODO: For each hot item, check if it's far from delivery
        for item in hot_items:
            # TODO: For each hot item, get its current location
            locations = grid.find_item_locations(int(item))
            if not locations:
                continue
            current_pos = locations[0]

            # TODO: Calculate distance to nearest delivery point
            # HINT: Use grid.manhattan_distance() to calculate distances
            current_dist = min(grid.manhattan_distance(current_pos, delivery_pos)
                               for delivery_pos in delivery_positions)

            # TODO: If hot item is >3 steps from delivery, find closer position
            # HINT: Look for empty spots or positions with cold items
            if current_dist > 3:
                # TODO: If optimization needed, search for closer positions
                # HINT: Call helper method to find best swap position
                swap = self._find_closer_position(current_pos, delivery_positions)
                if swap is None:
                    continue

                # Step 2.1 framework: benefit = frequency x distance_saved
                target_pos = (swap[1] % grid.width, swap[1] // grid.width)
                target_dist = min(grid.manhattan_distance(target_pos, delivery_pos)
                                  for delivery_pos in delivery_positions)
                distance_saved = current_dist - target_dist
                benefit = item_frequencies[item] * distance_saved

                # TODO: Return [current_position_index, target_position_index] for beneficial swap
                if benefit > minimum_improvement:
                    # print(f"  SWAP: item {item} (freq {item_frequencies[item]:.0f}) "
                    #       f"moving {current_dist} -> {target_dist} steps from bay")
                    self.frequency_swap_count += 1
                    return swap
        # Phase 2: If no frequency-based improvement found, try co-occurrence clustering
        if current_timestep % 200 == 0:  # Less frequent than hot-item optimization
            cooccurrence_swap = self._find_cooccurrence_swap()
            if cooccurrence_swap:
                # print(f"  CLUSTER: swap {cooccurrence_swap}")
                self.cooccurrence_swap_count += 1
                return cooccurrence_swap
        return [0, 0]  # No beneficial swap found

    def _find_closer_position(self, current_pos, delivery_positions):
        """
        Greedy neighborhood search for better item placement.

        Algorithm: Exhaustive search of all storage positions to find
        the position that minimizes distance to delivery points.

        Returns [current_index, target_index] if beneficial swap found.
        """
        grid = self.env.warehouse_grid
        current_idx = current_pos[1] * grid.width + current_pos[0]
        current_dist = min(grid.manhattan_distance(current_pos, delivery_pos)
                           for delivery_pos in delivery_positions)

        best_improvement = 0
        best_swap = None

        # TODO: Implement exhaustive neighborhood search
        # TODO: Loop through all grid positions (nested for loops over x,y)
        for y in range(grid.height):
            for x in range(grid.width):
                # TODO: Check if position is a storage cell (grid.cell_types[y, x] == 1)
                if grid.cell_types[y, x] != 1:
                    continue

                # Step 2.3 HINT: Look for empty spots or positions with cold items
                # (cold = below the 75th-percentile hot threshold)
                occupant = grid.get_item_at_position(x, y)
                if occupant is not None and grid.item_access_frequency[occupant] >= self.hot_threshold:
                    continue

                # TODO: Calculate distance from candidate position to delivery
                candidate_dist = min(grid.manhattan_distance((x, y), delivery_pos)
                                     for delivery_pos in delivery_positions)
                improvement = current_dist - candidate_dist

                # TODO: Require minimum improvement threshold (>1 step closer)
                if improvement <= 1:
                    continue

                # TODO: Apply greedy selection: choose position with maximum distance improvement
                if improvement > best_improvement:
                    best_improvement = improvement
                    # TODO: Convert 2D coordinates to 1D index for return value
                    # HINT: 1D index = y * grid.width + x
                    best_swap = [current_idx, y * grid.width + x]

        return best_swap  # None if no better position found

    def _find_cooccurrence_swap(self):
        """
        Greedy clustering algorithm for association-based spatial optimization.

        Algorithm: Scan all item pairs for clustering opportunities,
        calculate benefit for each, and greedily select highest-benefit move.

        Returns swap that maximizes benefit = co-occurrence_frequency × distance_saved
        """
        grid = self.env.warehouse_grid
        cooccurrence = grid.item_cooccurrence

        # Greedy search parameters
        min_cooccurrence = 3      # Minimum frequency threshold
        min_distance = 4          # Minimum distance threshold for clustering
        best_benefit = 0          # Track best benefit found
        best_swap = None          # Track best swap candidate

        # TODO: Implement greedy benefit maximization
        # TODO: Scan co-occurrence matrix (nested loops: item1, item2 where item1 < item2)
        for item1 in range(grid.num_item_types):
            for item2 in range(item1 + 1, grid.num_item_types):
                # TODO: Apply frequency filter (cooccurrence[item1, item2] > min_cooccurrence)
                cooccurrence_count = cooccurrence[item1, item2]
                if cooccurrence_count <= min_cooccurrence:
                    continue

                # TODO: Get current locations using grid.find_item_locations()
                item1_locations = grid.find_item_locations(item1)
                item2_locations = grid.find_item_locations(item2)
                if not item1_locations or not item2_locations:
                    continue
                pos1, pos2 = item1_locations[0], item2_locations[0]

                # TODO: Calculate current distance between items
                current_distance = grid.manhattan_distance(pos1, pos2)

                # TODO: Apply distance filter (current_distance > min_distance)
                if current_distance <= min_distance:
                    continue

                # TODO: Calculate benefit = cooccurrence_count × current_distance
                benefit = cooccurrence_count * current_distance

                # TODO: Update best_benefit and best_swap if this benefit is higher
                if benefit > best_benefit:
                    # TODO: Find adjacency swap for best pair (call helper method)
                    swap = self._find_adjacency_swap(pos1, pos2)
                    if swap:
                        best_benefit = benefit
                        best_swap = swap

        return best_swap  # Return highest-benefit clustering move

    def _find_adjacency_swap(self, pos1, pos2):
        """
        Helper for Step 3.3: move the item at pos1 into a storage cell
        adjacent to pos2, so the co-occurring pair sits side by side.

        Only targets empty cells or cold items (Step 2.3 hint), so
        clustering never displaces a hot item.
        """
        grid = self.env.warehouse_grid
        hot_threshold = getattr(self, 'hot_threshold', 0)
        pos1_idx = pos1[1] * grid.width + pos1[0]

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            x, y = pos2[0] + dx, pos2[1] + dy
            if not grid.is_valid_position(x, y) or (x, y) == pos1:
                continue
            if grid.cell_types[y, x] != 1:   # must be a storage cell
                continue
            occupant = grid.get_item_at_position(x, y)
            if occupant is None or grid.item_access_frequency[occupant] < hot_threshold:
                return [pos1_idx, y * grid.width + x]
        return None

    def track_layout_performance(self):
        """
        Performance analysis for greedy layout optimization algorithms.

        Measures:
        - Layout efficiency (frequency-weighted distances)
        - Algorithm convergence (swaps per period)
        - Optimization impact over time
        """
        if not hasattr(self, 'layout_metrics'):
            self.layout_metrics = []

        # Calculate current layout efficiency using weighted distance metric
        efficiency = self._calculate_layout_efficiency()

        self.layout_metrics.append({
            'timestep': self.env.current_timestep,
            'efficiency': efficiency,
            'total_swaps': len([a for a in self.action_history if a['layout_swap'] != [0, 0]]),
            'phase1_swaps': self._count_frequency_swaps(),
            'phase2_swaps': self._count_cooccurrence_swaps()
        })

        # Print progress every 1000 steps
        if self.env.current_timestep % 1000 == 0:
            recent_efficiency = np.mean([m['efficiency'] for m in self.layout_metrics[-10:]])
            print(f"Layout efficiency: {recent_efficiency:.3f}")

    def _calculate_layout_efficiency(self):
        """
        Objective function evaluation for layout quality.

        Algorithm: Weighted average distance where weights = access frequency
        Lower weighted distance = higher efficiency (better layout)
        """
        # TODO: Implement frequency-weighted distance calculation
        # TODO: Get item frequencies and delivery positions
        grid = self.env.warehouse_grid
        item_frequencies = grid.item_access_frequency
        delivery_positions = getattr(grid, 'truck_bay_positions', [(grid.width//2, grid.height//2)])

        weighted_distance_sum = 0.0
        total_frequency = 0.0

        # TODO: For each item with frequency > 0:
        for item in np.where(item_frequencies > 0)[0]:
            #       - Get item location
            locations = grid.find_item_locations(int(item))
            if not locations:
                continue
            #       - Calculate distance to nearest delivery
            distance = min(grid.manhattan_distance(locations[0], delivery_pos)
                           for delivery_pos in delivery_positions)
            #       - Weight distance by access frequency
            weighted_distance_sum += item_frequencies[item] * distance
            total_frequency += item_frequencies[item]

        if total_frequency == 0:
            return 0.0

        # TODO: Return normalized efficiency score (0-1 scale)
        # HINT: efficiency = 1.0 - (weighted_avg_distance / max_possible_distance)
        weighted_avg_distance = weighted_distance_sum / total_frequency
        max_possible_distance = grid.width + grid.height
        return 1.0 - (weighted_avg_distance / max_possible_distance)
    
    # track_layout_performance() calls these two methods, but the resource does not define them.
    def _count_frequency_swaps(self):
        """Number of Phase 1 (hot item) swaps this episode."""
        return getattr(self, 'frequency_swap_count', 0)

    def _count_cooccurrence_swaps(self):
        """Number of Phase 2 (co-occurrence) swaps this episode."""
        return getattr(self, 'cooccurrence_swap_count', 0)

    
    def _get_naive_order_assignments(self, queue_info, employee_info) -> list:
        """
        WEEK 2 STEP 2: Order assignment - students should improve this!
        
        Current problems:
        - Ignores employee locations
        - No consideration of order priority/value
        - Random assignments regardless of efficiency
        - Doesn't check if employees are actually available
        """
        
        # TODO WEEK 2 STEP 2: Students should implement intelligent order assignment
        # Current approach: Random assignments
        
        assignments = [0] * 20  # No assignments by default
        
        # Count how many employees we have (very naive)
        num_employees = int(np.sum(employee_info[:, 0] > 0))
        
        # Randomly assign first few orders to first few employees
        if num_employees > 0:
            for i in range(min(3, num_employees)):  # Only assign 3 orders max
                if np.random.random() < 0.6:  # 60% chance to assign
                    assignments[i] = (i % num_employees) + 1  # Random employee
        
        return assignments
    
    def record_reward(self, reward: float):
        """
        WEEK 3 STEP 1: Reward tracking and learning - students should expand this
        
        TODO WEEK 3 STEP 1: Students should implement:
        - Proper reward tracking
        - Performance analysis
        - Adaptive parameter adjustment
        - Multi-objective optimization
        """
        self.reward_history.append(reward)
        
        # Skeleton optimization - doesn't actually learn anything useful
        if len(self.reward_history) > 10:
            # "Update" weights randomly (this doesn't actually improve performance)
            if reward > 0:
                self.staffing_weights += np.random.randn(4) * 0.01
                self.layout_weights += np.random.randn(3) * 0.01
    
    def should_update_policy(self) -> bool:
        """
        WEEK 3 STEP 2: Policy updates and adaptation - students should improve this
        
        TODO WEEK 3 STEP 2: Students should implement proper update schedules
        """
        return len(self.action_history) % 50 == 0  # Arbitrary update frequency
    
    def get_performance_metrics(self) -> Dict:
        """
        Get agent performance metrics for analysis
        Students can use this to debug their improvements
        """
        if not self.reward_history:
            return {"avg_reward": 0, "total_actions": 0}
        
        return {
            "avg_reward": np.mean(self.reward_history[-100:]),  # Last 100 rewards
            "total_actions": len(self.action_history),
            "exploration_rate": self.exploration_rate,
            "recent_performance": np.mean(self.reward_history[-10:]) if len(self.reward_history) >= 10 else 0
        }


def create_skeleton_optimization_agent(env) -> SkeletonOptimizationAgent:
    """Factory function to create skeleton Optimization agent"""
    return SkeletonOptimizationAgent(env)


# TODO: Students should implement these advanced components:

class StudentOptimizationAgent(SkeletonOptimizationAgent):
    """
    Template for students to implement their improved Optimization agent
    
    Suggested improvements:
    1. Replace random staffing with demand-based hiring
    2. Implement proper layout optimization using item frequencies
    3. Add distance-based order assignment
    4. Implement basic Q-optimization or policy gradients
    5. Add proper exploration vs exploitation balance
    """
    
    def __init__(self, env):
        super().__init__(env)
        self.name = "StudentOptimization"
        
        # TODO: Students implement these
        # self.q_table = {}
        # self.policy_network = SimpleNeuralNetwork()
        # self.experience_buffer = []
        # self.target_network = None
        
    def _get_improved_staffing_action(self, financial_state, employee_info, queue_info):
        """
        WEEK 2 STEP 1: Students implement intelligent staffing:
        - Hire when queue is growing
        - Fire when queue is empty for extended periods
        - Consider profit margins before hiring
        - Balance managers vs workers
        """
        pass
    
    def _get_improved_layout_action(self, observation):
        """
        WEEK 1 STEP 1: Students implement smart layout optimization:
        - Move frequently accessed items closer to delivery
        - Group items that are often ordered together
        - Only optimize when queue is manageable
        - Track swap effectiveness
        """
        pass
    
    def _get_improved_order_assignments(self, queue_info, employee_info):
        """
        WEEK 2 STEP 2: Students implement efficient order assignment:
        - Assign orders to closest available employees
        - Prioritize high-value or urgent orders
        - Consider employee current locations
        - Balance workload across employees
        """
        pass
    
    def learn_from_experience(self, state, action, reward, next_state, done):
        """
        WEEK 3 STEP 3: Students implement multi-objective optimization:
        - Performance trend analysis
        - Adaptive parameter tuning
        - Multi-objective trade-off handling
        - Robust optimization techniques
        """
        pass