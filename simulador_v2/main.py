import json
from asyncio import current_task
from typing import List


class Task:
    def __init__(self, id, offset, computation_time, period_time, quantum, deadline):
        self.id = id
        self.offset = offset
        self.computation_time = computation_time
        self.period_time = period_time
        self.quantum = quantum
        self.deadline = deadline
        self.start_time = 0
        self.finish_time = 0
        self.remaining_time = computation_time
        self.waiting_time = 0

    def __repr__(self):
        return f"T{self.id}"


def read_tasks_from_json(file_path: str):
    with open(file_path) as f:
        data = json.load(f)
        tasks = []
        for i, t in enumerate(data['tasks']):
            try:
                tasks.append(Task(
                    id=i,
                    offset=t["offset"],
                    computation_time=t["computation_time"],
                    period_time=t["period_time"],
                    quantum=t["quantum"],
                    deadline=t["deadline"]
                ))
            except KeyError as e:
                raise ValueError(f"Erro na task {i}: campo vazio -> {e}")

    return data["simulation_time"], data["scheduler_name"], tasks


def simulate_fcfs(sim_time: int, tasks: List[Task]):
    tasks.sort(key=lambda task: task.offset)
    time = 0
    sequence = []
    ready_queue = []
    executed_tasks = []

    while time < sim_time:
        for task in tasks:
            if task.offset >= time:
                ready_queue.append(task)

        if ready_queue:
            current_task = ready_queue.pop(0)
            if current_task.start_time == 0:
                current_task.start_time = time
            sequence.extend([current_task.id] * current_task.computation_time)
            time += current_task.computation_time
            current_task.finish_time = time
            current_task.waiting_time = current_task.start_time - current_task.offset
            executed_tasks.append(current_task)
        else:
            sequence.append("idle")
            time += 1
    print_timeline(tasks, sim_time)
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
            if current_task.start_time == 0:
                current_task.start_time = time
            sequence.extend([current_task.id] * current_task.computation_time)
            time += current_task.computation_time
            current_task.finish_time = time
            current_task.waiting_time = current_task.start_time - current_task.offset
            executed_tasks.append(current_task)
        else:
            sequence.append("idle")
            time += 1
    print_timeline(tasks, sim_time)
    return sequence, executed_tasks

def simulate_rr(sim_time: int, tasks: List[Task]):
    time = 0
    sequence = []
    ready_queue = []
    tasks_remaining = []
    executed_tasks = []

    for task in tasks:
        if(task.computation_time % task.quantum == 0):
            task.ativs_remaining = task.computation_time / task.quantum
        else:
            task.ativs_remaining = task.computation_time % task.quantum

    while time < sim_time:

        pass

    print_timeline(tasks, sim_time)
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

def print_timeline(tasks: List[Task], sim_time):
    print("\nTimeline:")
    for task in tasks:
        line = []
        start = task.finish_time - task.computation_time
        for t in range(sim_time):
            if t >= task.offset and t < start:
                line.append('-')
            elif t >= start and t < task.finish_time:
                line.append('#')
            else:
                line.append('_')
        print(f"T{task.id}: {''.join(line)}")

if __name__ == "__main__":
    sim_time, scheduler, tasks = read_tasks_from_json("package.json")
    print(tasks.__getitem__(1).offset)
    if scheduler == "FCFS":
        sequence, executed_tasks = simulate_fcfs(sim_time, tasks)
    elif scheduler == "SJF":
        sequence, executed_tasks = simulate_sjf(sim_time, tasks)
    elif scheduler == "RR":
        sequence, executed_tasks = simulate_rr(sim_time, tasks)
    else:
        print("Algoritmo não implementado.")
    print("Sequência de Execução:")
    print(sequence)
    metrics = calculate_metrics(executed_tasks)
    print("\nMétricas:")
    for k, v in metrics.items():
        print(f"{k}: {v}")


# TODO: Tratar quando não há tarefas no processodor e mesmo assim, n se executa
# TODO: Tratar fila de em relação ao id, já que o print do fcfs está sendo: T0, T1, T3, T2 ao invés de sair em ordem
