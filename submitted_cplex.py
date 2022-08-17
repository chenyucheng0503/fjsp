from docplex.cp.model import *
import os
import sys
abs_path = os.path.abspath(os.path.dirname(__file__))
os.system(f'chmod -R 777 {abs_path}')
# context.solver.local.execfile = os.path.join(abs_path, "cpoptimizer")
context.solver.agent = 'local'
context.solver.local.execfile = '/Users/4paradigm/Code/fjsp/cpoptimizer'


class Agent:
    def __init__(self, file):
        self.file = file

    def solve_current_model(self):
        
        model = CpoModel()
        
        with open(self.file, 'r') as f:
            data = f.readlines()
        
        job_status = {}
        machine_status = {}
        
        for i in range(len(data)-1):
            index = 1
            item = list(map(lambda x: int(x), data[i+1].strip(' \n').split(' ')))
            steps = item[0]
            job_status[i] = {}    
            job_status[i]['interval'] = interval_var(start=[0, 48*60*60], end=[0, 90*24*60*60])
            # 工序的区间列表
            job_status[i]['step_interval_list'] = interval_var_list(steps)
            # 约束工件 interval
            model.add(span(job_status[i]['interval'], job_status[i]['step_interval_list']))

            # 约束: 每道工序只有在前道工序加工完成后才能进行后道工序加工
            for f in range(1, steps):
                model.add(end_before_start(job_status[i]['step_interval_list'][f-1], job_status[i]['step_interval_list'][f]))
            job_status[i]['machine_interval_list'] = []
            
            for step in range(steps):
                interval_dict = {}              # 存储所有可用的interval
                machines = item[index]
                for machine in range(machines):
                    m = item[index+machine*2+1]     # machine to use
                    # create a machine
                    if m not in machine_status:
                        machine_status[m] = {}
                        machine_status[m]['interval_list'] = []
                    process_time = item[index+machine*2+2]

                    interval = interval_var(length=process_time, optional=True)
                    interval_dict[m] = interval
                    machine_status[m]['interval_list'].append([interval, 1])
                    
                index += machines*2 + 1
                # job_status[i]['step_interval_list'][step]这道工序代表的interval, 只能从interval_dict中选其一
                model.add(alternative(job_status[i]['step_interval_list'][step], interval_dict.values()))

                job_status[i]['machine_interval_list'].append(interval_dict)

        # 在机器上不能同时操作两道工序, 即interval不能重叠, 用 no_overlap 约束也可以实现
        for m in machine_status:
            pulse_list = []
            for interval, n in machine_status[m]['interval_list']:
                pulse_list.append(pulse(interval, n))
            model.add(sum(pulse_list) <= 1)

        makespan = max([end_of(job_status[i]['interval']) for i in list(job_status.keys())])
        model.add_kpi(makespan, "makespan")

        model.add(minimize(makespan))
        res = model.solve(SearchType='Auto',
                          Workers=1,
                          TimeLimit=600,
                          LogVerbosity='Normal')
                
        solution = {m: [] for m in machine_status}
        for i in job_status:
            for f, interval_dict in enumerate(job_status[i]['machine_interval_list']):
                for m, v in interval_dict.items():
                    x = res[v]
                    if(len(x) == 0): continue
                    solution[m].append((i, f, x[0], x[1]))

        #print(solution)
        return solution

    def act(self):
        solution = self.solve_current_model()
        with open(self.file,'r') as f:
            data = f.readlines()
        
        info = data[0].split(' ')
        job_nums,machine_nums,_ = int(info[0]),int(info[1]),int(info[2])
        job_list = ['J%s'%i for i in range(1,job_nums+1)]
        mach_list = ['M%s'%i for i in range(1,machine_nums+1)]
        for i in range(machine_nums):
            machine = mach_list[i]
            print("%s:"%machine,end="")
            for item in solution[i+1]:
                print(f'({job_list[item[0]]},{job_list[item[0]]}_{item[1]+1},{item[2]},{item[3]})')
            print()


config = './data.txt'
agent = Agent(config)
agent.act()
