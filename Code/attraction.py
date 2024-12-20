class Attraction:
    """ Class which defines Attractions within the park simulation. Stores attraction characteristics,
    current state and log. """

    def __init__(self, attraction_characteristics):
        """  
        Required Inputs:
            attraction_characteristics: dictionary of characteristics for the attraction        
        """

        self.attraction_characteristics = attraction_characteristics
        self.state = {}  # characterizes attractions current state
        self.history = {}

        if (
                type(self.attraction_characteristics["popularity"]) != int
                or self.attraction_characteristics["popularity"] < 1
                or self.attraction_characteristics["popularity"] > 10
        ):
            raise AssertionError(
                f"Attraction {self.attraction_characteristics['name']} 'popularity' value must be an integer between"
                "1 and 10"
            )

        # characteristics
        self.name = self.attraction_characteristics["name"]
        self.park_area = self.attraction_characteristics["park_area"]
        self.run_time = self.attraction_characteristics["run_time"]
        self.capacity = self.attraction_characteristics["hourly_throughput"] * (
                    self.attraction_characteristics["run_time"] / 60)
        self.popularity = self.attraction_characteristics["popularity"]
        self.child_eligible = self.attraction_characteristics["child_eligible"]
        self.adult_eligible = self.attraction_characteristics["adult_eligible"]
        self.run_time_remaining = 0
        self.expedited_queue = self.attraction_characteristics["expedited_queue"]
        self.exp_queue_ratio = self.attraction_characteristics["expedited_queue_ratio"]
        self.exp_queue_passes = 0

        # state
        self.state["agents_in_attraction"] = []
        self.state["queue"] = []
        self.state["exp_queue"] = []
        self.exp_pass_status = "open" if self.exp_queue_ratio > 0 else "closed"
        self.state["exp_queue_passes_distributed"] = 0
        self.state["exp_queue_passes_skipped"] = 0
        self.state["exp_queue_passes_redeemed"] = 0
        self.state["exp_return_time"] = 0
        self.wait_time = 0
        self.exp_wait_time = 0

        # history
        self.history["queue_length"] = {}
        self.history["queue_wait_time"] = {}
        self.history["exp_queue_length"] = {}
        self.history["exp_queue_wait_time"] = {}
        self.history["exp_return_time"] = {}

    def get_wait_time(self):
        """ Returns the expected queue wait time according to the equation
        """
        return self.wait_time

    def get_exp_wait_time(self):
        """ Returns the expected queue wait time according to the equation
        """
        return self.exp_wait_time

    def get_exp_return_time(self):
        """ Returns the current expedited queue return time according to distribution schedule
        """
        return self.state["exp_return_time"]

    def add_to_queue(self, agent_id):
        """ Adds an agent to the queue """

        self.state["queue"].append(agent_id)

    def add_to_exp_queue(self, agent_id):
        """ Adds an agent to the expedited queue """

        self.state["exp_queue"].append(agent_id)
        expedited_wait_time = self.get_exp_wait_time()
        return expedited_wait_time

    def remove_pass(self):
        """ Removes a expedited pass """

        self.exp_queue_passes -= 1
        self.state["exp_queue_passes_distributed"] += 1

    # TODO: Consider deprecating this method or updating it to not remove agent from queue
    def return_pass(self, agent_id):
        """ Removes an expedited pass without redeeming it """

        self.exp_queue_passes += 1
        self.state["exp_queue_passes_distributed"] -= 1
        self.state["exp_queue"].remove(agent_id)

    def redeem_pass(self):
        """ Redeems a valid expedited pass after agent had it removed. """

        self.state["exp_queue_passes_redeemed"] += 1

    def step(self, time, park_close):
        """ Handles the following actions:
            - Allows agents to exit attraction if the run is complete
            - Loads expedited queue agents
            - Loads queue agents
            - Begins Ride
        """

        exiting_agents = []
        loaded_agents = []

        if self.run_time_remaining == 0:
            # left agents off attraction
            exiting_agents = self.state["agents_in_attraction"]
            self.state["agents_in_attraction"] = []
            self.run_time_remaining = self.run_time

            # devote seats to queue and expedited queue
            max_exp_queue_agents = int(self.capacity * self.exp_queue_ratio)
            # Handle case where expedited queue has fewer agents than the maximum number of expedited queue spots
            if len(self.state["exp_queue"]) < max_exp_queue_agents:
                max_queue_agents = int(self.capacity - len(self.state["exp_queue"]))
            else:
                max_queue_agents = int(self.capacity - max_exp_queue_agents)

            # load expedited queue agents
            expedited_agents_to_load = [agent_id for agent_id in self.state["exp_queue"][:max_exp_queue_agents]]
            self.state["agents_in_attraction"] = expedited_agents_to_load
            self.state["exp_queue"] = self.state["exp_queue"][max_exp_queue_agents:]

            # load queue agents
            agents_to_load = [agent_id for agent_id in self.state["queue"][:max_queue_agents]]
            self.state["agents_in_attraction"].extend(agents_to_load)
            self.state["queue"] = self.state["queue"][max_queue_agents:]

            loaded_agents = self.state["agents_in_attraction"]

        return exiting_agents, loaded_agents

    def pass_time(self):
        """ Pass 1 minute of time """

        self.run_time_remaining -= 1

    def store_history(self, time):
        """ Stores metrics """

        self.history["queue_length"].update(
            {
                time: len(self.state["queue"])
            }
        )
        self.history["queue_wait_time"].update(
            {
                time: self.get_wait_time()
            }
        )
        self.history["exp_queue_length"].update(
            {
                time: len(self.state["exp_queue"])
            }
        )
        self.history["exp_queue_wait_time"].update(
            {
                time: self.get_exp_wait_time()
            }
        )
        self.history["exp_return_time"].update(
            {
                time: self.get_exp_return_time()
            }
        )

    def update_exp_return_window(self, time, close):
        """
        Update the expedited queue return window based on the number of total passes accounted for.
        Inputs:
            :time - current park time (in minutes)
            :close - park close time (in minutes from park open)
        """
        # TODO: Do this after each agent obtains a pass.
        # TODO: Add handling of failed attempt to get pass?  Would the above warrant this?
        # TODO: Update this to be based on current time and num passes not yet redeemed.
        unredeemed_passes = self.state["exp_queue_passes_distributed"] - self.state["exp_queue_passes_redeemed"] - \
            self.state["exp_queue_passes_skipped"]
        minutes_to_process_unredeemed = (unredeemed_passes * self.run_time) / (self.capacity * self.exp_queue_ratio)
        est_time_to_redeem_all = time + minutes_to_process_unredeemed
        min_post_time = max(est_time_to_redeem_all,
                            time + (5 - time % 5),  # rounds up to nearest 5, always > time
                            self.state["exp_return_time"]  # never lower the return window
                            )
        max_post_time = close - 60
        if min_post_time > max_post_time:
            # no more expedited passes for the day
            self.exp_pass_status = "closed"
        elif est_time_to_redeem_all < min_post_time:
            self.state["exp_return_time"] = min_post_time
        else:
            self.state["exp_return_time"] = int(est_time_to_redeem_all + (5 - est_time_to_redeem_all % 5))

    def update_wait_times(self):
        """
        Updates the expected queue wait time according to new equation.  We will update estimated wait times based on the
        assumption that all queues will remain saturated during an agent's time in the queue, and that the ride will
        operate at its theoretical capacity.
        """
        if self.expedited_queue:
            self.wait_time = (len(self.state["queue"]) // (
                        self.capacity * (1 - self.exp_queue_ratio))) * self.run_time + self.run_time_remaining
            self.exp_wait_time = (len(self.state["exp_queue"]) // (
                        self.capacity * self.exp_queue_ratio)) * self.run_time + self.run_time_remaining
        else:
            self.wait_time = (len(self.state["queue"]) // self.capacity) * self.run_time + self.run_time_remaining
