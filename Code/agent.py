import random
import numpy as np

from behavior_reference import BEHAVIOR_ARCHETYPE_PARAMETERS


def calculate_utility(w_0, popularity, w_1, n_past, n_future, w_2, wait_time, w_3, distance):
    """ first pass at a utility function for selecting an attraction based on popularity, number of times already done
    or will do, wait time, and distance (in minutes) from current location.
    utility is proportional to popularity and inversely proportional to number of times already done (law of diminishing
    marginal utility).  Wait time also negative affects utility and is represented here as a discounted reward modifier.
    Stable values of w_2 range from 0.98 to 0.998.  E.g., if w_2=0.9885, a 60 minute wait cuts the utility in half.

    Will likely fine-tune this function over time to get more balanced results by archetype.
    """
    utility = w_0 * popularity / (w_1 * (1 + n_past + n_future))
    utility *= w_2 ** wait_time
    utility -= w_3 * distance
    return utility


def softmax(attraction_utilities, normalize=True):
    """ Quick self-implementation of softmax.
    attraction_utilities: dict of utility scores of valid attractions.
    output: dict of attraction_name: probability of selecting item for all keys in attraction_utilities
    """
    if normalize:
        # we need to get mu, std of these utilities and then return softmax of that scaled set
        mu = np.mean([attraction_utilities[u] for u in attraction_utilities])
        std = max(np.std([attraction_utilities[u] for u in attraction_utilities]), 1)
        attr_util_norm = {
            u: (attraction_utilities[u] - mu) / std for u in attraction_utilities
        }
        e_x_sum = sum([np.exp(u) for u in attr_util_norm.values()])
    else:
        e_x_sum = sum([np.exp(u) for u in attraction_utilities.values()])
    return {
        attraction_name: np.exp(utility) / e_x_sum
        for attraction_name, utility in attraction_utilities.items()
    }


class Agent:
    """ Class which defines agents within the park simulation. Stores agent characteristics, current state and log. """

    def __init__(self, random_seed):
        """  """

        self.agent_id = None  # unique identification number for agent
        self.state = {}  # characterizes agents current state
        self.log = ""  # logs agent history as text
        self.random_seed = random_seed

        for behavior_type, behavior_dict in BEHAVIOR_ARCHETYPE_PARAMETERS.items():
            age_class_sum = behavior_dict["percent_no_child_rides"] + behavior_dict["percent_no_adult_rides"] + \
                            behavior_dict["percent_no_preference"]
            # deal with fuzzy float addition
            if not 0.98 <= age_class_sum <= 1.0:
                raise AssertionError(
                    f"Behavior Archetype {behavior_type} characteristics percent_no_child_rides, percent_no_adult_rides,"
                    "and percent_no_preference, must add up to 1"
                )

    def initialize_agent(
            self,
            behavior_archetype_distribution,
            exp_ability,
            exp_wait_threshold,
            exp_limit,
            agent_id,
            attraction_names,
            activity_names
    ):
        """ Takes a dictionary of the agent behavior distributions, the agents unique id, a list of all attractions, and
        a list of all activities (non-attraction things to do at park). Initializes the agents characteristics, current state
        and their log. """

        self.agent_id = agent_id

        # initialize agent state
        self.state.update(
            {
                "arrival_time": None,
                "exit_time": None,
                "within_park": False,
                "current_location": None,
                "current_park_area": None,
                "current_action": None,
                "time_spent_at_current_location": 0,
                "destination": None,
                "time_to_destination": 0,
                "expedited_return_time": [],
                "expedited_pass": [],
                "expedited_pass_ability": exp_ability,
                "exp_wait_threshold": exp_wait_threshold,
                "exp_limit": exp_limit
            }
        )
        # initialize attraction history
        self.state.update(
            {
                "attractions": {
                    attraction: {
                        "times_completed": 0,
                    } for attraction in attraction_names
                }
            }
        )
        # initialize activity history
        self.state.update(
            {
                "activities": {
                    activity: {
                        "times_visited": 0,
                        "time_spent": 0,
                    } for activity in activity_names
                }
            }
        )

        # initialize agent behavior
        behavior_archetype = self.select_behavior_archetype(
            behavior_archetype_distribution=behavior_archetype_distribution,
            agent_id=agent_id,
        )

        self.state.update(
            {
                "age_class": self.select_age_class(
                    agent_id=agent_id,
                    behavior_archetype_dict=BEHAVIOR_ARCHETYPE_PARAMETERS[behavior_archetype]
                )
            }
        )
        if not self.state["age_class"]:
            raise ValueError("Agent age_class not set.")

        parameters = BEHAVIOR_ARCHETYPE_PARAMETERS[behavior_archetype]
        rng = np.random.default_rng(self.random_seed + self.agent_id)
        stay_time_preference = int(
            max((rng.normal(parameters["stay_time_preference"], parameters["stay_time_preference"] / 4, 1))[0], 0)
        )

        self.behavior = {
            "archetype": behavior_archetype,
            "stay_time_preference": stay_time_preference,
            "allow_repeats": parameters["allow_repeats"],
            "attraction_preference": parameters["attraction_preference"],
            "wait_threshold": parameters["wait_threshold"],
            "wait_discount_beta": parameters["wait_discount_beta"]
        }

    def select_behavior_archetype(self, agent_id, behavior_archetype_distribution):
        """ Selects a behavior_archetype based off of the behavior_archetype_distribution. """

        rng = random.uniform(0, sum(behavior_archetype_distribution.values()))
        floor = 0.0
        for behavior_archetype, behavior_archetype_weight in behavior_archetype_distribution.items():
            floor += behavior_archetype_weight
            if rng < floor:
                return behavior_archetype

    def select_age_class(self, agent_id, behavior_archetype_dict):
        """ Selects a behavior_archetype based off of the behavior_archetype_distribution. """

        age_class_distribution = {
            "no_child_rides": behavior_archetype_dict["percent_no_child_rides"],
            "no_adult_rides": behavior_archetype_dict["percent_no_adult_rides"],
            "no_preference": behavior_archetype_dict["percent_no_preference"]
        }
        rng = random.uniform(0, sum(age_class_distribution.values()))
        floor = 0.0
        for age_class, age_class_weight in age_class_distribution.items():
            floor += age_class_weight
            if rng < floor:
                return age_class

    def arrive_at_park(self, time, park_area):
        """ Takes a time (mins). Updates the Agent state and log to reflect arrival at the park """

        self.state["within_park"] = True
        self.state["arrival_time"] = time
        self.state["current_location"] = "gate"
        self.state["current_park_area"] = park_area
        self.state["current_action"] = "idling"
        self.state["time_spent_at_current_location"] = 0
        self.log += f"Agent arrived at park at time {time}. "

    def make_state_change_decision(self, attractions_dict, activities_dict, time, park_map, park_closed):
        """  When an agent is idle allow them to make a decision about what to do next. """
        # TODO: Should this method return action, location tuple or should it update internal state? or both?
        # ^ no, I think it's ok as-is.  agent wants to do something, park object will orchestrate the result of that
        # intended action.

        # decide if they want to leave
        # always leave park if the park is closed
        if park_closed:
            action = "leaving"
            location = "gate"
        else:
            action, location = self.decide_to_leave_park(time=time)

        if not action:
            # make decisions while holding an expedited pass
            action, location = self.make_attraction_activity_decision(
                activities_dict=activities_dict,
                attractions_dict=attractions_dict,
                park_map=park_map
            )

        return action, location

    def make_attraction_activity_decision(self, activities_dict, attractions_dict, park_map):
        """ Decide what to do """
        # TODO: If agent has a valid expedited queue pass, they should use it.
        for i in range(len(self.state["expedited_pass"])):
            if self.state["expedited_return_time"][i] <= 0:
                action, location = "redeeming exp pass", self.state["expedited_pass"][i]
                return action, location

        desired_decision_type, valid_attractions = self.decide_attraction_or_activity(
            attractions_dict=attractions_dict,
        )
        # select activity
        if desired_decision_type == "activity":
            selected_activity = self.select_activity_decision(activities_dict=activities_dict)
            action, location = "traveling", selected_activity
        # try to select attraction
        else:
            action, location = self.select_attraction_decision(
                valid_attractions=valid_attractions,
                attractions_dict=attractions_dict,
                park_map=park_map
            )
            # only default to activity if all wait times are too long for agent and
            # no exp passes are available
            if not action:
                selected_activity = self.select_activity_decision(activities_dict=activities_dict)
                action, location = "traveling", selected_activity

        return action, location

    def decide_attraction_or_activity(self, attractions_dict):
        """ Agent decides if they want to visit an attraction or activity. The agent will decide between
        an attraction or activity. If they select an activity, that's it. If they select an attraction, they
        see if any valid attractions exist for them to visit, while considering their attraction visit
        history and their expedited_pass status. If no valid attractions exist then they will default to 
        an activity. """

        # if agent has room for another exp pass, they should attempt to get one.?
        can_get_exp = len(self.state["expedited_pass"]) < self.state["exp_limit"] \
            and self.state["expedited_pass_ability"]

        coinflip = random.uniform(0, 1)
        if coinflip <= self.behavior["attraction_preference"] or can_get_exp:
            # determine which attractions agent is eligible for
            # remove repeats and/or attractions with exp pass in hand
            # TODO: Determine if we should allow attractions w/ exp passes in hand to be considered for standby
            if self.behavior["allow_repeats"]:
                valid_attractions = [
                    attraction for attraction in attractions_dict.keys()
                    if attraction not in self.state["expedited_pass"]
                ]
            else:
                valid_attractions = [
                    attraction for attraction, attractions_history in self.state["attractions"].items()
                    if attractions_history["times_completed"] == 0 and attraction not in self.state["expedited_pass"]
                ]
            if self.state["age_class"] == "no_child_rides":
                valid_attractions = [
                    attraction for attraction in valid_attractions if attractions_dict[attraction].adult_eligible
                ]
            elif self.state["age_class"] == "no_adult_rides":
                valid_attractions = [
                    attraction for attraction in valid_attractions if attractions_dict[attraction].child_eligible
                ]
            if len(valid_attractions) == 0:
                desired_decision_type = "activity"
                valid_attractions = []
            else:
                desired_decision_type = "attraction"
        else:
            desired_decision_type = "activity"
            valid_attractions = []

        return desired_decision_type, valid_attractions

    def select_attraction_decision(self, valid_attractions, attractions_dict, park_map):
        """ Selects an attraction to visit based on the attraction popularity """

        # get valid attraction wait times
        attraction_wait_times = {
            attraction_name: attraction.get_wait_time()
            for attraction_name, attraction in attractions_dict.items()
            if attraction_name in valid_attractions  # attractions_dict
        }
        # get valid attraction distances from agent (in minutes)
        attraction_distances = {
            attraction_name: park_map[self.state["current_park_area"]][attraction.park_area]
            for attraction_name, attraction in attractions_dict.items()
            if attraction_name in valid_attractions
        }
        attraction_popularity_distribution = {
            attraction_name: parameters.popularity for attraction_name, parameters in attractions_dict.items()
            if attraction_name in valid_attractions
        }
        attraction_n_past = {
            attr_name:
                attr_history["times_completed"] for attr_name, attr_history in self.state["attractions"].items()
            if attr_name in valid_attractions
        }
        attraction_n_future = {
            attr_name:
                1 if attr_name in self.state["expedited_pass"] else 0 for attr_name in attractions_dict.keys()
            if attr_name in valid_attractions
        }
        # get utility of all valid attractions once
        attraction_utilities = {
            attraction_name: calculate_utility(
                w_0=10,
                popularity=attraction_popularity_distribution[attraction_name],
                w_1=1,
                n_past=attraction_n_past[attraction_name],
                n_future=attraction_n_future[attraction_name],
                w_2=self.behavior["wait_discount_beta"],
                wait_time=attraction_wait_times[attraction_name],
                w_3=3,
                distance=attraction_distances[attraction_name]
            ) for attraction_name, parameters in attractions_dict.items()
            if attraction_name in valid_attractions
        }
        # remove any attractions with negative utility
        for attraction in valid_attractions:
            if attraction_utilities[attraction] <= 0:
                valid_attractions.remove(attraction)
                del attraction_utilities[attraction]
        action, location = None, None
        step_rng = 0
        while len(valid_attractions) > 0 and not action:
            step_rng += 1
            # generate popularity distribution for valid attractions
            probability_dist = softmax({
                attr: attraction_utilities[attr] for attr in valid_attractions
            })
            desired_attraction = random.choices(
                population=valid_attractions,
                weights=[probability_dist[attr] for attr in valid_attractions],
                k=1
            )[0]
            if (
                attraction_wait_times[desired_attraction] > self.state["exp_wait_threshold"]
                and self.state["expedited_pass_ability"]
                and len(self.state["expedited_pass"]) < self.state["exp_limit"]
                and attractions_dict[desired_attraction].expedited_queue
                and attractions_dict[desired_attraction].exp_pass_status == "open"
            ):
                action, location = "get pass", desired_attraction
            elif (
                    attraction_wait_times[desired_attraction]
                    > (self.behavior["wait_threshold"] + (attractions_dict[desired_attraction].popularity * 6))
            ):
                valid_attractions.remove(desired_attraction)
                del attraction_utilities[desired_attraction]
            elif any(
                    rt < attraction_wait_times[desired_attraction] + attractions_dict[desired_attraction].run_time
                    for rt in self.state["expedited_return_time"]
            ):
                valid_attractions.remove(desired_attraction)
                del attraction_utilities[desired_attraction]
            else:
                action, location = "traveling", desired_attraction

        return action, location

    def decide_to_leave_park(self, time):
        """ Agent determines if they should leave the park. Agents who just arrived will always decide to stay,
        otherwise agents will look at how long they have been at the park and how long they prefer to stay to make
        this decision """

        # TODO: Determine if holding any # of exp passes should influence this decision
        # TODO: Analyze how this is affecting agent time in park relative to stay time preference
        # Checking every timestep w/ growing prob of deciding to leave and never return will negatively bias
        # park attendance. geometric distribution: if 1% chance at each timestep of leaving forever, avg time to leave
        # is 100 timesteps but chance of leaving sooner is significant
        action, location = None, None

        # determine if they should leave park, the larger this number is the more likely they are to leave
        if time != self.state["arrival_time"]:
            actual_preference_value = (time - self.state["arrival_time"]) - self.behavior["stay_time_preference"]
            rng = np.random.default_rng(self.random_seed + self.agent_id + time)
            normal_coinflip = (rng.normal(0, 1, 1) * 60)[0]  # N(0,1) * 60 has 95% CI of (-117.6, 117.6)
            if actual_preference_value > normal_coinflip:
                action = "leaving"
                location = "gate"

        return action, location

    def select_activity_decision(self, activities_dict):
        """ Selects an activity to visit based off of the activity popularity. """

        activity_popularity_distribution = {
            activity: parameters.popularity for activity, parameters in activities_dict.items()
        }
        rng = random.uniform(0, sum(activity_popularity_distribution.values()))
        floor = 0.0
        for activity, activity_weight in activity_popularity_distribution.items():
            floor += activity_weight
            if rng < floor:
                return activity

    def pass_time(self):
        """ Pass 1 minute of time """
        if self.state["within_park"]:
            self.state["time_spent_at_current_location"] += 1
            if self.state["expedited_pass"]:
                self.state["expedited_return_time"] = [val - 1 for val in self.state["expedited_return_time"]]
            if self.state["time_to_destination"] > 0:
                self.state["time_to_destination"] -= 1

    def set_destination(self, action, location, travel_time):
        """ Updates agent state when they decide upon an action at a specified location"""

        # update internal state based on decided destination
        self.state["destination"] = location
        self.state["time_to_destination"] = travel_time  # primitive 5 min delay on all actions for now
        self.state["current_action"] = action

    # ACTIONS
    def leave_park(self, time):
        """ Updates agent state when they leave park """

        self.state["within_park"] = False
        self.state["current_location"] = "outside park"
        self.state["current_park_area"] = None
        self.state["destination"] = None
        self.state["time_to_destination"] = 0  # should be idempotent, just for safekeeping
        self.state["current_action"] = None
        self.state["exit_time"] = time
        self.state["time_spent_at_current_location"] = 0
        self.log += f"Agent left park at {time}. "

    def enter_queue(self, attraction, park_area, time):
        """ Updates agent state when they enter an attraction queue """

        self.state["current_location"] = attraction
        self.state["current_park_area"] = park_area
        self.state["destination"] = None
        self.state["time_to_destination"] = 0  # should be idempotent, just for safekeeping
        self.state["current_action"] = "queueing"
        self.state["time_spent_at_current_location"] = 0
        self.log += f"Agent entered queue for {attraction} at time {time}. "

    def enter_exp_queue(self, attraction, park_area, time):
        """ Updates agent state when they enter an attraction's expedited queue """

        self.state["current_location"] = attraction
        self.state["current_park_area"] = park_area
        self.state["destination"] = None
        self.state["time_to_destination"] = 0  # should be idempotent, just for safekeeping
        self.state["current_action"] = "queueing"
        self.state["time_spent_at_current_location"] = 0
        self.log += f"Agent entered exp queue for {attraction} at time {time}. "

    def begin_activity(self, activity, park_area, time):
        """ Updates agent state when they visit an activity """

        self.state["current_location"] = activity
        self.state["current_park_area"] = park_area
        self.state["destination"] = None
        self.state["time_to_destination"] = 0  # should be idempotent, just for safekeeping
        self.state["current_action"] = "browsing"
        self.state["time_spent_at_current_location"] = 0
        self.log += f"Agent visited the activity {activity} at time {time}. "

    def get_pass(self, attraction, park_area, time):
        """ Updates agent state when they get a pass """

        self.state["current_location"] = attraction
        self.state["current_park_area"] = park_area
        self.state["destination"] = None
        self.state["time_to_destination"] = 0  # should be idempotent, just for safekeeping
        self.state["current_action"] = "getting pass"
        self.state["expedited_pass"].append(attraction)
        self.state["time_spent_at_current_location"] = 0
        self.log += (
            f"Agent picked up an expedited pass for {attraction} at time {time}. "
        )

    def assign_expedited_return_time(self, expedited_return_time, current_time):
        """ Updates agent state when they are assigned a return time to their expedited attraction """

        minutes_to_return_time = max(0, expedited_return_time - current_time)
        self.state["expedited_return_time"].append(minutes_to_return_time)
        self.state["current_action"] = "idling"
        self.log += (
            f"The expedited queue return time is in {minutes_to_return_time} minutes. "
        )

    def return_exp_pass(self, attraction):
        """ Updates agent state when they leave park before using the pass """

        ind_to_remove = None
        for ind, attraction_pass in enumerate(self.state["expedited_pass"]):
            if attraction_pass == attraction:
                ind_to_remove = ind

        if ind_to_remove is not None:
            del self.state["expedited_pass"][ind_to_remove]
            del self.state["expedited_return_time"][ind_to_remove]
        else:
            raise ValueError(f"Agent {self.agent_id} hit a snag returning exp pass upon boarding.")

    def agent_exited_attraction(self, name, time):
        """ Update agents state after they leave an attraction """

        # self.state["current_location"] = "gate"  ## removing this because they shouldn't actually leave the area?
        self.state["current_action"] = "idling"
        self.state["attractions"][name]["times_completed"] += 1
        self.state["time_spent_at_current_location"] = 0

        self.log += f"Agent exited {name} at time {time}. "

    def agent_boarded_attraction(self, name, time):
        """ Update agents state after they board an attraction """
        if name in self.state["expedited_pass"]:
            self.return_exp_pass(name)
            # self.state["current_location"] = name  # they should now already be there from enter_queue/enter_exp_queue
            self.state["current_action"] = "riding"
            self.state["time_spent_at_current_location"] = 0
            self.log += (
                f"Agent boarded {name} and redeemed their expedited queue pass at time {time}. "
            )
            return True
        else:
            # self.state["current_location"] = name  # same as above
            self.state["current_action"] = "riding"
            self.state["time_spent_at_current_location"] = 0
            self.log += f"Agent boarded {name} at time {time}. "
            return False

    def agent_exited_activity(self, name, time):
        """ Update agents state after they leave an activity """

        # self.state["current_location"] = "gate"
        self.state["current_action"] = "idling"
        self.state["activities"][name]["times_visited"] += 1
        self.state["activities"][name]["time_spent"] += self.state["time_spent_at_current_location"]
        self.state["time_spent_at_current_location"] = 0
        self.log += f"Agent exited the activity {name} at time {time}. "
