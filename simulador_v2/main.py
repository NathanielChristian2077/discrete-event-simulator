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
                raise ValueError(f"Erro na task {i}: campo vazio -> {e}") from e

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
    sequence = []
    ready_queue = []
    tasks_remaining = tasks[:]
    executed_tasks = []

    for task in tasks:
        task.remaining_time = task.computation_time
        task.executions = []

    current_task = None
    for time in range(sim_time):
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

    print_timeline_preemptive(tasks, sim_time)
    return sequence, executed_tasks

def simulate_rm(sim_time: int, tasks: List[Task]):
    sequence = []
    executed_instances = []
    active_instances = []
    missed_deadlines = {task.id: {"misses": 0, "total": 0} for task in tasks}

    for time in range(sim_time):
        for task in tasks:
            if (time - task.offset) % task.period_time == 0 and time >= task.offset:
                instance = Task(
                    id=task.id,
                    offset=time,
                    computation_time=task.computation_time,
                    period_time=task.period_time,
                    quantum=task.quantum,
                    deadline=time + task.deadline
                )
                instance.remaining_time = instance.computation_time
                instance.executions = []
                active_instances.append(instance)
                missed_deadlines[task.id]["total"] += 1

        ready = [t for t in active_instances if t.offset <= time and t.remaining_time > 0]

        if ready:
            current = min(ready, key=lambda t: t.period_time)
            current.executions.append((time, time + 1))
            current.remaining_time -= 1
            sequence.append(current.id)

            if current.remaining_time == 0:
                current.finish_time = time + 1
                if current.finish_time > current.deadline:
                    missed_deadlines[current.id]["misses"] += 1
                executed_instances.append(current)
        else:
            sequence.append("idle")
    for inst in active_instances:
        if inst.remaining_time > 0 and inst not in executed_instances:
            inst.finish_time = None
            executed_instances.append(inst)

    print_timeline_realtime(executed_instances, sim_time)

    print("\nDeadlines Perdidos (RM):")
    for tid, data in missed_deadlines.items():
        ratio = data["misses"] / data["total"]
        print(f"T{tid} perdeu {data['misses']} de {data['total']} deadlines ({ratio:.2f})")
    return sequence, executed_instances


def simulate_edf(sim_time: int, tasks: List[Task]):
    sequence = []
    executed_instances = []
    active_instances = []
    missed_deadlines = {task.id: {"misses": 0, "total": 0} for task in tasks}

    for time in range(sim_time):
        for task in tasks:
            if (time - task.offset) % task.period_time == 0 and time >= task.offset:
                instance = Task(
                    id=task.id,
                    offset=time,
                    computation_time=task.computation_time,
                    period_time=task.period_time,
                    quantum=task.quantum,
                    deadline=time + task.deadline
                )
                instance.remaining_time = instance.computation_time
                instance.executions = []
                active_instances.append(instance)
                missed_deadlines[task.id]["total"] += 1

        ready = [t for t in active_instances if t.offset <= time and t.remaining_time > 0]

        if ready:
            current = min(ready, key=lambda t: t.deadline)
            current.executions.append((time, time + 1))
            current.remaining_time -= 1
            sequence.append(current.id)

            if current.remaining_time == 0:
                current.finish_time = time + 1
                if current.finish_time > current.deadline:
                    missed_deadlines[current.id]["misses"] += 1
                executed_instances.append(current)
        else:
            sequence.append("idle")
            
    for inst in active_instances:
        if inst.remaining_time > 0 and inst not in executed_instances:
            inst.finish_time = None
            executed_instances.append(inst)

    print_timeline_realtime(executed_instances, sim_time)

    print("\nDeadlines Perdidos (EDF):")
    for tid, data in missed_deadlines.items():
        ratio = data["misses"] / data["total"]
        print(f"T{tid} perdeu {data['misses']} de {data['total']} deadlines ({ratio:.2f})")

    return sequence, executed_instances

def calculate_metrics(tasks: List[Task]):
    completed_tasks = []

    for task in tasks:
        if hasattr(task, "executions") and task.executions:
            total_executed = sum(end - start for start, end in task.executions)
            if total_executed >= task.computation_time:
                completed_tasks.append(task)
            else:
                print(f"\n[AVISO] Tarefa T{task.id} não completou sua execução e será desconsiderada nas métricas.")
        elif task.finish_time and task.finish_time - task.offset >= task.computation_time:
            completed_tasks.append(task)
        else:
            print(f"\n[AVISO] Tarefa T{task.id} não completou sua execução e será desconsiderada nas métricas.")

    if not completed_tasks:
        return {
            "TAT_avg_system": 0,
            "WT_avg_system": 0,
            "TAT_per_task": [],
            "WT_per_task": [],
            "Most_Waiting_Task": None,
            "Least_Waiting_Task": None,
            "CPU_utilization": 0
        }

    tat_list = [task.finish_time - task.offset for task in completed_tasks]
    wt_list = [task.waiting_time for task in completed_tasks]

    return {
        "TAT_avg_system": sum(tat_list) / len(tat_list),
        "WT_avg_system": sum(wt_list) / len(wt_list),
        "TAT_per_task": tat_list,
        "WT_per_task": wt_list,
        "Most_Waiting_Task": max(completed_tasks, key=lambda t: t.waiting_time).id,
        "Least_Waiting_Task": min(completed_tasks, key=lambda t: t.waiting_time).id,
        "CPU_utilization": sum(t.computation_time for t in completed_tasks) / max(t.finish_time for t in completed_tasks)
    }

def calculate_metrics_realtime(instances: List[Task]):
    grouped = defaultdict(list)

    for inst in instances:
        if inst.finish_time is not None:
            grouped[inst.id].append(inst)

    all_task_ids = set(inst.id for inst in instances)
    completed_task_ids = set(grouped.keys())
    incomplete_ids = all_task_ids - completed_task_ids

    for tid in sorted(incomplete_ids):
        print(f"\n[AVISO] Tarefa T{tid} não completou nenhuma instância e será desconsiderada nas métricas.")

    tat_all = []
    wt_all = []
    tat_avg_per_task = {}
    wt_avg_per_task = {}

    for tid, inst_list in grouped.items():
        tats = [inst.finish_time - inst.offset for inst in inst_list]
        wts = [inst.finish_time - inst.offset - inst.computation_time for inst in inst_list]
        tat_avg_per_task[tid] = sum(tats) / len(tats)
        wt_avg_per_task[tid] = sum(wts) / len(wts)
        tat_all.extend(tats)
        wt_all.extend(wts)

    if not tat_all:
        return {
            "TAT_avg_system": 0,
            "WT_avg_system": 0,
            "TAT_avg_per_task": {},
            "WT_avg_per_task": {},
            "Most_Waiting_Task": None,
            "Least_Waiting_Task": None,
            "CPU_utilization": 0
        }

    most_wt = max(wt_avg_per_task.items(), key=lambda x: x[1])[0]
    least_wt = min(wt_avg_per_task.items(), key=lambda x: x[1])[0]
    total_computation = sum(inst.computation_time for insts in grouped.values() for inst in insts)
    total_time = max(inst.finish_time for insts in grouped.values() for inst in insts)

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

def detect_starvation(instances: List[Task], starvation_threshold: float = 0.8):
    starved = []
    for instance in instances:
        if instance.finish_time is None:
            continue

        turnaround = instance.finish_time - instance.offset
        waiting = turnaround - instance.computation_time

        if turnaround > 0:
            wait_ratio = waiting / turnaround
            if wait_ratio > starvation_threshold:
                starved.append({
                    "task_id": instance.id,
                    "offset": instance.offset,
                    "wait_ratio": round(wait_ratio, 2),
                    "waiting_time": waiting,
                    "turnaround": turnaround
                })
    return starved



from typing import List

def detect_priority_inversion(tasks: List[Task], sequence: List[int], sim_time: int, scheduler: str = "EDF"):
    if scheduler not in ["RM", "EDF"]:
        print("Detecção de inversão só implementada para RM e EDF.")
        return []

    inversions = []

    get_priority = (lambda t: t.deadline) if scheduler == "EDF" else (lambda t: t.period_time)

    for t in range(sim_time):
        running_id = sequence[t] if sequence[t] != "idle" else None
        running_priority = None

        ready = [
            task for task in tasks
            if task.offset <= t < task.offset + task.deadline and task.remaining_time > 0
        ]

        if running_id is not None:
            running_tasks = [task for task in ready if task.id == running_id]
            if running_tasks:
                running_priority = get_priority(running_tasks[0])
                if running_priority is None:
                    running_priority = None

        for task in ready:
            if running_id is not None and task.id != running_id:
                task_priority = get_priority(task)

                if task_priority is not None and running_priority is not None:
                    if task_priority < running_priority:
                        inversions.append({
                            "tempo": t,
                            "executando": running_id,
                            "bloqueada": task.id,
                            "prioridade_exec": running_priority,
                            "prioridade_bloq": task_priority
                        })

    return inversions


def report_deadlines_missed(instances: List[Task]):
    print("\nInstâncias que perderam deadlines:")
    any_missed = False
    for task in instances:
        if task.finish_time is not None and task.finish_time > task.deadline:
            delay = task.finish_time - task.deadline
            print(f"- Tarefa T{task.id} (instância com offset {task.offset}): deadline perdido por {delay} unidades de tempo (deadline = {task.deadline}, término = {task.finish_time})")
            any_missed = True
    if not any_missed:
        print("Nenhuma instância perdeu o deadline.")


if __name__ == "__main__":
    sim_time, scheduler, tasks = read_tasks_from_json("simulador_v2\\package2.json")
    from graphs import plot_gantt_chart, plot_gantt_chart_realtime
    if scheduler == "FCFS":
        sequence, executed_tasks = simulate_fcfs(sim_time, tasks)
        metrics = calculate_metrics(executed_tasks)
        plot_gantt_chart(executed_tasks, sim_time)
    elif scheduler == "SJF":
        sequence, executed_tasks = simulate_sjf(sim_time, tasks)
        metrics = calculate_metrics(executed_tasks)
        plot_gantt_chart(executed_tasks, sim_time)
    elif scheduler == "RR":
        sequence, executed_tasks = simulate_rr(sim_time, tasks)
        metrics = calculate_metrics(executed_tasks)
        plot_gantt_chart(tasks, sim_time)
    elif scheduler == "SRTF":
        sequence, executed_tasks = simulate_srtf(sim_time, tasks)
        metrics = calculate_metrics(executed_tasks)
        plot_gantt_chart(tasks, sim_time)
    elif scheduler == "RM":
        sequence, executed_tasks = simulate_rm(sim_time, tasks)
        metrics = calculate_metrics_realtime(executed_tasks)
        report_deadlines_missed(executed_tasks)
        plot_gantt_chart_realtime(executed_tasks, sim_time)
    elif scheduler == "EDF":
        sequence, executed_tasks = simulate_edf(sim_time, tasks)
        metrics = calculate_metrics_realtime(executed_tasks)
        report_deadlines_missed(executed_tasks)
        plot_gantt_chart_realtime(executed_tasks, sim_time)
    else:
        print("Algoritmo não implementado.")
        exit()

    print("\nSequência de Execução:")
    print(sequence)

    print("\nMétricas:")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    if scheduler in ["RM", "EDF"]:
        starved = detect_starvation(executed_tasks)
        if starved:
            print("\nInstâncias com starvation detectado:")
            for s in starved:
                print(f"T{s['task_id']} (offset {s['offset']}): espera = {s['waiting_time']}, TAT = {s['turnaround']}, WT/TAT = {s['wait_ratio']}")
        else:
            print("\nNenhuma instância com starvation.")


    if scheduler in ["RM", "EDF"]:
        inversions = detect_priority_inversion(executed_tasks, sequence, sim_time, scheduler)
        if inversions:
            print("\nInversões de prioridade detectadas:")
            for inv in inversions:
                print(f"Tempo {inv['tempo']}: T{inv['bloqueada']} (mais prioritária) bloqueada por T{inv['executando']}")
        else:
            print("\nNenhuma inversão de prioridade detectada.")