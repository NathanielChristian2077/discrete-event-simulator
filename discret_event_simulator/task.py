class Task:
    def __init__(self, id, offset, computation_time, period_time, quantum, deadline):
        self.id = id
        self.offset = offset
        self.computation_time = computation_time
        self.period_time = period_time
        self.quantum = quantum
        self.deadline = deadline
        self.remaining_time = computation_time
        self.start_time = None
        self.end_time = None