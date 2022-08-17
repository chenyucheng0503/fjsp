from ortools.sat.python import cp_model
import collections
import os
import sys
import time

IntMax = 99999


class Agent:
    def __init__(self, file):
        self.file = file

    def solve_model(self):
        model = cp_model.CpModel()

        with open(self.file, 'r') as f:
            data = f.readlines()

        information = list(map(lambda x: int(x), data[0].strip(' \n').split(' ')))
        job_num = information[0]
        machine_num = information[1]

        start_time_map = {}
        process_time_map = {}
        d_map = {}
        Tm_map = {}

        for k in range(machine_num):
            d_map[k] = model.NewIntVar(0, job_num*machine_num, '')

        for i in range(job_num):
            index = 1
            item = list(map(lambda x: int(x), data[i + 1].strip(' \n').split(' ')))
            operation_num = item[0]

            for j in range(operation_num):
                start_time_decided = model.NewIntVar(0, IntMax, '')
                process_time_decided = model.NewIntVar(0, IntMax, '')

                start_time_map[(i, j)] = start_time_decided
                process_time_map[(i, j)] = process_time_decided

                constraint_2 = None
                for k in range(machine_num):
                    process_time = model.NewIntVar(0, IntMax, '')
                    v = model.NewIntVar(0, 1, '')
                    if constraint_2:
                        constraint_2 += process_time * v


                # constraint 2
                model.Add(constraint_2 == process_time_decided)

                # constraint 3
                if j != 0:
                    model.Add(start_time_map[(i, j-1)] + process_time_map[(i, j-1)] <= start_time_decided)








    def print_solution(self):
        pass


if __name__ == '__main__':
    data = './data.txt'
    agent = Agent(data)
    agent.act()
