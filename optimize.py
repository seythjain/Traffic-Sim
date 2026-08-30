from utils import randomGraph
import random
import torch

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


def build_city(v, e, seed=None):
    if seed is not None:
        random.seed(seed)
    graph = randomGraph(v, e)
    intersections = {i: IntersectionManyWay(id=i, threshold=0) for i in range(v)}
    DIR_NAMES = ["Left", "Right", "Forward", "Backward"]
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


def total_wait(thresholds, v, e, steps=100, seed=None):
    """Run the city sim with given per-intersection thresholds, return total wait."""
    city = build_city(v, e, seed=seed)
    for i, inter in city.items():
        inter.threshold = max(0.0, float(thresholds[i]))
    for _ in range(steps):
        for inter in city.values():
            inter.timestep()
    return sum(inter.waitTotal for inter in city.values())


class ESOptimizer:
    """Evolution Strategies: treats `mean` as the learnable thresholds,
    estimates a gradient via random perturbations (since the sim itself
    isn't differentiable), and lets torch.optim do the update."""
    def __init__(self, v, e, lr=2.0, sigma=5.0, pop_size=30, steps=100):
        self.v, self.e, self.steps = v, e, steps
        self.sigma, self.pop_size = sigma, pop_size
        self.mean = torch.full((v,), 10.0, requires_grad=True)
        self.optimizer = torch.optim.Adam([self.mean], lr=lr)

    def step(self, seeds=(1, 2, 3)):
        # the sim is very high-variance (x*c^x amplifies random noise), so
        # each candidate is scored as an AVERAGE over several seeds instead
        # of one run - otherwise the "gradient" is mostly just noise
        noise = torch.randn(self.pop_size, self.v)
        rewards = torch.zeros(self.pop_size)
        for i in range(self.pop_size):
            thresholds = self.mean.detach() + self.sigma * noise[i]
            waits = [total_wait(thresholds, self.v, self.e, self.steps, seed=s) for s in seeds]
            rewards[i] = -sum(waits) / len(waits)

        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-8)
        grad_estimate = (noise * rewards.unsqueeze(1)).mean(dim=0) / self.sigma

        self.optimizer.zero_grad()
        self.mean.grad = -grad_estimate  # ascend reward = descend -reward
        self.optimizer.step()
        with torch.no_grad():
            self.mean.clamp_(min=0)
        return -rewards.mean().item()  # normalized, just for logging


if __name__ == "__main__":
    V, E = 10, 12
    opt = ESOptimizer(v=V, e=E, lr=1.0, sigma=3.0, pop_size=30, steps=100)
    for epoch in range(30):
        opt.step(seeds=(10, 20, 30, 40, 50))
        if (epoch + 1) % 5 == 0:
            eval_wait = sum(total_wait(opt.mean.detach(), V, E, 100, seed=s) for s in range(100, 105)) / 5
            print(f"epoch {epoch+1}: thresholds={opt.mean.detach().numpy().round(1)} "
                  f"avg_eval_wait={eval_wait:.2f}")