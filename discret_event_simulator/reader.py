import json
from task import Task

def read(path):
    with open(path, 'r') as file:
        data = json.load(file)
    tasks = []
    for i, task in enumerate(data['tasks']):
        try:
            tasks.append(Task(i,
                              task["offset"],
                              task["computation_time"],
                              task["period_time"],
                              task["quantum"],
                              task["deadline"]
                              ))
        except KeyError as e:
            raise ValueError(f"Erro na task {i}: campo vazio -> {e}")
        
    return data['simulation_time'], data['scheduler_name'], tasks