from utils import randomGraph
from prettyprint import printGraph, returnGraph
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
                threshold = 100,
                waitTotal = 0,
                carsMaxAdd = 3, # noise
                c = 1.1,
                ts = 0
                 ):
        self.id = id
        self.directions = Directions if Directions is not None else [
            {"name" : "Left", "partner_dir": "Right", "light_val": True, "waiting_cars": 0, "wait_score": 0, "connection": None },
            {"name" : "Right", "partner_dir": "Left", "light_val": True, "waiting_cars": 0, "wait_score": 0, "connection": None },
            {"name" : "Forward", "partner_dir": "Backward", "light_val": False, "waiting_cars": 0, "wait_score": 0, "connection": None },
            {"name" : "Backward", "partner_dir": "Forward", "light_val": False, "waiting_cars": 0, "wait_score": 0, "connection": None },
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
                direction["light_val"] = not direction["light_val"]
            else:
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
                red["waiting_cars"] += random.randint(0, self.carsMaxAdd)
                x = red["waiting_cars"]
                red["wait_score"] += x*self.c**x

    def printQuickSummary(self):
        print("\n\n")
        print(f"intersection: {self.id}    timestep: {self.ts}")
        for direction in self.directions:
            print(f"{direction["name"]}: {direction}")
            print(f"    wait_score: {direction["wait_score"]}")
        print("\n\n")

    def __str__(self):
        print(f"OVERALL STATS - Intersection {self.id}")
        print(f"Car Threshold: {self.threshold} \nTotal Wait Score: {self.waitTotal}")
        print(f"Formula for Wait Score: x = num_cars_on_curr_side, c = {self.c}; x*{self.c}^x \n")
        return ""


v = 10
e = 12
graph = randomGraph(v, e)
with open("graphs.txt", "w") as f:
    f.write("PREV GRAPH: \n" + str(graph))
    f.write("\nVisualization \n" + str(returnGraph(graph)))

printGraph(graph)

intersections = {i: IntersectionManyWay(id=i, threshold=5) for i in range(v)}

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

for i in range(100):
    for node in intersections.values():
        node.timestep()
    # if (i+1) % 10 == 0:
    #     for node in intersections.values():
    #         node.printQuickSummary()

total_wait = 0
for node in intersections.values():
    print(node)
    total_wait += node.waitTotal
    
print("CUMULATIVE WAIT: " + str(total_wait))
print("AVERAGE WATI: " + str(total_wait//v))