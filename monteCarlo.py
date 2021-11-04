import pandas as pd
import random
import numpy as np
import pulp as p
import time
import glob

def cleanData(filename):
    student_data = pd.read_excel(filename, sheet_name='pivot')
    school_data = pd.read_excel(filename, sheet_name='coding_total')
    
    school_index_dic = {}
    school_index_dic[0]=''
    school_index_dic[1]=''
    school_index_dic[2]=''
    school_index_dic[3]=''
    school_index_dic[4]=''
    school_index_dic[5]=''
    school_index_dic[6]='' # 남중
    school_index_dic[7]='' # 여중
    school_index_dic[8]='' # 여중
    school_index_dic[9]=''
    school_index_dic[10]=''
    school_index_dic[11]=''
    school_index_dic[12]=''
    
    student_data['몬테카를로'] = ''

    return student_data, school_data, school_index_dic

def monteCarlo(percent, student_data, school_data, school_index_dic):
    student_data['몬테카를로'] = ''
    # dictionary with school name as key, monte carlo 적용할 정원수 as value
    applied_dic = {}
    non_applied_dic = {}
    applied_percent = percent # monte carlo > 0.2, 0.4, 0.6, 0.8

    for i in range(school_num):
        applied_dic[school_index_dic[i]] = int(applied_percent*school_data[school_index_dic[i]][0])
        non_applied_dic[school_index_dic[i]] = school_data[school_index_dic[i]][0] - int(applied_percent*school_data[school_index_dic[i]][0])
        
    # catching NaN cases for gender specific schools
    female = []
    male = []
    for i in range(student_num):
        if student_data[school_index_dic[7]][i + 2] == student_data[school_index_dic[7]][i + 2]:
            female.append(i)
        elif student_data[school_index_dic[8]][i + 2] == student_data[school_index_dic[8]][i + 2]:
            female.append(i)
        elif student_data[school_index_dic[6]][i + 2] == student_data[school_index_dic[6]][i + 2]:
            male.append(i)

    # 학교별로 applied_percent만큼 랜덤으로 학생 뽑아오기
    applied_index = {}
    for k in range(school_num): # 학교별 랜덤으로 뽑은 학생 인덱스 담을 리스트 초기화
        applied_index[k] = []

    left_index = list(range(student_num))
    for k in range(school_num):
        applied = applied_dic[school_index_dic[k]]

        if k == 7 or k == 8: # 여중
            for index in random.sample(female,applied):
                if index in left_index:
                    applied_index[k].extend([index])
                    left_index.remove(index)
                    female.remove(index)
                    student_data.at[index+2,'몬테카를로'] = school_index_dic[k]

        elif k == 6: # 남중
            for index in random.sample(male,applied):
                if index in left_index:
                    applied_index[k].extend([index])
                    left_index.remove(index)
                    male.remove(index)
                    student_data.at[index+2,'몬테카를로'] = school_index_dic[k]

        else: # 남녀공학
            for index in random.sample(left_index,applied):
                if index in female:
                    female.remove(index)
                elif index in male:
                    male.remove(index)
                applied_index[k].extend([index])
                left_index.remove(index)
                student_data.at[index+2,'몬테카를로'] = school_index_dic[k]
    
    return applied_dic, non_applied_dic, applied_index, left_index

def linearProgramming(left_index, student_data, school_data, school_index_dic):
    # create minimization LP problem
    Lp_prob = p.LpProblem('Problem', p.LpMinimize)

    var_list = []
    for i in left_index:
      for j in range(school_num):
        var_list.append("x_%d_%d"%(i,j))

    # objective function
    dist_dic = {}
    for i in left_index:
      for j in range(0,school_num):
        value = student_data[school_index_dic[j]][i+2]
        dist_dic["x_%d_%d"%(i,j)]=9999 if value!=value else value


    conc_vars = p.LpVariable.dicts("alloc", var_list, 0, 1)

    obj = p.lpSum([dist_dic[i]*conc_vars[i] for i in var_list])
    Lp_prob += obj
    
    # adding constraints
    # student
    for j in left_index:
      tmp = p.lpSum([conc_vars[i] for i in var_list if i.split('_')[1]==str(j)])
      Lp_prob += tmp >= 1

    # school
    for k in range(school_num):
      tmp = p.lpSum([conc_vars[i] for i in var_list if i.split('_')[2]==str(k)])
      Lp_prob += tmp <= non_applied_dic[school_index_dic[k]]
    
    # create solver
    status = Lp_prob.solve(p.COIN(path='/usr/bin/cbc'))
    
    # add results to student_data dataframe
    length = len(var_list)
    for i in range(0,length,13):
        for j in range(13):
            if p.value(conc_vars[var_list[i+j]]) == 1:
                student_data.at[2+int(var_list[i+j].split('_')[1]), '몬테카를로'] = school_index_dic[int(var_list[i+j].split('_')[2])]
    
    return p.LpStatus[status], conc_vars, var_list

def createPivot(student_data, percent, repeat_index):
    # 배정중학교에 상응하는 거리를 새컬럼에 추가
    student_data['몬테카를로 거리'] = np.nan
    for i in range(2,2480):
        school_name = student_data['몬테카를로'][i]
        dist = student_data[school_name][i]
        student_data.at[i,'몬테카를로 거리'] = dist
        
    # 후 피벗
    piv = pd.pivot_table(student_data,index=['몬테카를로'],values=['몬테카를로 거리'], aggfunc=[np.mean])
    piv.reset_index(inplace=True)
    
    # write out csv file with pivot table
    piv.to_csv('./results/monte%s_piv%s.csv'%(percent, repeat_index))
    
    return piv

def repeatMonteCarlo(repeat_num, mc_percent):
    student_num = 2478 # 2478 2학교군 학생수
    school_num = 13 # 13개 강동2학교군학교
    student_data, school_data, school_index_dic = cleanData('pivot.xlsx')
    for i in range(repeat_num):
        start_time = time.time()
        applied_dic, non_applied_dic, applied_index, left_index = monteCarlo(mc_percent, student_data, school_data, school_index_dic)
        status, conc_vars, var_list = linearProgramming(left_index, student_data, school_data, school_index_dic)
        createPivot(student_data, mc_percent, i) # write out pivot table for each ith run
        student_data['몬테카를로'] = ''
        print("execution time for %d: %s seconds"%(i, time.time()-start_time))
    return student_data

def outputAverage(mc_percent):
    all_files = glob.glob("./results/monte%s_piv*.csv"%(mc_percent))

    tmp = []

    for filename in all_files:
        df = pd.read_csv(filename)
        df = df.drop([0])
        tmp.append(df)

    frame = pd.concat(tmp, axis=0, ignore_index=True)
    frame['mean'] = frame['mean'].astype(float)

    piv = pd.pivot_table(frame,index=['몬테카를로'],values=['mean'], aggfunc=[np.mean])
    piv.to_csv('./results/monte%s_res'%(mc_percent))
    
    return piv 

def main():
    repeatMonteCarlo(30,0.2)
    outputAverage(0.2)
    
    repeatMonteCarlo(30,0.4)
    outputAverage(0.4)
    
    repeatMonteCarlo(30,0.6)
    outputAverage(0.6)
    
    repeatMonteCarlo(30,0.8)
    outputAverage(0.8)

if __name__ == '__main__':
    main()