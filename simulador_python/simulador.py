import json

class Task:
    def __init__(self, id, offset, computation_time):
        self.id = id
        self.offset = offset
        self.computation_time = computation_time
        self.completion = 0
        self.waiting = 0
        self.turnaround = 0

def load_tasks_from_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
        tasks = []
        for i, task in enumerate(data['tasks']):
            try:
                tasks.append(Task(i,
                                  task["offset"],
                                  task["computation_time"]))
            except KeyError as e:
                raise ValueError(f"Erro na task {i}: campo vazio -> {e}")
        return tasks

def fcfs(tasks):
    tasks.sort(key=lambda task: task.offset)
    time = 0
    for task in tasks:
        if time < task.offset:
            time = task.offset
        task.waiting = time - task.offset
        time += task.computation_time
        task.completion = time
        task.turnaround = task.completion - task.offset

    print("\nFCFS Scheduling:")
    for task in tasks:
        print(f"P{task.id} WT={task.waiting} TAT={task.turnaround}")
    print_detailed_timeline(tasks, time)

def sjf_non_preemptive(tasks):
    n = len(tasks)
    complete = 0
    time = 0
    visited = [False] * n
    result = []

    while complete < n:
        idx = -1
        min_computation_time = float('inf')
        for i, task in enumerate(tasks):
            if task.offset <= time and not visited[i] and task.computation_time < min_computation_time:
                min_computation_time = task.computation_time
                idx = i

        if idx == -1:
            time += 1
            continue

        task = tasks[idx]
        visited[idx] = True
        task.waiting = time - task.offset
        time += task.computation_time
        task.completion = time
        task.turnaround = task.completion - task.offset
        result.append(task)
        complete += 1

    print("\nSJF Non-Preemptive Scheduling:")
    for task in result:
        print(f"P{task.id} WT={task.waiting} TAT={task.turnaround}")
    print_detailed_timeline(result, time)

def print_detailed_timeline(tasks, total_time):
    print("\nTimeline detalhada:")
    for task in tasks:
        line = []
        start = task.completion - task.computation_time
        for t in range(total_time):
            if t >= task.offset and t < start:
                line.append('-')
            elif t >= start and t < task.completion:
                line.append('#')
            else:
                line.append('_')
        print(f"P{task.id}: {''.join(line)}")

if __name__ == "__main__":
    procs = load_tasks_from_json('simulador_python/file.json')
    fcfs([Task(task.id, task.offset, task.computation_time) for task in procs])
    sjf_non_preemptive([Task(task.id, task.offset, task.computation_time) for task in procs])
