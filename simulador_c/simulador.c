#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int pid, arrival, burst, waiting, turnaround, completion, done;
} Process;

int load_processes(const char* filename, Process* p, int max) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        printf("Erro ao abrir o arquivo\n");
        return 0;
    }

    int count = 0;
    while (fscanf(file, "%d %d %d", &p[count].pid, &p[count].arrival, &p[count].burst) == 3 && count < max) {
        p[count].done = 0;
        count++;
    }

    fclose(file);
    return count;
}

void fcfs(Process p[], int n) {
    int time = 0;
    for (int i = 0; i < n; i++) {
        if (time < p[i].arrival)
            time = p[i].arrival;
        p[i].waiting = time - p[i].arrival;
        time += p[i].burst;
        p[i].completion = time;
        p[i].turnaround = p[i].completion - p[i].arrival;
    }

    printf("\nFCFS Scheduling:\n");
    for (int i = 0; i < n; i++)
        printf("P%d WT=%d TAT=%d\n", p[i].pid, p[i].waiting, p[i].turnaround);
    print_detailed_timeline(p, n, time);
}

void sjf(Process p[], int n) {
    int complete = 0, time = 0;
    while (complete < n) {
        int idx = -1, min = 9999;
        for (int i = 0; i < n; i++) {
            if (!p[i].done && p[i].arrival <= time && p[i].burst < min) {
                min = p[i].burst;
                idx = i;
            }
        }

        if (idx == -1) {
            time++;
            continue;
        }

        p[idx].waiting = time - p[idx].arrival;
        time += p[idx].burst;
        p[idx].completion = time;
        p[idx].turnaround = p[idx].completion - p[idx].arrival;
        p[idx].done = 1;
        complete++;
    }

    printf("\nSJF Non-Preemptive Scheduling:\n");
    for (int i = 0; i < n; i++)
        printf("P%d WT=%d TAT=%d\n", p[i].pid, p[i].waiting, p[i].turnaround);
    print_detailed_timeline(p, n, time);
}

void print_detailed_timeline(Process p[], int n, int total_time) {
    printf("\nTimeline detalhada:\n");
    for (int i = 0; i < n; i++) {
        int start = p[i].completion - p[i].burst;
        printf("P%d: ", p[i].pid);
        for (int t = 0; t < total_time; t++) {
            if (t >= p[i].arrival && t < start)
                printf("-");
            else if (t >= start && t < p[i].completion)
                printf("#");
            else
                printf("_");
        }
        printf("\n");
    }
}

int main() {
    Process p[100];
    int n = load_processes("processos.txt", p, 100);

    fcfs(p, n);
    sjf(p, n);

    return 0;
}
