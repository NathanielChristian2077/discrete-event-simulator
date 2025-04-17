from reader import read
from simulators import fcfs
from simulators import sjf
from util import calc_estatisticas


sim_time, scheduler, tasks = read("file.json")
if scheduler == "FCFS":
    execution, cpu_use = fcfs(sim_time, tasks)
#elif scheduler == "SJF":
#    execution, cpu_use = sjf(sim_time, tasks)
else:
    raise ValueError("Scheduler desconhecido.")
print("Execucao: ", execution)
stats = calc_estatisticas(tasks, sim_time, cpu_use)
for key, value in stats.items():
    print(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")