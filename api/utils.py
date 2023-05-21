import numpy as np
# import matplotlib.pyplot as plt
import random
import pandas as pd
import copy
# 先找所有局部最小，依次判断局部最小的前n个和后n个里有没有其他局部最小，如果有就比较哪个更小，删除另一个
# 找到局部最低后，跟上一个局部最低的位置要>order，不然就找两个之间的最低，把高的删除，再保存局部最低的位置和值

def remove_last(l):
    if l:
        l.pop()

def get_minima(test_list,order,low):
    minima = 100000
    minima_posi = -order
    minima_list = []
    for i in range(1, len(test_list) - 1):
        prev = test_list[i] - test_list[i - 1]
        nxt = test_list[i + 1] - test_list[i]
        if (prev < 0) and (nxt > 0) and test_list[i]<=low:
            if minima_posi + order >= i:
                if minima < test_list[i]:
                    pass
                else:
                    remove_last(minima_list)
                    minima_list.append(i)
                    minima = test_list[i]
                    minima_posi = i
            else:
                minima = test_list[i]
                minima_posi = i
                minima_list.append(i)
    return minima_list

def get_maxima(test_list,order,high):
    minima = -100000
    minima_posi = -order
    minima_list = []
    for i in range(1, len(test_list) - 1):
        prev = test_list[i] - test_list[i - 1]
        nxt = test_list[i + 1] - test_list[i]
        if (prev > 0) and (nxt < 0) and test_list[i]>=high:
            if minima_posi + order >= i:
                if minima > test_list[i]:
                    pass
                else:
                    remove_last(minima_list)
                    minima_list.append(i)
                    minima = test_list[i]
                    minima_posi = i
            else:
                minima = test_list[i]
                minima_posi = i
                minima_list.append(i)
    return minima_list

def cut(_df,start,end):
    df = copy.deepcopy(_df)
    df.drop(df[df.t < start].index, inplace=True)
    df.drop(df[df.t > end].index, inplace=True)
    return df

def calculate_average(l):
    length = len(l)
    if length==0: return 0
    sum = 0
    for each in l:
        sum = sum + each
    return sum/length

def calculate_average_in_dict(l,name):
    i = 0
    sum = 0
    for each in l:
        try:
            sum = sum + each[name]
            i = i + 1
        except:
            pass
    if i==0: return 0
    return sum/i

def calculate_CV(l):
    length = len(l)
    ave = calculate_average(l)
    sum = 0
    for each in l:
        sum = sum + (each - ave)**2
    var = sum / (length-1)
    SD = var**0.5
    return SD/ave

def calculate_CV_in_dict(l,name):
    ave = calculate_average_in_dict(l,name)
    if ave==0: return 0
    i = 0
    sum = 0
    for each in l:
        try:
            sum = sum + (each[name] - ave)**2
            i = i + 1
        except:
            pass
    if i-1==0:
        return 0
    var = sum / (i-1)
    SD = var**0.5
    return SD/ave

def cut_by_Y(data,y):
    data = data[data["Y"]<=y]
    start = data.iloc[0,0]
    end = data.iloc[len(data)-1,0]
    data = cut(data,start,end)
    return data

def normalize(data):
    _max = max(data)
    _min = min(data)
    _range = _max-_min
    result = list()
    for each in data:
        temp = (each-_min)/(_range)
        result.append(temp)
    return result

def normalize_Y(data):
    max_Y = max(data["Y"])
    min_Y = min(data["Y"])
    _range = max_Y-min_Y
    result = list()
    for each in data["Y"]:
        temp = (each - min_Y) / (_range)
        result.append(temp)
    data["Y"] = result
    return data

def normalize_t(data):
    max_t = max(data["t"])
    min_t = min(data["t"])
    _range = max_t - min_t
    result = list()
    for each in data["t"]:
        temp = (each - min_t) / (_range)
        result.append(temp)
    data["t"] = result
    y_list = list()
    t_list = list()
    t = 0
    i = 1
    while(t<=1.01):
        while(data.iloc[i,0]<t-0.00001):
            i = i + 1
        y = linearlize(data.iloc[i-1,2],data.iloc[i,2],data.iloc[i-1,0],data.iloc[i,0],t)
        y_list.append(y)
        t_list.append(t)
        t = t + 0.02
        if i==len(data)-1:
            while t<1.01:
                y = linearlize(data.iloc[i - 1, 2], data.iloc[i, 2], data.iloc[i - 1, 0], data.iloc[i, 0], t)
                y_list.append(y)
                t_list.append(t)
                t = t + 0.02
            break
    res_df = pd.DataFrame({"t":t_list,"Y":y_list})
    if len(res_df)!=51:
        raise Exception("normalize_t:res_df!=51")
    return res_df

def linearlize(x0,x1,t0,t1,t):
    result = x0 + (t-t0)/(t1-t0)*(x1-x0)
    return result

def slide_corr(data):
    _data = pd.read_csv("phone/1679301374407.txt",delim_whitespace=True,names=["t", "X", "Y", "Z", "gX", "gY", "gZ"])
    _data["t"] = _data["t"].map(lambda x: (x - _data.iloc[0,0])/1000)
    template = copy.deepcopy(_data)
    template = cut(template,11.76,13.1)

    x = template["Y"].values
    y = data.loc[:, "Y"].values
    x_norm = np.sum((x - np.mean(x))**2)
    y_norm = np.sum((y - np.mean(y))**2)
    corr = np.correlate(x, y, mode='same')
    # corr = normalize(corr)
    # print(len(corr))
    corr_df = pd.DataFrame({"t":data["t"],"corr":corr})
    return corr_df
    # print(corr_df)
    # print(len(x))
    # print(len(y))
    # plt.plot(corr, color='blue')
    #
    # t = data.iloc[0,0]
    # print(t)
    # corr_list = list()
    # j = 0
    # for i in range(first_index,first_index+len(data)-len(template)):
    #     x = template["Y"].values
    #     y = data.loc[i:i+len(template)-1,"Y"].values
    #     corr = np.correlate(x, y, mode='full')
    #     corr = corr[int(len(corr) / 2):]
    #     corr_list.append({"t":t+j*0.04,"corr":corr[0]})
    #     j = j+1
    # corr_df = pd.DataFrame(corr_list)
    # plt.plot(corr_df["corr"], color='red')
    # plt.show()
    # print(corr_df)
    # return corr_df
    # print(len(corr))
    # print(corr_list)
    # fig, axs = plt.subplots(2, 1, constrained_layout=True)
    # axs[0].plot(corr_list)
    # axs[1].plot(data["Y"])
    # plt.show()


