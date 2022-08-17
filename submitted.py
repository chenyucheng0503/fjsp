from ortools.sat.python import cp_model
import collections
import os
import sys
import time

IntMax = 99999


class Agent:
    def __init__(self, file):
        self.file = file

    def solve_current_model(self):
        """
        read file to solver
        :return:
        """
        starttime = time.time()
        model = cp_model.CpModel()

        with open(self.file, 'r') as f:
            data = f.readlines()

        starts = {}
        ends = {}
        presences = {}
        job_ends = []

        intervals_dict = collections.defaultdict(list)

        for i in range(len(data) - 1):
            index = 1
            item = list(map(lambda x: int(x), data[i + 1].strip(' \n').split(' ')))
            steps = item[0]

            for step in range(steps):
                start = model.NewIntVar(0, IntMax, 'start_{}_{}'.format(i, step))
                duration = model.NewIntVar(0, IntMax, 'dur_{}_{}'.format(i, step))
                end = model.NewIntVar(0, IntMax, 'end_{}{}'.format(i, step))
                interval = model.NewIntervalVar(start, duration, end, 'interval_{}{}'.format(i, step))

                starts[(i, step)] = start
                ends[(i, step)] = end

                # Precedence constraints
                if step > 0:
                    model.Add(start >= ends[(i, step-1)])

                machines = item[index]
                optional_list = []
                for machine in range(machines):
                    m = item[index + machine * 2 + 1]  # machine index
                    process_time = item[index + machine * 2 + 2]

                    optional = model.NewBoolVar('x_{}_{}_{}'.format(i, step, m))
                    _start = model.NewIntVar(0, IntMax, 'startMachine_{}_{}_{}'.format(i, step, m))
                    _duration = process_time
                    _end = model.NewIntVar(0, IntMax, 'endMachine_{}_{}_{}'.format(i, step, m))
                    # 注意是 optionalInterval, 因为工序不一定在这台机器上执行
                    _interval = model.NewOptionalIntervalVar(_start, _duration, _end, optional, 'durMachine_{}_{}_{}'.format(i, step, m))
                    optional_list.append(optional)

                    # 当且仅当 optional == True, 工件和机器的 interval 重合
                    model.Add(start == _start).OnlyEnforceIf(optional)
                    model.Add(duration == _duration).OnlyEnforceIf(optional)
                    model.Add(end == _end).OnlyEnforceIf(optional)

                    intervals_dict[m].append(_interval)
                    presences[(i, step, m)] = optional

                # ExactlyOne(literals) are the same as Sum(literals) == 1.
                # model.Add(sum(optional_list) == 1)
                model.AddExactlyOne(optional_list)

                index += machines * 2 + 1

            job_ends.append(end)

        # no overlap constraint in every machine
        for m in intervals_dict:
            model.AddNoOverlap(intervals_dict[m])

        # objective: makespan
        obj_var = model.NewIntVar(0, IntMax, 'makespan')
        model.AddMaxEquality(obj_var, job_ends)
        # model.Add(sum(job_ends) == obj_var)
        model.Minimize(obj_var)

        solver = cp_model.CpSolver()

        timeduration = time.time() - starttime
        print("build model cost {}s".format(timeduration))
        starttime = time.time()

        # Solve model
        solver.parameters.max_time_in_seconds = 20 * 60.0
        res = solver.Solve(model)

        if res != cp_model.OPTIMAL and res != cp_model.FEASIBLE:
            print("No Feasible Solution Found!")
            return None

        timeduration = time.time() - starttime
        print("solve model cost {}s".format(timeduration))
        solution = {m: [] for m in intervals_dict}

        for item in presences:
            if solver.Value(presences[item]):
                job_id, step, machine = item[0], item[1], item[2]
                start = solver.Value(starts[(job_id, step)])
                end = solver.Value(ends[(job_id, step)])
                solution[machine].append((job_id, step, start, end))
        print("makespan: {}".format(solver.Value(obj_var)))
        # print(solution)
        return solution

    def act(self):
        starttime = time.time()
        solution = self.solve_current_model()
        if not solution:
            return None

        print("solve total cost time: {}s".format(time.time() - starttime))
        print("*" * 50)

        with open(self.file, 'r') as f:
            data = f.readlines()

        info = data[0].split(' ')
        job_nums, machine_nums, _ = int(info[0]), int(info[1]), int(info[2])
        job_list = ['%s' % i for i in list(chr(ord('A')+i) for i in range(0, 26))]
        mach_list = ['M%s' % i for i in range(1, machine_nums + 1)]

        print("Solution in Job order:")
        for i in range(machine_nums):
            machine = mach_list[i]
            print("%s:" % machine, end="")
            for index, item in enumerate(solution[i+1]):
                if index < len(solution[i+1]) - 1:
                    print(f'({job_list[item[0]]},{job_list[item[0]]}{item[1] + 1},{item[2]},{item[3]})', end=",")
                else:
                    print(f'({job_list[item[0]]},{job_list[item[0]]}{item[1] + 1},{item[2]},{item[3]})')

        print()
        print("Solution in Machine order:")
        for i in range(machine_nums):
            machine = mach_list[i]
            print("%s:" % machine, end="")
            s = sorted(solution[i+1], key=lambda x: x[2])
            for index, item in enumerate(s):
                if index < len(solution[i+1]) - 1:
                    print(f'({job_list[item[0]]},{job_list[item[0]]}{item[1] + 1},{item[2]},{item[3]})', end=",")
                else:
                    print(f'({job_list[item[0]]},{job_list[item[0]]}{item[1] + 1},{item[2]},{item[3]})')


if __name__ == '__main__':
    data = './data_final.txt'
    agent = Agent(data)
    agent.act()
