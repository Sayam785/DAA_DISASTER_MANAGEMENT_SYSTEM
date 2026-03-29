
VOLUNTEER_SKILL_COSTS = {
    "Medical":      {"value": 9, "cost": 4},
    "NDRF":         {"value": 10, "cost": 5},
    "Rescue":       {"value": 8, "cost": 3},
    "Logistics":    {"value": 6, "cost": 2},
    "Firefighting": {"value": 9, "cost": 4},
    "Search":       {"value": 7, "cost": 3},
    "Transport":    {"value": 5, "cost": 2},
    "Comms":        {"value": 6, "cost": 3},
}

DISASTER_RESOURCE_BUDGETS = {
    "Fire":         12,
    "Flood":        15,
    "Earthquake":   18,
    "Medical":      10,
    "Landslide":    14,
    "Accident":     8,
    "Default":      10,
}


def knapsack_optimize(volunteers, disaster_type, max_budget=None):
    """
    Solves the 0/1 Knapsack problem to select the optimal set of volunteers
    for a given disaster within a resource budget constraint.

    Args:
        volunteers: list of volunteer dicts (must have 'id', 'group' keys)
        disaster_type: string to determine budget
        max_budget: override budget (optional)

    Returns:
        dict with selected volunteers, total_value, total_cost, dp_table_summary
    """
    if not volunteers:
        return {
            "selected": [],
            "total_value": 0,
            "total_cost": 0,
            "budget": max_budget or 0,
            "dp_steps": 0
        }

    W = max_budget or DISASTER_RESOURCE_BUDGETS.get(disaster_type, DISASTER_RESOURCE_BUDGETS["Default"])

    # Assign value and cost to each volunteer based on their skill group
    items = []
    for v in volunteers:
        profile = VOLUNTEER_SKILL_COSTS.get(v["group"], {"value": 5, "cost": 2})
        items.append({
            "id": v["id"],
            "name": v["name"],
            "group": v["group"],
            "value": profile["value"],
            "cost": profile["cost"]
        })

    n = len(items)

    # Build DP table: dp[i][w] = max value using first i items with budget w
    dp = [[0] * (W + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        item = items[i - 1]
        item_cost = item["cost"]
        item_value = item["value"]

        for w in range(W + 1):
            # Option 1: skip this volunteer
            dp[i][w] = dp[i - 1][w]

            # Option 2: include this volunteer (only if budget allows)
            if item_cost <= w:
                include_value = dp[i - 1][w - item_cost] + item_value
                if include_value > dp[i][w]:
                    dp[i][w] = include_value

    # Backtrack to find which volunteers were selected
    selected = []
    w = W
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected.append(items[i - 1])
            w -= items[i - 1]["cost"]

    selected.reverse()

    total_value = dp[n][W]
    total_cost = sum(s["cost"] for s in selected)

    return {
        "selected": selected,
        "total_value": total_value,
        "total_cost": total_cost,
        "budget": W,
        "dp_steps": n * (W + 1),
        "all_considered": items
    }


def get_supplies_allocation(supplies_list, capacity=20):
    """
    Secondary knapsack: optimally allocate supply items within weight/volume capacity.

    Args:
        supplies_list: list of supply strings (e.g. ["Water", "Blankets"])
        capacity: total carrying capacity units

    Returns:
        dict with selected supplies and utilization
    """
    SUPPLY_PROFILES = {
        "Water":         {"value": 9, "weight": 5},
        "Blankets":      {"value": 6, "weight": 3},
        "First Aid":     {"value": 8, "weight": 2},
        "Food":          {"value": 7, "weight": 4},
        "Ropes":         {"value": 5, "weight": 2},
        "Flashlights":   {"value": 6, "weight": 1},
        "Stretchers":    {"value": 8, "weight": 4},
        "Fire Gear":     {"value": 9, "weight": 5},
        "Oxygen":        {"value": 10, "weight": 6},
        "Sandbags":      {"value": 7, "weight": 5},
    }

    items = []
    for supply in supplies_list:
        supply = supply.strip()
        if supply in SUPPLY_PROFILES:
            profile = SUPPLY_PROFILES[supply]
            items.append({"name": supply, **profile})
        else:
            items.append({"name": supply, "value": 5, "weight": 2})

    n = len(items)
    W = capacity

    if n == 0:
        return {"selected_supplies": [], "total_weight": 0, "capacity": W}

    dp = [[0] * (W + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for w in range(W + 1):
            dp[i][w] = dp[i - 1][w]
            if items[i - 1]["weight"] <= w:
                include = dp[i - 1][w - items[i - 1]["weight"]] + items[i - 1]["value"]
                if include > dp[i][w]:
                    dp[i][w] = include

    # Backtrack
    selected = []
    w = W
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected.append(items[i - 1])
            w -= items[i - 1]["weight"]

    return {
        "selected_supplies": [s["name"] for s in selected],
        "total_weight": sum(s["weight"] for s in selected),
        "capacity": capacity
    }
