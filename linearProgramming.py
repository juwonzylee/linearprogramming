import pulp as p
import pandas as pd
import time

def cleanData(filename):
    student_data = pd.read_excel(filename, sheet_name='pivot')
    school_data = pd.read_excel(filename, sheet_name='school_data')
    
    student_num = student_data.shape[0]-2
    school_num = len(school_data.columns)
    school_index_dic = {}
    for i in range(school_num):
        school_index_dic[i] = school_data.columns[i]
    
    return student_data, school_data, school_index_dic, school_num, student_num

def linearProgramming(student_num, school_num, student_data, school_data, school_index_dic):
    # create minimization LP problem
    Lp_prob = p.LpProblem('Problem', p.LpMinimize)

    var_list = []
    for i in range(student_num):
      for j in range(school_num):
        var_list.append("x_%d_%d"%(i,j))

    # objective function
    dist_dic = {}
    for i in range(0,student_num):
      for j in range(0,school_num):
        value = student_data[school_index_dic[j]][i+2]
        dist_dic["x_%d_%d"%(i,j)]=9999 if value!=value else value


    conc_vars = p.LpVariable.dicts("alloc", var_list, 0, 1)

    obj = p.lpSum([dist_dic[i]*conc_vars[i] for i in var_list])
    Lp_prob += obj
    
    # adding constraints
    # student
    for j in range(student_num):
      tmp = p.lpSum([conc_vars[i] for i in var_list if i.split('_')[1]==str(j)])
      Lp_prob += tmp >= 1

    # school
    for k in range(school_num):
      tmp = p.lpSum([conc_vars[i] for i in var_list if i.split('_')[2]==str(k)])
      Lp_prob += tmp <= school_data[school_index_dic[k]][0]
    
    # create solver
    status = Lp_prob.solve(p.COIN(path='/usr/bin/cbc'))
    
    return p.LpStatus[status], conc_vars, var_list

# writing out to excel file
def write_out(student_data, var_list, conc_vars, school_index_dic, school_num, filename):
    allocated = ['','']
    
    k = 0
    length = len(var_list)
    for i in range(0,length,school_num):
        for j in range(school_num):
            if p.value(conc_vars[var_list[i+j]]) == 1:
                allocated.append(school_index_dic[int(var_list[i+j].split('_')[2])])

    student_data['선형계획법 배정학교']= pd.Series(allocated)
    student_data.to_excel(filename)

def main(input_file, output_file):
    student_data, school_data, school_index_dic, school_num, student_num = cleanData(input_file)
    status, conc_vars, var_list = linearProgramming(student_num, school_num, student_data, school_data, school_index_dic)
    write_out(student_data, var_list, conc_vars, school_index_dic, school_num, output_file)

if __name__=='__main__':
    main('seongbuk_1.xlsx', 'seongbuk_1_LP_result.xlsx')