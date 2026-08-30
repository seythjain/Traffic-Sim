from utils import randomGraph
import random
import torch
import csv

DIR_NAMES = ["Left", "Right", "Forward", "Backward"]


class IntersectionManyWay:
    def __init__(self, id=0, Directions=None, threshold=0, waitTotal=0,
                 carsMaxAdd=3, c=1.1, ts=0):
        self.id = id
        self.directions = Directions if Directions is not None else [
            {"name": "Left", "partner_dir": "Right", "light_val": True, "waiting_cars": 0, "wait_score": 0, "red_duration": 0, "connection": None},
            {"name": "Right", "partner_dir": "Left", "light_val": True, "waiting_cars": 0, "wait_score": 0, "red_duration": 0, "connection": None},
            {"name": "Forward", "partner_dir": "Backward", "light_val": False, "waiting_cars": 0, "wait_score": 0, "red_duration": 0, "connection": None},
            {"name": "Backward", "partner_dir": "Forward", "light_val": False, "waiting_cars": 0, "wait_score": 0, "red_duration": 0, "connection": None},
        ]
        self.threshold = threshold
        self.waitTotal = waitTotal
        self.carsMaxAdd = carsMaxAdd
        self.c = c
        self.ts = ts

    def connect(self, from_dir, neighbor, to_dir):
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
                direction["red_duration"] = 0
                direction["light_val"] = not direction["light_val"]

    def timestep(self, newts=True):
        if newts:
            self.ts += 1
        reds = [d for d in self.directions if not d["light_val"]]
        for red in reds:
            if red["wait_score"] > self.threshold:
                self.switchGreen()
                self.timestep(newts=False)
            else:
                red["red_duration"] += 1
                red["waiting_cars"] += random.randint(0, self.carsMaxAdd)
                red["wait_score"] = red["waiting_cars"] * (red["red_duration"] ** 2)


def build_city_from_graph(graph, v, thresholds):
    """Build intersections wired according to a FIXED graph, with given
    per-intersection thresholds. Reused across configs so the comparison
    is apples-to-apples (same road layout, different threshold policy)."""
    intersections = {i: IntersectionManyWay(id=i, threshold=float(thresholds[i])) for i in range(v)}
    used = {i: 0 for i in range(v)}
    for start in graph:
        for end in graph[start]:
            if start < end and used[start] < 4 and used[end] < 4:
                sd, ed = DIR_NAMES[used[start]], DIR_NAMES[used[end]]
                intersections[start].connect(sd, intersections[end], ed)
                intersections[end].connect(ed, intersections[start], sd)
                used[start] += 1
                used[end] += 1
    return intersections


def run_sim(graph, v, thresholds, steps, seed=None):
    if seed is not None:
        random.seed(seed)
    city = build_city_from_graph(graph, v, thresholds)
    for _ in range(steps):
        for node in city.values():
            node.timestep()
    total_wait = sum(node.waitTotal for node in city.values())
    total_ts = sum(node.ts for node in city.values())
    avg_wait = total_wait / total_ts if total_ts else 0
    return total_wait, avg_wait


class ESOptimizer:
    """Evolution Strategies optimizer, scoped to ONE fixed graph."""
    def __init__(self, graph, v, lr=1.0, sigma=3.0, pop_size=20, steps=200):
        self.graph, self.v, self.steps = graph, v, steps
        self.sigma, self.pop_size = sigma, pop_size
        self.mean = torch.full((v,), 10.0, requires_grad=True)
        self.optimizer = torch.optim.Adam([self.mean], lr=lr)

    def step(self, seeds=(1, 2)):
        noise = torch.randn(self.pop_size, self.v)
        rewards = torch.zeros(self.pop_size)
        for i in range(self.pop_size):
            thresholds = torch.clamp(self.mean.detach() + self.sigma * noise[i], min=0)
            waits = [run_sim(self.graph, self.v, thresholds.tolist(), self.steps, seed=s)[0] for s in seeds]
            rewards[i] = -sum(waits) / len(waits)
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-8)
        grad = (noise * rewards.unsqueeze(1)).mean(dim=0) / self.sigma
        self.optimizer.zero_grad()
        self.mean.grad = -grad
        self.optimizer.step()
        with torch.no_grad():
            self.mean.clamp_(min=0)


def optimize_for_graph(graph, v, epochs=15, **kwargs):
    opt = ESOptimizer(graph, v, **kwargs)
    for _ in range(epochs):
        opt.step()
    return opt.mean.detach().tolist()


if __name__ == "__main__":
    V = 10
    E = 12
    EVAL_STEPS = 100       # timesteps for the final comparison run
    ES_STEPS = 150          # timesteps per candidate during ES search (kept short for speed)
    ES_EPOCHS = 150
    NUM_GRAPHS = 5000

    results = []
    for g in range(NUM_GRAPHS):
        random.seed(1000 + g)
        graph = randomGraph(V, E)

        random_thresholds = [random.uniform(0, 40) for _ in range(V)]
        optimized_thresholds = optimize_for_graph(
            graph, V, epochs=ES_EPOCHS, lr=1.0, sigma=3.0, pop_size=20, steps=ES_STEPS
        )

        eval_seed = 5000 + g  # same seed for both configs -> same car arrivals, fair comparison
        wait_random, avg_random = run_sim(graph, V, random_thresholds, steps=EVAL_STEPS, seed=eval_seed)
        wait_opt, avg_opt = run_sim(graph, V, optimized_thresholds, steps=EVAL_STEPS, seed=eval_seed)

        improvement = 100 * (wait_random - wait_opt) / wait_random if wait_random else 0
        results.append({
            "graph": g, "graph_edges": graph,
            "random_thresholds": random_thresholds,
            "optimized_thresholds": optimized_thresholds,
            "wait_random": wait_random, "wait_optimized": wait_opt,
            "avg_wait_random": avg_random, "avg_wait_optimized": avg_opt,
            "improvement_pct": improvement,
        })
        print(f"graph {g}: random={wait_random:.1f}  optimized={wait_opt:.1f}  "
              f"improvement={improvement:.1f}%")

    # with open("comparison_results.csv", "w", newline="") as f:
    #     writer = csv.writer(f)
    #     writer.writerow(["graph", "wait_random", "wait_optimized",
    #                       "avg_wait_random", "avg_wait_optimized", "improvement_pct"])
    #     for r in results:
    #         writer.writerow([r["graph"], r["wait_random"], r["wait_optimized"],
    #                           r["avg_wait_random"], r["avg_wait_optimized"], r["improvement_pct"]])

    with open("comparison_details.txt", "w") as f:
        for r in results:
            f.write(f"Graph {r['graph']}\n")
            f.write(f"  Edges: {r['graph_edges']}\n")
            f.write(f"  Random thresholds:    {[round(t, 1) for t in r['random_thresholds']]}\n")
            f.write(f"  Optimized thresholds: {[round(t, 1) for t in r['optimized_thresholds']]}\n")
            f.write(f"  Total wait (random):    {r['wait_random']:.1f}\n")
            f.write(f"  Total wait (optimized): {r['wait_optimized']:.1f}\n")
            f.write(f"  Improvement: {r['improvement_pct']:.1f}%\n\n")

    avg_improvement = sum(r["improvement_pct"] for r in results) / len(results)
    print(f"\nAverage improvement across {NUM_GRAPHS} graphs: {avg_improvement:.1f}%")
    print("Saved comparison_results.csv and comparison_details.txt")
