from prettyprint import printGraph
import random

def randomGraph(v, e):
    # there are only v*(v-1)/2 possible edges between v nodes - without this
    # clamp, asking for more than that sends the retry loop below into an
    # infinite search for a pair that doesn't exist
    max_possible_edges = v * (v - 1) // 2
    e = min(e, max_possible_edges)

    graph = {}
    for i in range(v):
        graph[i] = []

    edges = []

    # Step 1: build a random spanning tree over all v nodes first.
    # This guarantees the graph ends up as ONE connected section instead of
    # possibly splitting into separate islands - every node gets linked to
    # the growing connected component before any "extra" random edges happen.
    nodes = list(range(v))
    random.shuffle(nodes)
    connected = [nodes[0]]
    for node in nodes[1:]:
        other = random.choice(connected)
        graph[node].append(other)
        graph[other].append(node)
        edges.append((node, other))
        connected.append(node)

    # Step 2: use up whatever edge budget is left on random extra edges,
    # same recursive retry logic as before (skip self-loops and dupes)
    extra = e - len(edges)
    for i in range(extra):
        def initialize():
            start = random.randint(0, v-1)
            end = random.randint(0, v-1)
            if start == end:
                return initialize()
            if (start, end) in edges or (end, start) in edges:
                return initialize()
            graph[start].append(end)
            graph[end].append(start)
            edges.append((start, end))
        initialize()
    return graph


#   SIMPLE INTERSECTION

class Intersection:
    def __init__(self, 
                lightLR = {"name": "Left-Right", "light_val": False, "waiting_cars": 0, "wait_score": 0},
                lightFB = {"name": "Forward-Backward" , "light_val": True, "waiting_cars": 0, "wait_score": 0},
                threshold = 100,
                waitTotal = 0,
                carsMaxAdd = 3,
                c = 1.1,
                ts = 0
                 ):
        self.lightLR = lightLR
        self.lightFB = lightFB
        self.threshold = threshold
        self.waitTotal = waitTotal
        self.carsMaxAdd = carsMaxAdd
        self.c = c
        self.ts = ts

    def switchGreen(self):
        green = self.lightLR if self.lightLR["light_val"] else self.lightFB
        red = self.lightLR if not self.lightLR["light_val"] else self.lightFB
        # print(f"green: {green}")
        # print(f"red: {red}")
        red["light_val"] = not red["light_val"]
        green["light_val"] = not green["light_val"]     

        self.waitTotal += red["wait_score"]
        red["waiting_cars"] = 0
        red["wait_score"] = 0


    def timestep(self):
        self.ts += 1
        red = self.lightLR if not self.lightLR["light_val"] else self.lightFB

        if red["wait_score"] > self.threshold:
            self.switchGreen()
        else:
            red["waiting_cars"] += random.randint(0, self.carsMaxAdd)
            x = red["waiting_cars"]
            red["wait_score"] += x*2**x

    def printQuickSummary(self):
        print("\n\n")
        print(f"timestep: {self.ts}")
        print(f"LR: {self.lightLR}")
        print(f"    wait_score: {self.lightLR["wait_score"]}")
        print(f"FB: {self.lightFB}")
        print(f"    wait_score: {self.lightFB["wait_score"]}")
        print("\n\n")

    def __str__(self):
        green = self.lightLR if self.lightLR["light_val"] else self.lightFB
        red = self.lightLR if not self.lightLR["light_val"] else self.lightFB

        print(f"TIMESTEP: {self.ts}\n")
        print(f"Green: {green["name"]}")
        print(f"Red: {red["name"]}\n")

        print(f"GREEN SIDE (prettry boring)")
        print(f"Cars Waiting: 0")
        print(f"Wait Score: 0\n")

        print(f"RED SIDE:")
        print(f"Cars Waiting: {red["waiting_cars"]}")
        print(f"Wait Score: {red["wait_score"]}\n")

        print("OVERALL STATS")
        print(f"Car Threshold: {self.threshold} \nTotal Wait Score: {self.waitTotal}")
        print(f"Formula for Wait Score: x = num_cars_on_curr_side, c = {self.c}; x*{self.c}^x \n")
        return ""


if __name__ == "main":
    printGraph(randomGraph(10, 7))