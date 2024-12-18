# TODO

1. Add group dynamics. **[HARD]** Guests usually visit parks in groups and there is a strong bias for groups to do activities together.  The following features should be explored:
 - Group decisioning: Guests should usually make decisions together and visit attractions that everyone can agree on, with the occasional sit-out from a minority of the party
 - Arrive and leave park at same time.  Groups will also almost always stay together and arrivals and departures should coincide.  Very niche addition would be for guests to split up with some pressure to join back together before leaving, although not necessary.

2. Add more detailed ride interactions. **[MED]**  Rides can break down and operate below theoretical capacity.  How does this impact the availability of future priority passes and how does it impact the queues for the rest of the day?

3. Food options can be diversified and can be modeled as FCFS queues themselves. **[MED]**
 - Mobile Orders?
 - - A separate system that guests could use to schedule meal pickup.  Subject to demand as well.
    
4. Add travel time **[LOW-MED]**
   - for starters, we could simply add 5 minutes to account for traveling.
   - more accurate would be to have known distance from current position to all other attractions
5. Update guest utility function to factor in:
- distance of options **[LOW-MED]**
- number of times option has already been done **[LOW-MED]**

6. Intentional Overposting **[LOW to HARD]**
- in order to influence guest flow, overposting can be used to influence which attractions guests will choose.
- guests should always act based on posted wait times and not actual wait times or true estimates.

7. No more than 15 minutes in expedited queue  **[LOW-MED]**
- guests will be upset if they have to wait long in the expedited queue. what mechanism could be implemented to ensure the wait times stay at or below 15 minutes? change split at merge?

8. Log more data at each timestep for on the fly analytics **[LOW]**
- add graphs:
  - Number of Guests in Park by minute/hour of Operating Day
  - Return time vs time of day for each attraction - shows how quickly expedited passes are disbursed

9. Add more expedited systems
- FP+
- TDR system, priority pass + DPA
- - this one would require utility function to consider price as well as time
- Lightning Lane single / multi-pass
- - this one would require utility function to consider price as well as time 
- Universal, Six Flags, Cedar Fair systems 
    
10. Resort-level abstraction
    - if we want, we can make a resort.py object to which parks and hotels belong, and guests can move between them over the length of their stay
    - this would allow for the inclusion of additional behavior like:
        - returning to hotel to relax midday
        - park hopping for resort guests and APs
    

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

