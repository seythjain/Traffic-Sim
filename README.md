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

```bash
python main.py
```

This will:
1. Generate a random graph (10 vertices, 12 edges by default)
2. Run 1 million timesteps of simulation
3. Output graphs to `graphs.txt`
4. Print intersection and city-wide statistics

## Configuration

In `main.py`, you can adjust:
- `v`: Number of intersections (vertices)
- `e`: Number of connections (edges)
- `threshold`: Wait score threshold for switching lights (default: 0)
- `carsMaxAdd`: Maximum cars arriving per timestep (default: 3)
- `optim_thresh`: Array of optimized thresholds per intersection (commented out)

## Output Files

- `graphs.txt`: Visual representation of the intersection network
- `comparison_results.csv`: Simulation comparison results (gitignored)
- `comparison_details.txt`: Detailed comparison data (gitignored)

## Example Results

The provided optimized thresholds in `main.py` show:
- **Without optimization** (threshold=0): 1,426,331.69 total wait score
- **With optimization**: 1,077,012.99 total wait score (~24% improvement)

## Requirements

- Python 3.x
- No external dependencies required

## Future Enhancements

- Optimization algorithms to find ideal per-intersection thresholds
- Visualization of traffic flow over time
- Support for variable intersection configurations
- Different car arrival distributions
