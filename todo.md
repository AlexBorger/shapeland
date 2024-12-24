# TODO

1. Add group dynamics. **[HARD]** Guests usually visit parks in groups and there is a strong bias for groups to do activities together.  The following features should be explored:
   - Group decisioning: Guests should usually make decisions together and visit attractions that everyone can agree on, with the occasional sit-out from a minority of the party
        - One agent can be identified as the lead agent that takes care of make_state_change_decision on behalf of the entire group.   
   - Arrive and leave park at same time.  Groups will also almost always stay together and arrivals and departures should coincide.  Very niche addition would be for guests to split up with some pressure to join back together before leaving, although not necessary.

2. Add more detailed ride interactions. **[MED]**  Rides can break down and operate below theoretical capacity.  How does this impact the availability of future priority passes and how does it impact the queues for the rest of the day?
   - Break up dispatches into ride vehicles whose total throughput matches attraction config  **[DONE]**
   - Define ride vehicle dimensions and fill vehicles based on group sizes
      - Blocked on #1.
   - Attraction breakdowns and slowness
      - with some probability at each timestep, attraction can experience a slight delay, or
      - a complete breakdown requiring evacs, queue dump and agent compensation in terms of free exp passes
         - can specify rules of redemption like which attractions are eligible, time window, etc
      - these can be specified by float parameters at attraction init, like "reliability_factor" or "breakdown_probability"

3. Food options can be diversified and can be modeled as FCFS queues themselves. **[MED]**
   - We could model each food location with a queue and specify average time to eat/drink items from that location.
     - e.g., a popcorn stand might have a long line but takes little time to eat, but a table service meal could be the opposite.
   - Mobile Orders?
     - A separate system that guests could use to schedule meal pickup.  Subject to demand as well.
    
4. Add travel time **[LOW-MED] [MOSTLY DONE]**
   - for starters, we could simply add 5 minutes to account for traveling.  **[DONE]**
     - agents now have two additional state fields, "destination" and "time_to_destination". 
     - with this change, the main park step() method only processes actions for agents that have reached their destination.  with this update, all actions (get exp pass, go to redeem exp pass, visit attraction's standby queue, leave park) all take 5 minutes to do.
     - Once an agent's time_to_destination reaches zero (i.e., they reached it) they will proceed with their action as they would have previously, and each of those actions then reset destination to None and time_to_destination to 0.
   - more accurate would be to have known distance from current position to all other attractions **[DONE]**
     - For simplicity, we can add "park_area" as an attribute for each attraction and activity, and only build a representation of distances between areas instead of each attraction/activity.
   - even more accurate would be to place POIs within park area and differentiate travel times within park area
   - even even more accurate would be to build an actual network of pathways that agents have to navigate to reach their destination.  they may or may not know the optimal path, so algorithmic path routing would need to take that into account.  **[TO DO]** **[VERY HARD]**
5. Update guest utility function to factor in:
   - distance of options **[LOW-MED]**
      - simple version: **[DONE]**
   - number of times option has already been done **[LOW-MED]**
      - simple version: **[DONE]**

6. Intentional Overposting **[LOW to HARD]**
   - in order to influence guest flow, overposting can be used to influence which attractions guests will choose.
   - guests should always act based on posted wait times and not actual wait times or true estimates.
   - while this mechanism is not blocked on other work, usefulness is related to analysis of actual vs posted and attraction slowness/breakdowns

7. No more than 15 minutes in expedited queue  **[LOW-MED]**
   - guests will be upset if they have to wait long in the expedited queue. what mechanism could be implemented to ensure the wait times stay at or below 15 minutes? change split at merge?
      - Note: As of now, exp queue wait times are naturally low even on busy days.  This wouldn't be necessary until we account for 
8. Log more data at each timestep for on the fly analytics **[LOW]**
   - log internal estimate / posted wait times per agent+attraction and actual wait times
      - this can then be used to analyze how frequently agents experience overposts/underposts and the extent of each
   - add graphs:
      - Number of Guests in Park by minute/hour of Operating Day **[DONE]**
      - Return time vs time of day for each attraction - shows how quickly expedited passes are distributed **[DONE]**
   - figure out why agents show as doing activities after park close **[LOW]**
   - analyze agent outcomes by archetype
      - how many attractions do they do? each archetype will have its own distribution  **[LOW]**
   - analyze average number of attractions+activities done
   - analyze ride efficiency expressed in both actual vs theoretical capacity and dispatch capacity
   - analyze percent of day agents have 1+ exp passes in hand, or plot time vs # agents with no exp pass in hand
   - analyze number of exp passes redeemed / abandoned by archetype

9. Add more expedited systems
   - FP+
   - TDR system, priority pass + DPA
      - this one would require utility function to consider price as well as time
   - Lightning Lane single / multi-pass
      - this one would require utility function to consider price as well as time 
   - Universal, Six Flags, Cedar Fair systems 
    
10. World-level abstraction
    - if we want, we can make a world.py object to which parks and hotels belong, and guests can move between them over the length of their stay
    - this would allow for the inclusion of additional behavior like:
      - returning to hotel to relax midday
      - park hopping for resort guests and APs
    - We can create a hotel-level abstraction called hotel.py or resort.py that has its own amenities
      - Each resort can have multiple transportation methods to other resorts and parks
    
11. Agent Satisfaction
    - If we collect how many attractions / activities an agent wanted to do as well as what they accomplished by park close, we can create a formula to output a CSAT score (out of 10)
    - Can factor in things like:
       - how often their actual wait times were less/more than posted
       - if they got to do their most sought-after attractions
       - attraction breakdowns
    

side note - the following are all addressed in Disney's FastPass: A Complicated History @ 1:02:00 :

"The simulation does not take into account walking or attraction distance.
 Guests teleport everywhere and don't consider distance when making decisions.
 However, walking times are simulated as an activity.

 Guests do not have attractions that they want to do before entering the park.
 All attraction decisions are made based on a popularity weighted die roll, with checks
 for balking point and adult/child eligibility.
 
 Guests do not leave for any reason other than their stay time preference has been met.
 
 Guests cannot leave and reenter the park.
 
 Guests travel and think independently.  No pairs or groups.

 Attractions never experience downtime.

 The standby wait times are exact and not inflated.

 There is only one park so no park hopping because my god I don't even want to think about what that does to the data."
 
... so most of the items in this TODO are already acknowledged by shapeland's creators.

At 1:02:18, Kevin adds the following disclaimer about FP+:

"
Dear Nerds,
The simulation is built on a paper FastPass system, so simulating 
FastPass Plus was done in a rather "hacky" way.  Essentially, instead
of giving guests the ability to book in advance, we gave guests the
ability to hold three FastPasses at a time, and rather than only choose
to grab a FastPass if the standby wait was over 30 minutes, guests grab
a FastPass immediately if available.  This simulates the speed that
FastPass Plus reservations filled.  Essentially, this gives priority to early
risers rather than resort guests, but it shouldn't skew results as we
are only viewing distribution effects on a macro park scale, not a micro
individual guest scale.  Also, the three FastPass number is a
rolling number, so guests do not need to wait until they've redeemed
all three to receive another.  However, reservations fill up so fast anyways
that the effects of this are minimal.
"

... it would be interesting to see how addressing some of these points affect
guests at the individual level.  Would the simulation's outcome differ enough
from the Defunctland video to warrant conversation?  We shall see.

