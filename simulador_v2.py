import json
from typing import List, Dict

class Task:
    def __init__(self, id, offset, computation_time, period_time, quantum, deadline):
        self.id = id
        self.offset = offset
        self.computation_time = computation_time
        self.period_time = period_time
        self.quantum = quantum
        self.deadline = deadline
        self.start_time = None
        self.finish_time = None
        self.remaining_time = computation_time
        self.waiting_time = 0

    def __repr__(self):
        return f"T{self.id}"


def read_tasks_from_json(file_path: str):
    with open(file_path) as f:
        data = json.load(f)

    tasks = []
    for i, t in enumerate(data["tasks"]):
        tasks.append(Task(
            id=i,
            offset=t["offset"],
            computation_time=t["computation_time"],
            period_time=t["period_time"],
            quantum=t["quantum"],
            deadline=t["deadline"]
        ))

    return data["simulation_time"], data["scheduler_name"], tasks


def simulate_fcfs(sim_time: int, tasks: List[Task]):
    time = 0
    sequence = []
    ready_queue = []
    executed_tasks = []

    while time < sim_time:
        for task in tasks:
            if task.offset == time:
                ready_queue.append(task)

        if ready_queue:
            current_task = ready_queue.pop(0)
            if current_task.start_time is None:
                current_task.start_time = time
            sequence.extend([current_task.id] * current_task.computation_time)
            time += current_task.computation_time
            current_task.finish_time = time
            current_task.waiting_time = current_task.start_time - current_task.offset
            executed_tasks.append(current_task)
        else:
            sequence.append("idle")
            time += 1

    return sequence, executed_tasks


def simulate_sjf(sim_time: int, tasks: List[Task]):
    time = 0
    sequence = []
    ready_queue = []
    executed_tasks = []
    tasks_remaining = tasks[:]

    while time < sim_time:
        for task in tasks_remaining[:]:
            if task.offset <= time:
                ready_queue.append(task)
                tasks_remaining.remove(task)

        if ready_queue:
            current_task = min(ready_queue, key=lambda t: t.computation_time)
            ready_queue.remove(current_task)
            if current_task.start_time is None:
                current_task.start_time = time
            sequence.extend([current_task.id] * current_task.computation_time)
            time += current_task.computation_time
            current_task.finish_time = time
            current_task.waiting_time = current_task.start_time - current_task.offset
            executed_tasks.append(current_task)
        else:
            sequence.append("idle")
            time += 1

    return sequence, executed_tasks


def calculate_metrics(tasks: List[Task]):
    tat_list = [task.finish_time - task.offset for task in tasks]
    wt_list = [task.waiting_time for task in tasks]

    return {
        "TAT_avg_system": sum(tat_list) / len(tat_list),
        "WT_avg_system": sum(wt_list) / len(wt_list),
        "TAT_per_task": tat_list,
        "WT_per_task": wt_list,
        "Most_Waiting_Task": max(tasks, key=lambda t: t.waiting_time).id,
        "Least_Waiting_Task": min(tasks, key=lambda t: t.waiting_time).id,
        "CPU_utilization": sum(t.computation_time for t in tasks) / max(t.finish_time for t in tasks)
    }


def main(file_path: str):
    sim_time, scheduler, tasks = read_tasks_from_json(file_path)

    if scheduler == "FCFS":
        sequence, executed_tasks = simulate_fcfs(sim_time, tasks)
    elif scheduler == "SJF":
        sequence, executed_tasks = simulate_sjf(sim_time, tasks)
    else:
        print("Algoritmo não implementado.")
        return

    print("Sequência de Execução:")
    print(sequence)

    metrics = calculate_metrics(executed_tasks)
    print("\nMétricas:")
    for k, v in metrics.items():
        print(f"{k}: {v}")

# Exemplo de uso:
# main("config.json")