
import heapq
from itertools import count


# Cost of relaxing each preference
RELAX_COST = {
    "duration": 1,
    "location": 3,
    "difficulty": 5,
}


def is_available(trek):
    return (
        trek["status"].lower() == "open"
        and trek["available_slots"] > 0
    )


def same_location(trek_location, preferred_location):
    trek_location = trek_location.strip().casefold()
    preferred_location = preferred_location.strip().casefold()

    return (
        preferred_location in trek_location
        or trek_location in preferred_location
    )


def matches(trek, preferences, state):
    relax_duration, relax_location, relax_difficulty = state

    if not relax_difficulty:
        if trek["difficulty"].lower() != preferences["difficulty"].lower():
            return False

    if not relax_duration:
        if trek["duration"] > preferences["max_duration"]:
            return False

    if not relax_location:
        if not same_location(
                trek["location"],
                preferences["location"]
        ):
            return False

    return is_available(trek)


def heuristic(treks, preferences, state):
    """Estimate the cheapest relaxations needed for a valid trek."""
    relax_duration, relax_location, relax_difficulty = state
    best = float("inf")

    for trek in treks:
        if not is_available(trek):
            continue

        cost = 0

        if (
            not relax_difficulty
            and trek["difficulty"].lower()
            != preferences["difficulty"].lower()
        ):
            cost += RELAX_COST["difficulty"]

        if (
            not relax_duration
            and trek["duration"] > preferences["max_duration"]
        ):
            cost += RELAX_COST["duration"]

        if (
                not relax_location
                and not same_location(
            trek["location"],
            preferences["location"]
        )
        ):
            cost += RELAX_COST["location"]

        best = min(best, cost)

    return best


def astar_recommend(treks, preferences):
    """Find the lowest-cost preference relaxation using A*."""
    start = (False, False, False)
    serial = count()

    frontier = [
        (
            heuristic(treks, preferences, start),
            0,
            next(serial),
            start,
        )
    ]

    best_cost = {start: 0}
    explored = 0

    while frontier:
        _, g_cost, _, state = heapq.heappop(frontier)

        if g_cost != best_cost.get(state):
            continue

        explored += 1

        results = [
            trek for trek in treks
            if matches(trek, preferences, state)
        ]

        if results:
            return {
                "treks": results,
                "relaxed": [
                    name for name, enabled in zip(
                        ("duration", "location", "difficulty"),
                        state
                    )
                    if enabled
                ],
                "cost": g_cost,
                "states_explored": explored,
            }

        # Each successor relaxes one additional preference.
        for index, name in enumerate(
            ("duration", "location", "difficulty")
        ):
            if state[index]:
                continue

            next_state = list(state)
            next_state[index] = True
            next_state = tuple(next_state)

            new_cost = g_cost + RELAX_COST[name]

            if new_cost < best_cost.get(next_state, float("inf")):
                best_cost[next_state] = new_cost
                h_cost = heuristic(treks, preferences, next_state)

                heapq.heappush(
                    frontier,
                    (
                        new_cost + h_cost,
                        new_cost,
                        next(serial),
                        next_state,
                    ),
                )

    return {
        "treks": [],
        "relaxed": [],
        "cost": None,
        "states_explored": explored,
    }


# Test the algorithm independently before integrating Flask.
if __name__ == "__main__":
    sample_treks = [
        {
            "name": "Rajmachi Trek",
            "location": "Pune",
            "difficulty": "Moderate",
            "duration": 2,
            "status": "Open",
            "available_slots": 0,
        },
        {
            "name": "Lohagad Trek",
            "location": "Pune",
            "difficulty": "Moderate",
            "duration": 2,
            "status": "Open",
            "available_slots": 5,
        },
        {
            "name": "Harishchandragad Trek",
            "location": "Nashik",
            "difficulty": "Moderate",
            "duration": 3,
            "status": "Open",
            "available_slots": 4,
        },
        {
            "name": "Closed Trek",
            "location": "Pune",
            "difficulty": "Moderate",
            "duration": 2,
            "status": "Closed",
            "available_slots": 10,
        },
    ]

    preferences = {
        "difficulty": "Moderate",
        "max_duration": 2,
        "location": "Pune",
    }

    result = astar_recommend(sample_treks, preferences)

    print("Relaxed preferences:", result["relaxed"])
    print("Search cost:", result["cost"])
    print("States explored:", result["states_explored"])
    print("Recommended treks:")

    for trek in result["treks"]:
        print("-", trek["name"])
