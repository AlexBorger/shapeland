import random
import os
import json
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from tabulate import tabulate

from agent import Agent
from attraction import Attraction
from activity import Activity


class Park:
    """ Park simulation class """

    def __init__(self, attraction_list, activity_list, park_map, entrance_park_area, plot_range, version=1.0,
                 random_seed=0, verbosity=0):
        """ 
        Required Inputs:
            attraction_list: list of attractions dictionaries
            activity_list: list of activity dictionaries
            park_map: dictionary of source -> destination park area distances (minutes)
        Optional Inputs:
            random_seed: seeds random number generation for reproduction
            version: specify the version
            verbosity: display metrics
        """

        # static
        self.attraction_list = attraction_list
        self.activity_list = activity_list
        self.park_map = park_map
        self.entrance_park_area = entrance_park_area
        self.plot_range = plot_range
        self.random_seed = random_seed
        self.version = version
        self.verbosity = verbosity

        # dynamic
        self.schedule = {}
        self.agents = {}
        self.attractions = {}
        self.activities = {}
        self.history = {"total_active_agents": {}, "total_left_agents": {}, "distributed_passes": 0,
                        "redeemed_passes": 0}
        self.time = 0
        self.arrival_index = 0
        self.active_agents = 0
        self.left_agents = 0
        self.park_close = None
    
    def generate_arrival_schedule(self, arrival_seed, total_daily_agents, perfect_arrivals):
        """ 
        Builds a schedule that determines how many agents arrive each minute throughout the day.
        Each minute of the day is assigned from a Poisson distribution. A Poisson distribution generally
        characterizes arrivals in many different settings. It is good to use if the arrivals are all
        random and independent of each other.

        Required Inputs:
            arrival_seed: Dictionary of arrival distributions
            total_daily_agents: Total agents visiting during the day
        Optional Inputs:
            perfect_arrivals: Enforces the exact number of daily agents to visit
        """

        if sum(arrival_seed.values()) != 100:
            raise AssertionError(
                "The percent of hourly arrivals does not add up to 100%"
            )

        # determine how many hours the park is open
        operating_hours = len(arrival_seed)
        if operating_hours > 24:
            raise AssertionError(f"Arrival Schedule suggests park is open more than 24 hours ({operating_hours})")
        last_hour_key = list(arrival_seed.keys())[-1]
        if arrival_seed[last_hour_key] != 0:
            last_hour_arrivals = arrival_seed[last_hour_key]
            raise AssertionError(f"Arrival Schedule suggests closing hour has nonzero arrivals: {last_hour_arrivals}")

        self.park_close = (len(arrival_seed) - 1) * 60  # last hour entry is closing time, don't count it

        # generate arrivals per minute by drawing from poisson distribution
        for hour, key in zip(range(operating_hours), arrival_seed):
            arrival_pct = arrival_seed[key]

            total_hour_agents = total_daily_agents * arrival_pct * 0.01  # convert integer pct to decimal
            expected_minute_agents = total_hour_agents/60

            # enforces randomness across hours but retains reproducibility
            rng = np.random.default_rng(self.random_seed+hour) 
            minute_arrivals = list(rng.poisson(lam=expected_minute_agents, size=60))

            for minute, arrivals in zip(range(60), minute_arrivals):
                exact_minute = hour*60 + minute
                self.schedule.update({exact_minute: arrivals})
        
        # enforce perfect arrivals
        random.seed(self.random_seed)
        if perfect_arrivals:
            actual_total_daily_agents = sum(self.schedule.values())
            dif = actual_total_daily_agents - total_daily_agents
            if dif > 0:
                for _ in range(dif):
                    rng_key = random.choice(list(key for key, val in self.schedule.items() if val>0))
                    self.schedule[rng_key] -= 1
            if dif < 0:
                for _ in range(dif*-1):
                    rng_key = random.choice(list(key for key, val in self.schedule.items() if val>0))
                    self.schedule[rng_key] += 1
                    
            assert sum(self.schedule.values()) == total_daily_agents

    def generate_agents(self, behavior_archetype_distribution, exp_ability_pct, exp_wait_threshold, exp_limit):
        """ Take a dictionary of agent behavior archetype distributions. Initializes agents. """

        if sum(behavior_archetype_distribution.values()) != 100:
            raise AssertionError(
                "The percent of behavior archetypes does not add up to 100%"
            )

        total_agents = sum(self.schedule.values())
        for agent_id in range(total_agents):
            random.seed(self.random_seed + agent_id)
            exp_ability = random.uniform(0, 1) < exp_ability_pct

            agent = Agent(random_seed=self.random_seed)
            agent.initialize_agent(
                agent_id=agent_id,
                behavior_archetype_distribution=behavior_archetype_distribution,
                exp_ability=exp_ability,
                exp_wait_threshold=exp_wait_threshold,
                exp_limit=exp_limit,
                attraction_names=[attraction["name"] for attraction in self.attraction_list], 
                activity_names=[activity["name"] for activity in self.activity_list], 
            ) 
            self.agents.update({agent_id: agent})

    def generate_attractions(self):
        """ Initializes attractions """

        self.attraction_list = sorted(self.attraction_list, key=lambda k: k['popularity']) 
        for attraction in self.attraction_list:
            self.attractions.update(
                {
                    attraction["name"]: Attraction(attraction_characteristics=attraction)
                }
            )
    
    def generate_activities(self):
        """ Initializes activities """

        self.activity_list = sorted(self.activity_list, key=lambda k: k['popularity']) 
        for activity in self.activity_list:
            self.activities.update(
                {
                    activity["name"]: Activity(activity_characteristics=activity, random_seed=self.random_seed)
                }
            )

    def step(self):
        """ A minute of time passes, update all agents and attractions. """

        if self.time < self.park_close:
            # allow new arrivals to enter
            total_arrivals = self.schedule[self.time]
            for new_arrival_index in range(total_arrivals):
                agent_index = self.arrival_index + new_arrival_index
                self.agents[agent_index].arrive_at_park(time=self.time, park_area=self.entrance_park_area)

            self.arrival_index += total_arrivals

        # get idle agents and agents en route to a destination
        idle_agent_ids = self.get_idle_agent_ids()

        # update attraction posted wait times and expedited queue return times
        for attraction_name, attraction in self.attractions.items():
            attraction.update_wait_times()
            attraction.update_exp_return_window(time=self.time, close=self.park_close)

        # get idle activity action
        for agent_id in idle_agent_ids:
            # does the park object really need these action/location values? or is it just an orchestrator that should
            # let the agents sort out their own internal state...?
            agent = self.agents[agent_id]
            action, location = agent.make_state_change_decision(
                attractions_dict=self.attractions,
                activities_dict=self.activities,
                time=self.time,
                park_map=self.park_map,
                park_closed=self.park_close <= self.time
            )
            # determine travel time to new destination
            current_park_area = agent.state["current_park_area"]
            if location in self.attractions:
                destination_park_area = self.attractions[location].park_area
            elif location in self.activities:
                destination_park_area = self.activities[location].park_area
            elif location == 'gate':
                destination_park_area = self.entrance_park_area
            else:
                raise ValueError(f"Agent cannot travel to location {location}.  Unknown park area mapping.")
            travel_time = self.park_map[current_park_area][destination_park_area]
            agent.set_destination(action, location, travel_time)

        # all agents that are now ready to take a delayed action should now be processed.
        # either: (a) agent is not at their next location and we (later) subtract 1 min from time_to_destination, or
        # (b) they reached destination and we will now process them exactly as we would have before.
        reached_destination_agent_ids = self.get_reached_destination_agent_ids()
        for agent_id in reached_destination_agent_ids:
            self.update_park_state(
                agent=self.agents[agent_id],
                time=self.time
            )
            
        # process attractions
        for attraction_name, attraction in self.attractions.items():
            exiting_agents, loaded_agents = attraction.step(time=self.time, park_close=self.park_close)
            for agent_id in exiting_agents:
                self.agents[agent_id].agent_exited_attraction(name=attraction_name, time=self.time)
            for agent_id in loaded_agents:
                if self.agents[agent_id].state["current_action"] == "browsing":
                    # force exit if expedited queue estimate was too high
                    self.activities[self.agents[agent_id].state["current_location"]].force_exit(agent_id=agent_id)
                    self.agents[agent_id].agent_exited_activity(
                        name=self.agents[agent_id].state["current_location"],
                        time=self.time
                    )
                redeem = self.agents[agent_id].agent_boarded_attraction(name=attraction_name, time=self.time)
                if redeem:
                    self.history["redeemed_passes"] += 1
                    attraction.redeem_pass()

        # process activities
        for activity_name, activity in self.activities.items():
            exiting_agents = activity.step(time=self.time)
            for agent_id in exiting_agents:
                self.agents[agent_id].agent_exited_activity(name=activity_name, time=self.time)

        # update time counters and history
        for agent in self.agents.values():
            agent.pass_time()
        for attraction in self.attractions.values():
            attraction.pass_time()
            attraction.store_history(time=self.time)
        for activity in self.activities.values():
            activity.pass_time()
            activity.store_history(time=self.time)

        # update own history
        self.calculate_total_active_agents()
        self.history["total_left_agents"].update({self.time: self.left_agents})

        if self.verbosity == 1 and self.time % 60 == 0:
            self.print_metrics()
        if self.verbosity == 2:
            self.print_metrics()

        self.time += 1

    def get_idle_agent_ids(self):
        """ Identifies agents within park who have just arrived, who have exited a ride or who have left an activity """

        idle_agent_ids = [
            agent_id for agent_id, agent_dict in self.agents.items()
            if agent_dict.state["within_park"] and agent_dict.state["current_action"] == "idling"
        ]

        return idle_agent_ids

    def get_reached_destination_agent_ids(self):
        """ Identifies agents within park who have reached their destination where they will take an action that they
        previously chose.  Currently, actions that require agent cooldown (agent.state["time_to_destination"] > 0) are:
            - leaving
            - traveling (either to attraction or activity)
            - redeeming exp pass
            - get pass
        """

        reached_destination_agent_ids = [
            agent_id for agent_id, agent_dict in self.agents.items()
            if agent_dict.state["within_park"]
            and agent_dict.state["current_action"] in ["leaving", "traveling", "redeeming exp pass", "get pass"]
            and agent_dict.state["time_to_destination"] == 0
        ]

        return reached_destination_agent_ids
    
    def update_park_state(self, agent, time):
        """ Updates the agent state, attraction state and activity state based on the action """

        if agent.state["time_to_destination"] > 0:
            raise ValueError(f"Agent {agent.agent_id} reached update_park_state before reaching destination.")

        action = agent.state["current_action"]
        location = agent.state["destination"]

        if action == "leaving":
            # TODO: Determine if we should be forfeiting an exp pass because we left the park
            # if agent.state["expedited_pass"]:
            #    for attraction in agent.state["expedited_pass"]:
            #        self.attractions[attraction].return_pass(agent.agent_id)
            #        agent.return_exp_pass(attraction=attraction)
            agent.leave_park(time=time)
            self.left_agents += 1

        if action == "traveling":
            if location in self.attractions:
                park_area = self.attractions[location].park_area
                agent.enter_queue(attraction=location, park_area=park_area, time=time)
                self.attractions[location].add_to_queue(agent_id=agent.agent_id)

            if location in self.activities:
                park_area = self.activities[location].park_area
                agent.begin_activity(activity=location, park_area=park_area, time=time)
                self.activities[location].add_to_activity(
                    agent_id=agent.agent_id,
                    expedited_return_time=agent.state["expedited_return_time"]
                )

        if action == "redeeming exp pass":
            if location not in self.attractions:
                raise ValueError(f"Tried to redeem exp pass at non-attraction location: {location}")
            park_area = self.attractions[location].park_area
            agent.enter_exp_queue(attraction=location, park_area=park_area, time=time)
            self.attractions[location].add_to_exp_queue(agent_id=agent.agent_id)

        # TODO: Figure out what to do with this part... where should they go? set park entrance area?
        if action == "get pass":
            park_area = self.attractions[location].park_area
            agent.get_pass(attraction=location, park_area=park_area, time=time)
            self.attractions[location].remove_pass()
            expedited_return_time = self.attractions[location].get_exp_return_time()
            agent.assign_expedited_return_time(expedited_return_time=expedited_return_time, current_time=time)
            self.history["distributed_passes"] += 1

    def calculate_total_active_agents(self):
        """ Counts how many agents are currently active within the park """

        active_agents = len([agent_id for agent_id, agent in self.agents.items() if agent.state["within_park"]])
        self.active_agents = active_agents
        self.history["total_active_agents"].update({self.time: active_agents})

    def print_metrics(self):
        """ Prints park metrics """

        print(f"Time: {self.time}")
        print(f"Total Agents in Park: {self.history['total_active_agents'][self.time]}")
        print(f"Attraction Wait Times (Minutes):")
        for attraction_name, attraction in self.attractions.items():
            print(f"     {attraction_name}: {attraction.history['queue_wait_time'][self.time]}")
        print(f"Activity Visitor (Agents):")
        for activity_name, activity in self.activities.items():
            print(f"     {activity_name}: {activity.history['total_vistors'][self.time]}")
        print(f"{'-'*50}\n")

    @staticmethod
    def make_lineplot(dict_list, x, y, hue, title, location, show=False, y_max=None):
        """ Create a hued lineplot derived from a list of dictionaries """
        
        df = pd.DataFrame(dict_list)
        l = [time for ind, time in enumerate(list(df['Time'].unique())) if ind % 60 == 0]
        plt.figure(figsize=(15,8))
        ax = sns.lineplot(data=df, x=x, y=y, hue=hue)
        ax.set(xticks=l, xticklabels=l, title=title)
        ax.tick_params(axis='x', rotation=45)
        if y_max:
            if y_max == 'auto':
                auto_y_max = round(1.1 * max(df[y]))  # add 10% empty space above max data point
                auto_y_max = max(auto_y_max, max(df[y]) + 1)  # for small values, 10% may round down. add 1 as buffer
                ax.set(ylim=(0, auto_y_max))
            else:
                ax.set(ylim=(0, y_max))
        plt.savefig(location, transparent=False, facecolor="white", bbox_inches="tight")
        plt.savefig(f"{location} Transparent", transparent=True, bbox_inches="tight")
        plt.show()
        if not show:
            plt.close()
    
    @staticmethod
    def make_histogram(dict_list, x, title, location, show=False):
        """ Create a histogram derived from a list of dictionaries """
        
        df = pd.DataFrame(dict_list)
        l = sorted(list(set(val for val in df[x])))
        plt.figure(figsize=(15, 8))
        ax = sns.histplot(data=df, x=x, stat="percent", bins=np.arange(-0.5, len(l)))  # weird trick to align labels
        ax.set(title=title, xticks=l, xticklabels=l)
        plt.savefig(location, transparent=False, facecolor="white", bbox_inches="tight")
        plt.savefig(f"{location} Transparent", transparent=True, bbox_inches="tight")
        plt.show()
        if show:
            disp_df = pd.DataFrame(df[x].describe()).reset_index()
            disp_df.columns = ["Metric", x]
            print(
                tabulate(
                    disp_df, 
                    headers='keys', 
                    tablefmt='psql', 
                    showindex=False,
                    floatfmt='.2f'
                )
            )
        if not show:
            plt.close()
    
    @staticmethod
    def make_barplot(dict_list, x, y, hue, y_max, title, location, estimator=None, show=False):
        """ Create a hued barplot derived from a list of dictionaries """

        df = pd.DataFrame(dict_list)
        plt.figure(figsize=(15, 8))
        if estimator:
            ax = sns.barplot(data=df, x=x, y=y, hue=hue, ci=None, estimator=estimator)
        else:
            ax = sns.barplot(data=df, x=x, y=y, hue=hue)
        ax.set(title=title)
        if y_max:
            if y_max == 'auto':
                if not estimator:  # estimator is used when dataset is more granular than viz.  if estimator, sns auto.
                    auto_y_max = round(1.1 * max(df[y]))
                    auto_y_max = max(auto_y_max, max(df[y]) + 1)  # for small values, 10% may round down. add 1 as pad
                    ax.set(ylim=(0, auto_y_max))
            else:
                ax.set(ylim=(0, y_max))
        plt.savefig(location, transparent=False, facecolor="white", bbox_inches="tight")
        plt.savefig(f"{location} Transparent", transparent=True, bbox_inches="tight")
        plt.show()
        if show and not estimator:
            print(
                tabulate(
                    df.sort_values(hue), 
                    headers='keys', 
                    tablefmt='psql', 
                    showindex=False,
                    floatfmt='.2f'
                )
            )
        if show and estimator == sum:
            print(
                tabulate(
                    df.groupby(x).sum().reset_index(),
                    headers='keys', 
                    tablefmt='psql', 
                    showindex=False,
                )
            )
        if not show:
            plt.close()

    def make_plots(self, show=False):
        """ Plots key park information, save to version folder """

        version_path = os.path.join(f"{self.version}")
        if not os.path.exists(version_path):
            os.mkdir(version_path)

        # Attractions
        queue_length = []
        queue_wait_time = []
        exp_queue_length = []
        exp_queue_wait_time = []
        exp_queue_return_time = []
        for attraction_name, attraction in self.attractions.items():
            for time, val in attraction.history["queue_length"].items():
                queue_length.append({"Time": time, "Agents": val, "Attraction": attraction_name})
            for time, val in attraction.history["queue_wait_time"].items():
                queue_wait_time.append({"Time": time, "Minutes": val, "Attraction": attraction_name})
            for time, val in attraction.history["exp_queue_length"].items():
                exp_queue_length.append({"Time": time, "Agents": val, "Attraction": attraction_name})
            for time, val in attraction.history["exp_queue_wait_time"].items():
                exp_queue_wait_time.append({"Time": time, "Minutes": val, "Attraction": attraction_name})
            for time, val in attraction.history["exp_return_time"].items():
                exp_queue_return_time.append({"Time": time, "Expedited Queue Return Time": val,
                                              "Attraction": attraction_name})
        
        avg_queue_wait_time = []
        for attraction_name, attraction in self.attractions.items():
            queue_wait_list = [
                val for time, val in attraction.history["queue_wait_time"].items()
                if time <= self.park_close
            ]
            exp_queue_wait_list = [
                val for time, val in attraction.history["exp_queue_wait_time"].items()
                if time <= self.park_close
            ]
            avg_queue_wait_time.append(
                {
                    "Attraction": attraction_name,
                    "Average Wait Time": sum(queue_wait_list)/len(queue_wait_list),
                    "Queue Type": "Standby"
                }
            )
            avg_queue_wait_time.append(
                {
                    "Attraction": attraction_name,
                    "Average Wait Time": sum(exp_queue_wait_list)/len(exp_queue_wait_list),
                    "Queue Type": "Expedited"
                }
            )

        # Activities
        total_vistors = []
        for activity_name, activity in self.activities.items():
            for time, val in activity.history["total_vistors"].items():
                total_vistors.append({"Time": time, "Agents": val, "Activity": activity_name})

        # Agent Distribution
        broad_agent_distribution = []
        specific_agent_distribution = []
        park_population = []
        for time, total_agents in self.history["total_active_agents"].items():
            broad_agent_distribution.append(
                {
                    "Time": time,
                    "Approximate Percent": sum(
                        [attraction.history["queue_length"][time] for attraction in self.attractions.values()]
                    )/total_agents if total_agents > 0 else 0,
                    "Type": "Attractions"
                }
            )
            broad_agent_distribution.append(
                {
                    "Time": time,
                    "Approximate Percent": sum(
                        [activity.history["total_vistors"][time] for activity in self.activities.values()]
                    )/total_agents if total_agents > 0 else 0,
                    "Type": "Activities"
                }
            )
            park_population.append(
                {
                    "Time": time,
                    "Agents": total_agents,
                    "Type": "In Park"
                }
            )
            park_population.append(
                {
                    "Time": time,
                    "Agents": self.history["total_left_agents"][time],
                    "Type": "Left Park"
                }
            )
            park_population.append(
                {
                    "Time": time,
                    "Agents": total_agents + self.history["total_left_agents"][time],
                    "Type": "Total"
                }
            )
            # Specific agent distribution
            for attraction_name, attraction in self.attractions.items():
                specific_agent_distribution.append(
                    {
                        "Time": time,
                        "Approximate Percent": attraction.history["queue_length"][time]/total_agents if total_agents > 0 else 0,
                        "Type": attraction_name
                    }
                )
            for activity_name, activity in self.activities.items():
                specific_agent_distribution.append(
                    {
                        "Time": time,
                        "Approximate Percent": activity.history["total_vistors"][time]/total_agents if total_agents > 0 else 0,
                        "Type": activity_name
                    }
                )

        attraction_counter = []
        attraction_density = []
        for agent_id, agent in self.agents.items():
            attraction_counter.append(
                {
                    "Agent": agent_id,
                    "Behavior": agent.behavior["archetype"],
                    "Total Attractions Visited": sum(
                        attraction['times_completed'] for attraction in agent.state["attractions"].values()
                    )
                }
            )
            for attraction, attraction_dict in agent.state["attractions"].items():
                attraction_density.append(
                    {
                        "Attraction": attraction,
                        "Visits": attraction_dict["times_completed"]
                    }
                )

        self.make_lineplot(
            dict_list=queue_length, 
            x="Time", 
            y="Agents", 
            hue="Attraction",
            y_max=self.plot_range["Attraction Queue Length"], 
            title="Attraction Queue Length",
            location=f"{self.version}/Attraction Queue Length",
            show=show,
        )

        self.make_lineplot(
            dict_list=queue_wait_time, 
            x="Time", 
            y="Minutes", 
            hue="Attraction",
            y_max=self.plot_range["Attraction Wait Time"],  
            title="Attraction Wait Time",
            location=f"{self.version}/Attraction Wait Time",
            show=show,
        )

        self.make_lineplot(
            dict_list=exp_queue_length, 
            x="Time", 
            y="Agents", 
            hue="Attraction",
            y_max=self.plot_range["Attraction Expedited Queue Length"],  
            title="Attraction Expedited Queue Length",
            location=f"{self.version}/Attraction Expedited Queue Length",
            show=show,
        )

        self.make_lineplot(
            dict_list=exp_queue_wait_time, 
            x="Time", 
            y="Minutes", 
            hue="Attraction",
            y_max=self.plot_range["Attraction Expedited Wait Time"],  
            title="Attraction Expedited Wait Time",
            location=f"{self.version}/Attraction Expedited Wait Time",
            show=show,
        )

        self.make_lineplot(
            dict_list=exp_queue_return_time,
            x="Time",
            y="Expedited Queue Return Time",
            hue="Attraction",
            y_max=self.plot_range["Attraction Expedited Queue Return Times"],
            title="Attraction Expedited Queue Return Times",
            location=f"{self.version}/Attraction Expedited Queue Return Times",
            show=show,
        )

        self.make_lineplot(
            dict_list=total_vistors, 
            x="Time", 
            y="Agents", 
            hue="Activity",
            y_max=self.plot_range["Activity Vistors"],  
            title="Activity Vistors",
            location=f"{self.version}/Activity Vistors",
            show=show,
        )

        self.make_lineplot(
            dict_list=broad_agent_distribution, 
            x="Time", 
            y="Approximate Percent", 
            hue="Type",
            y_max=self.plot_range["Approximate Agent Distribution (General)"],  
            title="Approximate Agent Distribution (General)",
            location=f"{self.version}/Approximate Agent Distribution (General)",
            show=show,
        )

        self.make_lineplot(
            dict_list=specific_agent_distribution, 
            x="Time", 
            y="Approximate Percent", 
            hue="Type",
            y_max=self.plot_range["Approximate Agent Distribution (Specific)"],  
            title="Approximate Agent Distribution (Specific)",
            location=f"{self.version}/Approximate Agent Distribution (Specific)",
            show=show,
        )

        self.make_lineplot(
            dict_list=park_population,
            x="Time",
            y="Agents",
            hue="Type",
            y_max=self.plot_range["Agent Arrivals and Departures"],
            title="Agent Arrivals and Departures",
            location=f"{self.version}/Agent Arrivals and Departures",
            show=show
        )

        self.make_barplot(
            dict_list=avg_queue_wait_time,
            x="Attraction",
            y="Average Wait Time",
            hue="Queue Type",
            y_max=self.plot_range["Attraction Average Wait Times"],
            title="Attraction Average Wait Times",
            location=f"{self.version}/Attraction Average Wait Times",
            show=show
        )

        self.make_histogram(
            dict_list=attraction_counter, 
            x="Total Attractions Visited",
            title="Agent Attractions Histogram",
            location=f"{self.version}/Agent Attractions Histogram",
            show=show
        )

        self.make_barplot(
            dict_list=attraction_density,
            x="Attraction",
            y="Visits",
            hue=None,
            y_max=self.plot_range["Attraction Total Visits"],
            estimator=sum,
            title="Attraction Total Visits",
            location=f"{self.version}/Attraction Total Visits",
            show=show
        )

        self.make_barplot(
            dict_list=[
                {   
                    "Expedited Passes": " ",
                    "Total Passes": self.history["distributed_passes"],
                    "Type": "Distributed"
                },
                {
                    "Expedited Passes": " ",
                    "Total Passes": self.history["redeemed_passes"],
                    "Type": "Redeemed"
                }
            ], 
            x="Expedited Passes", 
            y="Total Passes",
            hue="Type", 
            y_max=self.plot_range["Expedited Pass Distribution"],
            title="Expedited Pass Distribution", 
            location=f"{self.version}/Expedited Pass Distribution", 
            show=show
        )
        self.make_barplot(
            dict_list= [
                {   
                    "Age Class": " ",
                    "Agents": len([agent_id for agent_id, agent in self.agents.items() if agent.state["age_class"] == "no_child_rides"]),
                    "Type": "No Child Rides"
                },
                {
                    "Age Class": " ",
                    "Agents": len([agent_id for agent_id, agent in self.agents.items() if agent.state["age_class"] == "no_adult_rides"]),
                    "Type": "No Adult Rides"
                },
                {
                    "Age Class": " ",
                    "Agents": len([agent_id for agent_id, agent in self.agents.items() if agent.state["age_class"] == "no_preference"]),
                    "Type": "No Preference"
                },
            ], 
            x="Age Class", 
            y="Agents",
            hue="Type", 
            y_max=self.plot_range["Age Class Distribution"],
            title="Age Class Distribution", 
            location=f"{self.version}/Age Class Distribution", 
            show=show
        )

    def print_logs(self, N=None, selected_agent_ids=None):
        """ Prints the logs of random agents or a list of agents """

        if N:
            all_agent_ids = list(self.agents.keys())
            random.seed(self.random_seed)
            selected_agent_ids = random.sample(all_agent_ids, N)
        for agent_id in selected_agent_ids:
            print(f"Agent ID: {agent_id}")
            print(f"Agent Archetype: {self.agents[agent_id].behavior['archetype']}")
            print(f"{self.agents[agent_id].log}\n")

    @staticmethod
    def write_data_to_file(data, output_file_path, output_file_format):
        """ Takes a data object, writes and saves as a pickle or json. """

        full_path = output_file_path + "." + output_file_format
        if isinstance(full_path, str):
            if output_file_format not in {"json"}:
                raise ValueError(f"Incompatible file format :{output_file_format}")
            # Create folder if not already present
            folder = os.path.dirname(full_path)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)
            mode = "wt"
            file_writer = open(full_path, mode)
        else:
            raise ValueError("full_path must be specified")

        writers = {
            "json": lambda file_writer: json.dump(data, file_writer, indent=2),
        }
        writers[output_file_format](file_writer)
        file_writer.close()