import json
from asyncio import current_task
from typing import List
from collections import defaultdict


class Task:
    def __init__(self, id, offset, computation_time, period_time, quantum, deadline):
        self.id = id
        self.offset = offset
        self.computation_time = computation_time
        self.period_time = period_time
        self.quantum = quantum
        self.deadline = deadline
        self.start_time = None
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
    tasks_remaining = tasks[:]
    tasks_remaining.sort(key=lambda task: task.offset)
    time = 0
    sequence = []
    ready_queue = []
    executed_tasks = []

    while time < sim_time:
        for task in tasks_remaining[:]:
            if task.offset <= time:
                ready_queue.append(task)
                tasks_remaining.remove(task)

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

    print_timeline_simple(tasks, sim_time)
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
    print_timeline_simple(tasks, sim_time)
    return sequence, executed_tasks

def simulate_rr(sim_time: int, tasks: List[Task]):
    from collections import deque

    time = 0
    sequence = []
    ready_queue = deque()
    tasks_remaining = tasks[:]
    executed_tasks = []

    for task in tasks:
        task.remaining_time = task.computation_time
        task.executions = []

    while time < sim_time or ready_queue:
        for task in tasks_remaining[:]:
            if task.offset <= time:
                ready_queue.append(task)
                tasks_remaining.remove(task)

        if ready_queue:
            current = ready_queue.popleft()

            if current.start_time is None and current.remaining_time == current.computation_time:
                current.start_time = time

            exec_time = min(current.quantum, current.remaining_time)
            current.executions.append((time, time + exec_time))
            sequence.extend([current.id] * exec_time)
            time += exec_time
            current.remaining_time -= exec_time

            for task in tasks_remaining[:]:
                if task.offset <= time:
                    ready_queue.append(task)
                    tasks_remaining.remove(task)

            if current.remaining_time > 0:
                ready_queue.append(current)
            else:
                current.finish_time = time
                current.waiting_time = current.finish_time - current.offset - current.computation_time
                executed_tasks.append(current)
        else:
            sequence.append("idle")
            time += 1

    print_timeline_preemptive(tasks, sim_time)
    return sequence, executed_tasks


def simulate_srtf(sim_time: int, tasks: List[Task]):
    time = 0
    sequence = []
    ready_queue = []
    tasks_remaining = tasks[:]
    executed_tasks = []

    for task in tasks:
        task.remaining_time = task.computation_time
        task.executions = []

    current_task = None
    while time < sim_time:
        for task in tasks_remaining[:]:
            if task.offset <= time:
                ready_queue.append(task)
                tasks_remaining.remove(task)

        if current_task and current_task.remaining_time == 0:
            current_task.finish_time = time
            current_task.waiting_time = current_task.finish_time - current_task.offset - current_task.computation_time
            executed_tasks.append(current_task)
            current_task = None

        if ready_queue or current_task:
            if ready_queue:
                if current_task:
                    ready_queue.append(current_task)
                current_task = min(ready_queue, key=lambda t: t.remaining_time)
                ready_queue.remove(current_task)

            if current_task.start_time is None and current_task.remaining_time == current_task.computation_time:
                current_task.start_time = time

            current_task.remaining_time -= 1
            current_task.executions.append((time, time + 1))
            sequence.append(current_task.id)
        else:
            sequence.append("idle")

        time += 1

    print_timeline_preemptive(tasks, sim_time)
    return sequence, executed_tasks

# TODO: Refazer RM e EDF para não incluir instâncias não finalizadas no cálculo de métricas
def simulate_rm(sim_time: int, tasks: List[Task]):
    sequence = []
    executed_tasks = []
    active_tasks = []
    missed_deadlines = {}

    for task in tasks:
        task.remaining_time = task.computation_time
        task.executions = []
        task.instances = []
        missed_deadlines[task.id] = {"misses": 0, "total": 0}

    for time in range(sim_time):
        for task in tasks:
            if (time - task.offset) % task.period_time == 0 and time >= task.offset:
                new_instance = Task(
                    id=task.id,
                    offset=time,
                    computation_time=task.computation_time,
                    period_time=task.period_time,
                    quantum=task.quantum,
                    deadline=time + task.deadline
                )
                new_instance.remaining_time = task.computation_time
                new_instance.executions = []
                new_instance.original_id = task.id
                active_tasks.append(new_instance)
                missed_deadlines[task.id]["total"] += 1
        if ready := [
            t
            for t in active_tasks
            if t.offset <= time and t.remaining_time > 0
        ]:
            current = min(ready, key=lambda t: t.period_time)
            current.executions.append((time, time + 1))
            current.remaining_time -= 1
            sequence.append(current.id)

            if current.remaining_time == 0:
                current.finish_time = time + 1
                if current.finish_time > current.deadline:
                    missed_deadlines[current.id]["misses"] += 1
                    executed_tasks.append(current)
                elif current.deadline > sim_time:
                    print(f"\nTarefa {current.id} interrompida, tempo de simulação insuficiente para execução completa.")
        else:
            sequence.append("idle")

    for t in active_tasks:
        if t.executions and t not in executed_tasks:
            executed_tasks.append(t)

    print_timeline_realtime(executed_tasks, sim_time)

    print("\nDeadlines Perdidos (RM):")
    for tid, data in missed_deadlines.items():
        if data["misses"] >= 0:
            ratio = data["misses"] / data["total"]
            print(f"T{tid} perdeu {data['misses']} de {data['total']} deadlines ({ratio:.2f})")

    return sequence, executed_tasks


def simulate_edf(sim_time: int, tasks: List[Task]):
    sequence = []
    executed_tasks = []
    active_tasks = []
    missed_deadlines = {}

    for task in tasks:
        task.remaining_time = task.computation_time
        task.executions = []
        task.instances = []
        missed_deadlines[task.id] = {"misses": 0, "total": 0}

    for time in range(sim_time):
        for task in tasks:
            if (time - task.offset) % task.period_time == 0 and time >= task.offset:
                new_instance = Task(
                    id=task.id,
                    offset=time,
                    computation_time=task.computation_time,
                    period_time=task.period_time,
                    quantum=task.quantum,
                    deadline=time + task.deadline
                )
                new_instance.remaining_time = task.computation_time
                new_instance.executions = []
                new_instance.original_id = task.id
                active_tasks.append(new_instance)
                missed_deadlines[task.id]["total"] += 1

        if ready := [
            t
            for t in active_tasks
            if t.offset <= time and t.remaining_time > 0
        ]:
            current = min(ready, key=lambda t: t.deadline)
            current.executions.append((time, time + 1))
            current.remaining_time -= 1
            sequence.append(current.id)

            if current.remaining_time == 0:
                current.finish_time = time + 1
                if current.finish_time > current.deadline:
                    missed_deadlines[current.id]["misses"] += 1
                executed_tasks.append(current)
        else:
            sequence.append("idle")

    for t in active_tasks:
        if t.executions and t not in executed_tasks:
            executed_tasks.append(t)

    print_timeline_realtime(executed_tasks, sim_time)

    print("\nDeadlines Perdidos (EDF):")
    for tid, data in missed_deadlines.items():
        if data["misses"] > 0:
            ratio = data["misses"] / data["total"]
            print(f"T{tid} perdeu {data['misses']} de {data['total']} deadlines ({ratio:.2f})")

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

def calculate_metrics_realtime(instances: List[Task]):
    grouped = defaultdict(list)
    for task in instances:
        grouped[task.id].append(task)

    tat_avg_per_task = {}
    wt_avg_per_task = {}
    tat_all = []
    wt_all = []

    for tid, inst_list in grouped.items():
        tats = [t.finish_time - t.offset for t in inst_list]
        wts = [t.finish_time - t.offset - t.computation_time for t in inst_list]
        tat_avg_per_task[tid] = sum(tats) / len(tats)
        wt_avg_per_task[tid] = sum(wts) / len(wts)
        tat_all.extend(tats)
        wt_all.extend(wts)

    most_wt = max(wt_avg_per_task.items(), key=lambda x: x[1])[0]
    least_wt = min(wt_avg_per_task.items(), key=lambda x: x[1])[0]

    total_computation = sum(t.computation_time for t in instances)
    total_time = max(t.finish_time for t in instances)

    return {
        "TAT_avg_system": sum(tat_all) / len(tat_all),
        "WT_avg_system": sum(wt_all) / len(wt_all),
        "TAT_avg_per_task": tat_avg_per_task,
        "WT_avg_per_task": wt_avg_per_task,
        "Most_Waiting_Task": most_wt,
        "Least_Waiting_Task": least_wt,
        "CPU_utilization": total_computation / total_time
    }


def print_timeline_simple(tasks: List[Task], sim_time):
    print("\nTimeline:")
    for task in tasks:
        line = ['_'] * sim_time
        start = task.finish_time - task.computation_time
        for i in range(start, min(task.finish_time, sim_time)):
            if i >= 0:
                line[i] = '#'
        print(f"T{task.id}: {''.join(line)}")

def print_timeline_preemptive(tasks: List[Task], sim_time):
    print("\nTimeline:")
    for task in tasks:
        line = ['_'] * sim_time
        for start, end in getattr(task, 'executions', []):
            for i in range(start, min(end, sim_time)):
                if i >= 0:
                    line[i] = '#'
        print(f"T{task.id}: {''.join(line)}")

def print_timeline_realtime(tasks: List[Task], sim_time):
    from collections import defaultdict

    print("\nTimeline:")
    lines = defaultdict(lambda: ['_'] * sim_time)

    for task in tasks:
        tid = f"T{task.id}"
        for start, end in getattr(task, 'executions', []):
            for i in range(start, min(end, sim_time)):
                lines[tid][i] = '#'

    for tid in sorted(lines):
        print(f"{tid}: {''.join(lines[tid])}")

def detect_starvation(tasks: List[Task], sim_time: int, starvation_threshold: int = 0.8):
    starved_tasks = []
    for task in tasks:
        turnaround = task.finish_time - task.offset
        if turnaround == 0:
            continue
        wait_ratio = task.waiting_time / turnaround
        if wait_ratio > starvation_threshold:
            starved_tasks.append((task.id, round(wait_ratio, 2)))
    return starved_tasks


def detect_priority_inversion(tasks: List[Task]):
    inversions = []
    for high in tasks:
        for low in tasks:
            if high.id != low.id:
                if high.quantum < low.quantum and high.offset < low.offset:
                    if high.start_time is not None and low.start_time is not None:
                        if high.start_time > low.start_time:
                            if high.offset <= low.start_time:
                                inversions.append((low.id, high.id, high.start_time))
    return inversions

if __name__ == "__main__":
    sim_time, scheduler, tasks = read_tasks_from_json("simulador_v2\\package.json")

    if scheduler == "FCFS":
        sequence, executed_tasks = simulate_fcfs(sim_time, tasks)
        metrics = calculate_metrics(executed_tasks)
    elif scheduler == "SJF":
        sequence, executed_tasks = simulate_sjf(sim_time, tasks)
        metrics = calculate_metrics(executed_tasks)
    elif scheduler == "RR":
        sequence, executed_tasks = simulate_rr(sim_time, tasks)
        metrics = calculate_metrics(executed_tasks)
    elif scheduler == "SRTF":
        sequence, executed_tasks = simulate_srtf(sim_time, tasks)
        metrics = calculate_metrics(executed_tasks)
    elif scheduler == "RM":
        sequence, executed_tasks = simulate_rm(sim_time, tasks)
        metrics = calculate_metrics_realtime(executed_tasks)
    elif scheduler == "EDF":
        sequence, executed_tasks = simulate_edf(sim_time, tasks)
        metrics = calculate_metrics_realtime(executed_tasks)
    else:
        print("Algoritmo não implementado.")
        exit()

    print("\nSequência de Execução:")
    print(sequence)

    print("\nMétricas:")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    starved = detect_starvation(executed_tasks, sim_time)
    if starved:
        print("\nTarefas com starvation:")
        for tid, ratio in starved:
            print(f"T{tid} (WT/TAT = {ratio})")

    inversions = detect_priority_inversion(executed_tasks)
    if inversions:
        print("\nInversões de prioridade detectadas:")
        for low, high, t in inversions:
            print(f"T{high} (prioridade) foi atrasada por T{low} no tempo {t}")