def calc_estatisticas(tasks, sim_time, cpu_use):
    turnaround_times = []
    waiting_times = []

    for task in tasks:
        turnaround = task.end_time - task.offset
        waiting = turnaround - task.computation_time
        turnaround_times.append(turnaround)
        waiting_times.append(waiting)

    return {
        "TAT_avg": sum(turnaround_times) / len(tasks),
        "WT_avg":sum(waiting_times) / len(tasks),
        "Utilizacao": cpu_use / sim_time,
        "Maior_WT": max(waiting_times),
        "Menor_WT": min(waiting_times),
        "task_maior_WT": tasks[waiting_times.index(max(waiting_times))].id,
        "task_menor_WT": tasks[waiting_times.index(min(waiting_times))].id
    }