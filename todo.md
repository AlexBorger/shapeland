# TODO

1. Add group dynamics. **[HARD]** Guests usually visit parks in groups and there is a strong bias for groups to do activities together.  The following features should be explored:
 - Group decisioning: Guests should usually make decisions together and visit attractions that everyone can agree on, with the occasional sit-out from a minority of the party
 - Arrive and leave park at same time.  Groups will also almost always stay together and arrivals and departures should coincide.  Very niche addition would be for guests to split up with some pressure to join back together before leaving, although not necessary.

2. Add more detailed ride interactions. **[MED]**  Rides can break down and operate below theoretical capacity.  How does this impact the availability of future priority passes and how does it impact the queues for the rest of the day?

3. Food options can be diversified and can be modeled as FCFS queues themselves. **[MED]**
 - Mobile Orders?
 - - A separate system that guests could use to schedule meal pickup.  Subject to demand as well.
    
4. Add travel time **[LOW-MED]**
5. Update guest utility function to factor in:
- distance of options **[LOW-MED]**
- number of times option has already been done **[LOW-MED]**

6. Intentional Overposting **[LOW to HARD]**
- in order to influence guest flow, overposting can be used to influence which attractions guests will choose.
- guests should always act based on posted wait times and not actual wait times or true estimates.

7. No more than 15 minutes in expedited queue  **[LOW-MED]**
- guests will be upset if they have to wait long in the expedited queue. what mechanism could be implemented to ensure the wait times stay at or below 15 minutes? change split at merge?

8. Log more data at each timestep for on the fly analytics **[LOW]**