from park import Park
from behavior_reference import BEHAVIOR_ARCHETYPE_PARAMETERS


def main():
    VERSION = "sim_test"
    VERBOSITY = 1
    SHOW_PLOTS = True
    RNG_SEED = 10

    TOTAL_DAILY_AGENTS = 5000  # 38047  # actual average
    PERFECT_ARRIVALS = True
    HOURLY_PERCENT = {
        "10:00 AM": 10,
        "11:00 AM": 20,
        "12:00 AM": 17,
        "3:00 PM": 20,
        "4:00 PM": 15,
        "5:00 PM": 10,
        "6:00 PM": 1,
        "7:00 PM": 5,
        "8:00 PM": 1,
        "9:00 PM": 1,
        "10:00 PM": 0,
        "11:00 PM": 0,
        "12:00 PM": 0
    }
    EXP_ABILITY_PCT = 0.9
    EXP_THRESHOLD = 30
    EXP_LIMIT = 1

    AGENT_ARCHETYPE_DISTRIBUTION = {
        "ride_enthusiast": 10,
        "ride_favorer": 15,
        "park_tourer": 25,
        "park_visitor": 30,
        "activity_favorer": 15,
        "activity_enthusiast": 5,
    }

    ATTRACTIONS = [
        {
            "name": "Ride of Passage",
            "run_time": 7,
            "park_area": "Pandora",
            "hourly_throughput": 1646,
            "num_vehicles": 4,
            "agents_per_vehicle": 48,
            "popularity": 10,
            "expedited_queue": True,
            "expedited_queue_ratio": 0.8,
            "child_eligible": True,
            "adult_eligible": True,
        },
        {
            "name": "Serengeti Safari",
            "run_time": 20,
            "park_area": "Africa",
            "hourly_throughput": 3240,
            "num_vehicles": 30,
            "agents_per_vehicle": 36,
            "popularity": 9,
            "expedited_queue": True,
            "expedited_queue_ratio": 0.8,
            "child_eligible": True,
            "adult_eligible": True,
        },
        {
            "name": "Annapurna Adventure",
            "run_time": 3,
            "park_area": "Asia",
            "hourly_throughput": 2040,
            "num_vehicles": 3,
            "agents_per_vehicle": 34,
            "popularity": 8,
            "expedited_queue": True,
            "expedited_queue_ratio": 0.8,
            "child_eligible": False,
            "adult_eligible": True,
        },
        {
            "name": "Kaveri Rapids",
            "run_time": 5,
            "park_area": "Asia",
            "hourly_throughput": 2160,
            "num_vehicles": 15,
            "agents_per_vehicle": 12,
            "popularity": 7,
            "expedited_queue": True,
            "expedited_queue_ratio": 0.8,
            "child_eligible": True,
            "adult_eligible": True,
        },
        {
            "name": "Agave River Journey",
            "run_time": 5,
            "park_area": "Pandora",
            "hourly_throughput": 1440,
            "num_vehicles": 15,
            "agents_per_vehicle": 8,
            "popularity": 6,
            "expedited_queue": True,
            "expedited_queue_ratio": 0.8,
            "child_eligible": True,
            "adult_eligible": True,
        },
        {
            "name": "Dinosaur",
            "run_time": 4,
            "park_area": "Dinoland USA",
            "hourly_throughput": 2520,
            "num_vehicles": 14,
            "agents_per_vehicle": 12,
            "popularity": 5,
            "expedited_queue": True,
            "expedited_queue_ratio": 0.8,
            "child_eligible": False,
            "adult_eligible": True,
        },
        {
            "name": "Primeval Hurl",
            "run_time": 2,
            "park_area": "Dinoland USA",
            "hourly_throughput": 1440,
            "num_vehicles": 12,
            "agents_per_vehicle": 4,
            "popularity": 4,
            "expedited_queue": True,
            "expedited_queue_ratio": 0.8,
            "child_eligible": True,
            "adult_eligible": True,
        },
        {
            "name": "It's Difficult to Be an Insect",
            "run_time": 13,
            "park_area": "Discovery Island",
            "hourly_throughput": 1985,
            "num_vehicles": 1,
            "agents_per_vehicle": 430,
            "popularity": 3,
            "expedited_queue": True,
            "expedited_queue_ratio": 0.8,
            "child_eligible": True,
            "adult_eligible": True,
        }
    ]

    ACTIVITIES = [
        {
            "name": "sightseeing",
            "park_area": "Discovery Island",
            "popularity": 5,
            "mean_time": 5
        },
        {
            "name": "show",
            "park_area": "Discovery Island",
            "popularity": 5,
            "mean_time": 30
        },
        {
            "name": "merchandise",
            "park_area": "Discovery Island",
            "popularity": 5,
            "mean_time": 30
        },
        {
            "name": "food",
            "park_area": "Discovery Island",
            "popularity": 5,
            "mean_time": 45
        }
      ]

    PARK_MAP = {
        "Discovery Island":
            {
                "Discovery Island": 1,  # distance for POI within same area
                "Pandora": 5,
                "Africa": 5,
                "Asia": 5,
                "Dinoland USA": 5,
                "Oasis": 3
            },
        "Pandora":
            {
                "Discovery Island": 5,
                "Pandora": 2,
                "Africa": 8,
                "Asia": 10,
                "Dinoland USA": 10,
                "Oasis": 8
            },
        "Africa":
            {
                "Discovery Island": 5,
                "Pandora": 8,
                "Africa": 2,
                "Asia": 6,
                "Dinoland USA": 10,
                "Oasis": 8
            },
        "Asia":
            {
                "Discovery Island": 5,
                "Pandora": 10,
                "Africa": 6,
                "Asia": 2,
                "Dinoland USA": 5,
                "Oasis": 8
            },
        "Dinoland USA":
            {
                "Discovery Island": 5,
                "Pandora": 10,
                "Africa": 10,
                "Asia": 5,
                "Dinoland USA": 1,
                "Oasis": 8
            },
        "Oasis":
            {
                "Discovery Island": 3,
                "Pandora": 8,
                "Africa": 8,
                "Asia": 8,
                "Dinoland USA": 8,
                "Oasis": 1
            }
    }

    ENTRANCE_PARK_AREA = "Oasis"

    # Initialize Park
    RNG_SEED = 5

    PLOT_RANGE = {
        "Attraction Queue Length": 'auto',
        "Attraction Wait Time": 'auto',
        "Attraction Expedited Queue Length": 'auto',
        "Attraction Expedited Wait Time": 'auto',
        "Activity Vistors": 'auto',
        "Approximate Agent Distribution (General)": 1.0,
        "Approximate Agent Distribution (Specific)": 1.0,
        "Agent Arrivals and Departures": 'auto',
        "Attraction Average Wait Times": 'auto',
        "Agent Attractions Histogram": 1.0,
        "Attraction Total Visits": 'auto',
        "Expedited Pass Distribution": 'auto',
        "Age Class Distribution": 'auto',
    }

    park = Park(
        attraction_list=ATTRACTIONS,
        activity_list=ACTIVITIES,
        park_map=PARK_MAP,
        entrance_park_area=ENTRANCE_PARK_AREA,
        plot_range=PLOT_RANGE,
        random_seed=RNG_SEED,
        version=VERSION,
        verbosity=VERBOSITY
    )

    # Build Arrivals

    park.generate_arrival_schedule(
        arrival_seed=HOURLY_PERCENT,
        total_daily_agents=TOTAL_DAILY_AGENTS,
        perfect_arrivals=PERFECT_ARRIVALS,
    )

    # Build Agents
    park.generate_agents(
        behavior_archetype_distribution=AGENT_ARCHETYPE_DISTRIBUTION,
        exp_ability_pct=EXP_ABILITY_PCT,
        exp_wait_threshold=EXP_THRESHOLD,
        exp_limit=EXP_LIMIT
    )

    # Build Attractions + Activities
    park.generate_attractions()
    park.generate_activities()

    # Pass Time
    for _ in range(len(HOURLY_PERCENT.keys()) * 60):
        park.step()

    # Save Parameters of Current Run
    sim_parameters = {
        "VERSION": VERSION,
        "VERBOSITY": VERBOSITY,
        "SHOW_PLOTS": SHOW_PLOTS,
        "RNG_SEED": RNG_SEED,
        "TOTAL_DAILY_AGENTS": TOTAL_DAILY_AGENTS,
        "PERFECT_ARRIVALS": PERFECT_ARRIVALS,
        "HOURLY_PERCENT": HOURLY_PERCENT,
        "EXP_ABILITY_PCT": EXP_ABILITY_PCT,
        "EXP_THRESHOLD": EXP_THRESHOLD,
        "EXP_LIMIT": EXP_LIMIT,
        "AGENT_ARCHETYPE_DISTRIBUTION": AGENT_ARCHETYPE_DISTRIBUTION,
        "ATTRACTIONS": ATTRACTIONS,
        "ACTIVITIES": ACTIVITIES,
        "BEHAVIOR_ARCHETYPE_PARAMETERS": BEHAVIOR_ARCHETYPE_PARAMETERS,
    }
    park.write_data_to_file(
        data=sim_parameters,
        output_file_path=f"{VERSION}/parameters",
        output_file_format="json"
    )

    # Store + Print Data
    # park.make_plots(show=SHOW_PLOTS)
    park.print_logs(N=5)


if __name__ == "__main__":

    # Run standard simulation
    main()
