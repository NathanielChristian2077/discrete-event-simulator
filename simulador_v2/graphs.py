from typing import List
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from main import Task

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import List

def plot_gantt_chart(tasks: List, sim_time: int, title="Gantt Chart"):
    fig, ax = plt.subplots(figsize=(10, len(tasks) * 0.8))

    # Definindo cores únicas por tarefa
    color_map = {}
    colors = plt.cm.get_cmap("tab10", len(tasks))

    for idx, task in enumerate(tasks):
        tid = f"T{task.id}"
        if tid not in color_map:
            color_map[tid] = colors(idx)

        # Para métodos não-preemptivos (FCFS, SJF), construímos 'executions'
        if not hasattr(task, 'executions') or not task.executions:
            task.executions = [(task.start_time, task.finish_time)]

        for start, end in task.executions:
            ax.barh(y=tid, width=end - start, left=start, height=0.6,
                    color=color_map[tid], edgecolor='black')

    ax.set_xlabel("Tempo")
    ax.set_ylabel("Tarefas")
    ax.set_title(title)
    ax.set_xlim(0, sim_time)
    ax.set_yticks([f"T{task.id}" for task in tasks])
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)

    # Legenda
    patches = [mpatches.Patch(color=color_map[f"T{task.id}"], label=f"T{task.id}") for task in tasks]
    ax.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    plt.show()


def plot_gantt_chart_realtime(instances: List[Task], sim_time: int, title="Gantt Chart (Tempo Real)"):
    fig, ax = plt.subplots(figsize=(12, len(instances) * 0.5))

    color_map = {}
    colors = plt.cm.get_cmap("tab10", 10)  # até 10 tarefas

    # Nomear instâncias: T0_0, T0_1...
    instance_labels = []
    task_instance_counts = {}

    for inst in instances:
        tid = inst.id
        task_instance_counts[tid] = task_instance_counts.get(tid, 0)
        label = f"T{tid}_{task_instance_counts[tid]}"
        instance_labels.append((label, inst))
        task_instance_counts[tid] += 1

    # Plotagem
    yticks = []
    yticklabels = []
    legend_labels = {}

    for y, (label, inst) in enumerate(instance_labels):
        base_color = colors(inst.id % 10)
        legend_labels[f"T{inst.id}"] = base_color

        # Determinar cor (vermelho se perdeu deadline)
        color = 'red' if inst.finish_time and inst.finish_time > inst.deadline else base_color

        for start, end in inst.executions:
            ax.barh(y=label, width=end - start, left=start, height=0.6,
                    color=color, edgecolor='black')

        # Linha de deadline
        ax.axvline(inst.deadline, color='gray', linestyle='--', linewidth=1)

        yticks.append(label)
        yticklabels.append(label)

    ax.set_xlabel("Tempo")
    ax.set_ylabel("Instâncias")
    ax.set_title(title)
    ax.set_xlim(0, sim_time)
    ax.set_yticks(range(len(yticks)))
    ax.set_yticklabels([lbl for lbl, _ in instance_labels])
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)

    # Legenda
    patches = [mpatches.Patch(color=color, label=task)
            for task, color in legend_labels.items()]
    patches.append(mpatches.Patch(color='red', label='Deadline perdido'))
    ax.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    plt.show()
