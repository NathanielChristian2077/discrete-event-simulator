from task import Task

def fcfs(sim_time, tasks):
    queue = sorted(tasks, key=lambda t:t.offset)
    time = 0
    execution = []
    cpu_use = 0

    for task in queue:
        if time < task.offset:
            time = task.offset
        task.start_time = time
        for _ in range (task.computation_time):
            execution.append(f"T{task.id}")
        time += task.computation_time
        task.end_time = time
        cpu_use += task.computation_time
    return execution, cpu_use

def sjf(sim_time, tasks):
    queue = []
    time = 0
    execution = []
    cpu_use = 0
    tasks = sorted(tasks, key=lambda t:t.offset)
    index = 0

    while time < sim_time:
        while index < len(tasks) and tasks[index].offset <= time:
            queue.append(tasks[index])
            index += 1
        if queue:
            queue.sort(key=lambda t:t.computation_time)
            current = queue.pop(0)
            current.start_time = time
            for _ in range (current.computation_time):
                execution.append(f"T{current.id}")
            time += current.computation_time
            current.end_time = time
            cpu_use += current.computation_time
        else:
            execution.append("idle")
            time += 1
        return execution,cpu_use