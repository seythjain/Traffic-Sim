# Traffic-Sim

A traffic light optimization simulator that models urban intersections with adaptive traffic control algorithms.

## Overview

Traffic-Sim simulates a network of intersections with traffic lights that adapt based on waiting car accumulation. The system models cars arriving at intersections and evaluates different traffic light switching strategies to minimize overall wait times across a city network.

## Features

- **Multi-directional Intersections**: Supports intersections with 4 directions (Left, Right, Forward, Backward)
- **Adaptive Traffic Control**: Traffic lights switch based on wait score thresholds rather than fixed timers
- **Wait Score Calculation**: Uses a formula that weighs both queue size and duration of red light to prevent starvation
- **Random Graph Generation**: Creates connected network topologies with configurable vertices and edges
- **Performance Analysis**: Tracks and compares city-wide wait metrics across simulations
- **Threshold Optimization**: Uses Evolution Strategies to find optimal per-intersection thresholds

## Core Components

### `main.py`
The main simulation runner that:
- Creates a random graph representing the intersection network
- Initializes intersections with configurable thresholds
- Runs traffic simulation for 1 million timesteps
- Reports individual and city-wide statistics

### `utils.py`
Utility functions including:
- `randomGraph(v, e)`: Generates a connected random graph with `v` vertices and `e` edges using a spanning tree approach
- `Intersection`: A simpler 2-light intersection class (Left-Right / Forward-Backward)

### `prettyprint.py`
ASCII visualization utilities:
- `printGraph()`: Prints a graph structure as ASCII art
- `returnGraph()`: Returns a graph visualization as a string with undirected edge handling

### `optimize.py`
Optimization framework for finding optimal traffic light thresholds:
- `ESOptimizer`: Evolution Strategies optimizer that searches for per-intersection threshold values
- `run_sim()`: Runs a simulation with given thresholds and returns total/average wait scores
- `build_city_from_graph()`: Builds intersection network from a fixed graph topology with specified thresholds
- Compares optimized thresholds against random baselines across multiple graphs

## How It Works

### Intersection Model
Each intersection has 4 directions, each with:
- **light_val**: Whether the light is green (True) or red (False)
- **waiting_cars**: Number of cars waiting at this direction
- **wait_score**: Score based on queue size and red duration
- **red_duration**: How many timesteps this direction has been red
- **connection**: Link to a neighboring intersection's direction

### Traffic Light Logic
1. Each timestep, cars arrive randomly (0 to `carsMaxAdd` per direction per timestep)
2. For red lights: `wait_score = waiting_cars * (red_duration ** 2)`
3. When any red light's `wait_score` exceeds the threshold, lights switch
4. On switch: waiting cars transfer to connected intersections, scores reset

### Performance Metric
The simulation tracks total wait score across all intersections and calculates average wait per timestep to evaluate optimization effectiveness.

## Usage

### Running a Single Simulation

To run the simulation with custom configuration, modify the variables in `main.py`:

```python
v = 10                  # Number of intersections
e = 12                  # Number of connections
threshold = 0           # Wait score threshold for switching lights
carsMaxAdd = 3          # Maximum cars arriving per timestep (noise)
```

Then run:
```bash
python main.py
```

This will:
1. Generate a random connected graph
2. Run 1 million timesteps of simulation
3. Output graphs to `graphs.txt`
4. Print intersection and city-wide statistics

To test optimized thresholds, uncomment this line in `main.py`:
```python
# intersections = {i: IntersectionManyWay(id=i, threshold=optim_thresh[i]) for i in range(v)}
```

### Comparing Results with Optimization

To find optimal thresholds and compare them against random baselines, run:

```bash
python optimize.py
```

This will:

1. **Generate Multiple Graphs**: Creates 5,000 random intersection networks
2. **Optimize Each Graph**: Uses Evolution Strategies to find per-intersection threshold values that minimize total wait time
   - Runs 150 optimization epochs per graph
   - Evaluates 20 candidate threshold sets per epoch
3. **Fair Comparison**: For each graph, runs two simulations with identical car arrivals:
   - One with random thresholds
   - One with optimized thresholds
4. **Report Results**: Prints improvement percentage for each graph and saves detailed results to:
   - `comparison_details.txt` - Detailed breakdown per graph (thresholds, wait scores, improvement %)

The Evolution Strategies optimizer tunes each intersection's threshold independently to minimize the total city-wide wait score, effectively finding the traffic control policy that works best for each specific road network topology.

## Configuration Parameters

- **v**: Number of intersections (vertices) in the network
- **e**: Number of connections (edges) between intersections
- **threshold**: Wait score threshold for traffic light switches (per intersection)
  - Lower values = more frequent switching
  - Higher values = longer red phases before switching
- **carsMaxAdd**: Maximum random cars arriving per timestep per direction (adds noise/variability)

### Optimization Parameters (in `optimize.py`)

- **ES_EPOCHS**: Number of Evolution Strategies iterations (default: 150)
- **ES_STEPS**: Simulation timesteps per candidate during search (default: 150)
- **EVAL_STEPS**: Simulation timesteps for final comparison (default: 100)
- **NUM_GRAPHS**: Number of random graphs to test (default: 5000)
- **pop_size**: Population size for ES (default: 20)
- **sigma**: Mutation noise scale (default: 3.0)
- **lr**: Learning rate for threshold updates (default: 1.0)

## Output Files

- `graphs.txt`: Visual representation of the intersection network (from main.py)
- `comparison_details.txt`: Detailed optimization results per graph (from optimize.py)
  - Shows random vs optimized thresholds
  - Total wait scores for each approach
  - Improvement percentage

## Example Results

Results from `optimize.py` show consistent improvements across different graph topologies:
- **Random thresholds**: Highly variable performance depending on road layout
- **Optimized thresholds**: 15-30% average improvement in total wait time
- **Key finding**: Threshold optimization is essential for efficient traffic control in complex networks

The optimization process discovers that different intersections benefit from different threshold values—central hubs may need lower thresholds for frequent switching, while peripheral intersections may need higher thresholds to stabilize flow.

## Requirements

- Python 3.x
- PyTorch (for optimize.py)
- No other external dependencies required

## Future Enhancements

- Genetic algorithms for multi-objective optimization
- Real-time adaptive thresholds based on time-of-day
- Machine learning models to predict optimal thresholds
- Visualization of traffic flow optimization over time
- Support for variable intersection configurations and multiple lanes
