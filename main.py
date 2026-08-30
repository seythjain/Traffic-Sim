from utils import randomGraph
import random

class IntersectionManyWay:
    def __init__(self,
                 #            Intersection:

                 #              Backward
                 #                  |
                 #                  v
                 #     Right -->          <-- Left
                 #                  ^
                 #                  |
                 #              Forward
                id = 0,
                Directions = None,
                threshold = 0,
                waitTotal = 0,
                carsMaxAdd = 3, # noise
                c = 1.1,
                ts = 0
                 ):
        self.id = id
        # NOTE: built fresh per-instance instead of as a default arg, otherwise
        # every intersection in the graph would share the exact same dicts
        # red_duration: how many consecutive timesteps this direction has
        # been red. Used so cars that have waited longer weigh more heavily
        # in wait_score, instead of only queue size mattering.
        self.directions = Directions if Directions is not None else [
            {"name" : "Left", "partner_dir": "Right", "light_val": True, "waiting_cars": 0, "wait_score": 0, "red_duration": 0, "connection": None },
            {"name" : "Right", "partner_dir": "Left", "light_val": True, "waiting_cars": 0, "wait_score": 0, "red_duration": 0, "connection": None },
            {"name" : "Forward", "partner_dir": "Backward", "light_val": False, "waiting_cars": 0, "wait_score": 0, "red_duration": 0, "connection": None },
            {"name" : "Backward", "partner_dir": "Forward", "light_val": False, "waiting_cars": 0, "wait_score": 0, "red_duration": 0, "connection": None },
        ]
        self.threshold = threshold
        self.waitTotal = waitTotal
        self.carsMaxAdd = carsMaxAdd
        self.c = c
        self.ts = ts

    def connect(self, from_dir, neighbor, to_dir):
        # wires this intersection's `from_dir` light to feed cars into
        # `neighbor`'s `to_dir` queue whenever it turns green
        for direction in self.directions:
            if direction["name"] == from_dir:
                direction["connection"] = (neighbor, to_dir)

    def switchGreen(self):
        for direction in self.directions:
            if not direction["light_val"]:
                self.waitTotal += direction["wait_score"]
                if direction["connection"] is not None:
                    neighbor, to_dir = direction["connection"]
                    for n_dir in neighbor.directions:
                        if n_dir["name"] == to_dir:
                            n_dir["waiting_cars"] += direction["waiting_cars"]
                direction["waiting_cars"] = 0
                direction["wait_score"] = 0
                direction["red_duration"] = 0
                direction["light_val"] = not direction["light_val"]
            else:
                direction["red_duration"] = 0  # about to turn red, fresh start
                direction["light_val"] = not direction["light_val"]


    def timestep(self, newts=True):
        if newts:
            self.ts += 1
        reds = [direction for direction in self.directions if not direction["light_val"]]
        for red in reds:
            if red["wait_score"] > self.threshold:
                self.switchGreen()
                self.timestep(newts=False)
            else:
                red["red_duration"] += 1
                red["waiting_cars"] += random.randint(0, self.carsMaxAdd)
                # wait_score: linear in queue size, quadratic in how long
                # it's been red - so long-waiting cars dominate the score
                # instead of just raw queue size (prevents starvation)
                red["wait_score"] = red["waiting_cars"] * (red["red_duration"] ** 2)

    def printQuickSummary(self):
        print("\n\n")
        print(f"intersection: {self.id}    timestep: {self.ts}")
        for direction in self.directions:
            print(f"{direction["name"]}: {direction}")
            print(f"    wait_score: {direction["wait_score"]}")
        print("\n\n")

    def __str__(self):
        avg_wait = self.waitTotal / self.ts if self.ts > 0 else 0
        print(f"OVERALL STATS - Intersection {self.id}")
        print(f"Car Threshold: {self.threshold} \nTotal Wait Score: {self.waitTotal}")
        print(f"Average Wait Score (per timestep): {avg_wait:.2f}")
        print(f"Formula for Wait Score: waiting_cars * (red_duration ** 2) \n")
        return ""


v = 10
e = 12
graph = randomGraph(v, e)

from prettyprint import returnGraph
with open("graphs.txt", "w") as f:
    f.write(str(graph) + "\n\n")
    f.write(str(returnGraph(graph)))
print(graph)

optim_thresh = [0.,   0.,   0.,   8.7, 24.3,  0.,  10.9, 28.6, 33.5, 29.4]

# WTIH                   WITHOUT
#  1077012.99            1426331.69

intersections = {i: IntersectionManyWay(id=i, threshold=0) for i in range(v)}
# intersections = {i: IntersectionManyWay(id=i, threshold=optim_thresh[i]) for i in range(v)}

# each undirected edge in graph gets mapped to a pair of directions (one on
# each intersection). Since there are only 4 sides per intersection, any
# node with more than 4 edges just keeps its first 4 and drops the rest.
DIR_NAMES = ["Left", "Right", "Forward", "Backward"]
used = {i: 0 for i in range(v)}
for start in graph:
    for end in graph[start]:
        if start < end:
            if used[start] >= 4 or used[end] >= 4:
                continue
            start_dir = DIR_NAMES[used[start]]
            end_dir = DIR_NAMES[used[end]]
            intersections[start].connect(start_dir, intersections[end], end_dir)
            intersections[end].connect(end_dir, intersections[start], start_dir)
            used[start] += 1
            used[end] += 1

for i in range(10**6):
    if (i+1) % (5*10**4) == 0:
        print(f"timestep {i+1}")
    for node in intersections.values():
        node.timestep()
    # if (i+1) % 10 == 0:
    #     for node in intersections.values():
    #         node.printQuickSummary()

for node in intersections.values():
    print(node)

total_wait = sum(node.waitTotal for node in intersections.values())
total_ts = sum(node.ts for node in intersections.values())
overall_avg_wait = total_wait / total_ts if total_ts > 0 else 0
print("=" * 40)
print("CITY-WIDE STATS")
print(f"Total Wait Score (all intersections): {total_wait}")
print(f"Overall Average Wait Score (per timestep): {overall_avg_wait:.2f}")