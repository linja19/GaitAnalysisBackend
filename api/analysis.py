import pandas as pd
# import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from .utils import *
import copy

def analyze_data(_data,template):
    data = copy.deepcopy(_data)
    time = data["t"][len(data) - 1]
    # create figure
    # fig, axs = plt.subplots(3, 1, constrained_layout=True, sharex=True)
    data["t"] = data["t"].map(lambda x: (x - data.iloc[0,0])/1000)

    # lowpass filter data
    b, a = signal.butter(4, 0.8, 'lowpass')
    try:
        filtedDataX = signal.filtfilt(b, a, data["X"])
        filtedDataZ = signal.filtfilt(b, a, data["Z"])
        filtedDataY = signal.filtfilt(b, a, data["Y"])
        filtedDataGZ = signal.filtfilt(b,a,data["gZ"])
        filtedDataGX = signal.filtfilt(b,a,data["gX"])
        filtedDataGY = signal.filtfilt(b,a,data["gY"])
    except Exception as e:
        print(e)
        print(data)
    filted_df = pd.DataFrame(data={"t":data["t"],"Y":filtedDataY,"X":filtedDataX,"Z":filtedDataZ,"gZ":filtedDataGZ,"gX":filtedDataGX,"gY":filtedDataGY})

    accZ_max = max(filtedDataZ)
    gyroX_min = min(filtedDataGX)

    if accZ_max>0.6: accZ_max = 0.3

    # get local extrama list from filtered data
    acc_extrema_list = get_minima(filtedDataY,1,-0.9)
    accZ_maxima_list = get_maxima(filtedDataZ,10,accZ_max)
    accZ_minima_list = get_minima(filtedDataZ,5,-0.1)
    gyro_extrema_list = get_minima(filtedDataGX,15,gyroX_min*0.7)

    if not acc_extrema_list or not gyro_extrema_list or not accZ_maxima_list or not accZ_minima_list:
        return {}

    j = 0
    k = 0
    m = 1
    leftHS_t2 = list()
    leftHS_Z = list()
    leftHS_Y = list()
    rightHS_t2 = list()
    rightHS_Z = list()
    rightHS_Y = list()
    rightTO_t2 = list()
    rightTO_Z = list()
    rightTO_Y = list()
    funda_list = list()
    last_rightHS_t = -1
    for each in accZ_maxima_list:
        n = each
        if gyro_extrema_list[0]>n:
            continue
        while(j<len(accZ_maxima_list) and accZ_maxima_list[j]<n):
            j = j + 1
        HS_t = filted_df.iloc[n]["t"] #accZ的局部最高为同侧触地
        HS_Z = filted_df.iloc[n]["Z"]
        HS_Y = filted_df.iloc[n]["Y"]
        while m<len(gyro_extrema_list)+1 and gyro_extrema_list[m-1]<n:
            m = m + 1
        TO_t = filted_df.iloc[gyro_extrema_list[m-2]]["t"] #HS前的gyroX局部最低为同侧离地
        TO_Z = filted_df.iloc[gyro_extrema_list[m-2]]["Z"]
        TO_Y = filted_df.iloc[gyro_extrema_list[m-2]]["Y"]
        while k<len(acc_extrema_list) and acc_extrema_list[k]<gyro_extrema_list[m-2]:
            k = k + 1
        t = filted_df.iloc[acc_extrema_list[k-1]]["t"]  #TO前的accY局部最低为对侧触地
        Z = filted_df.iloc[acc_extrema_list[k-1]]["Z"]
        Y = filted_df.iloc[acc_extrema_list[k-1]]["Y"]

        # gait parameter
        funda_dict = {}
        rightHS_flag = False
        leftHS_flag = False
        if TO_t-t>0.1 and TO_t-t<0.2: # stance
            leftHS_t2.append(t)
            leftHS_Z.append(Z)
            leftHS_Y.append(Y)
            stance_t = TO_t - t
            funda_dict["leftHS_t"] = t
            funda_dict["stance_t"] = stance_t
            rightHS_flag = True
        if HS_t - TO_t<0.6 and HS_t-TO_t>0.3: # swing
            rightHS_t2.append(HS_t)
            rightHS_Z.append(HS_Z)
            rightHS_Y.append(HS_Y)
            rightTO_t2.append(TO_t)
            rightTO_Z.append(TO_Z)
            rightTO_Y.append(TO_Y)
            swing_t = HS_t - TO_t
            funda_dict["rightHS_t"] = HS_t
            funda_dict["rightTO_t"] = TO_t
            funda_dict["swing_t"] = swing_t
            leftHS_flag = True
            last_rightHS_flag = True
        else:
            last_rightHS_flag = False
        if leftHS_flag and last_rightHS_flag and rightHS_flag and last_rightHS_t>0:
            left = HS_t - t
            right = t - last_rightHS_t
            # print("left",left)
            # print("right",right)
            symm = left / right
            funda_dict["symmetry"] = abs(1-symm)
        last_rightHS_t = HS_t
        if bool(funda_dict):
            funda_list.append(funda_dict)
        # max: 0.2/(0.3+0.2)=0.4
        # min: 0.1/(0.6+0.1)=0.14

    if not funda_list: return {}

    delta_t = list()
    template_list = list()
    for i in range(len(funda_list) - 1):
        try:
            _t = funda_list[i + 1]["rightHS_t"] - funda_list[i]["rightHS_t"]
            delta_t.append(_t)
        except:
            pass

    med = calculate_average(delta_t)
    j = 0
    template_list.append([])
    template_list[j].append(funda_list[0])
    for i in range(len(funda_list) - 1):
        try:
            _t = funda_list[i + 1]["rightHS_t"] - funda_list[i]["rightHS_t"]
            if _t * 0.8 > med:
                j = j + 1
                template_list.append([])
            template_list[j].append(funda_list[i+1])
        except:
            pass

    final_list = list()
    for each_list in template_list:
        for i in range(len(each_list) - 1):
            _start = each_list[i]["rightHS_t"]
            _end = each_list[i + 1]["rightHS_t"]
            p = cut(data, _start, _end)
            p = normalize_t(p)
            p = normalize_Y(p)
            norm_a = np.linalg.norm(p["Y"])
            p["Y"] = p["Y"] / norm_a
            corr = np.correlate(template["Y"], p["Y"], mode='valid')
            # if i == 1:
            #     print(1)
            #     plt.plot(p["Y"])
            #     plt.plot(template["Y"], color='red')
            #     plt.show()
            if corr > 0.95:
                final_list.append(each_list[i])

    ave_stance = calculate_average_in_dict(final_list,"stance_t")
    ave_swing = calculate_average_in_dict(final_list,"swing_t")
    if ave_swing+ave_stance==0:
        ave_double = 0
    else:
        ave_double = ave_stance / (ave_swing + ave_stance)
    ave_symm = calculate_average_in_dict(final_list,"symmetry")

    print("after correlation")
    print("Double", ave_double * 100)
    print("Coefficient of Variation Swing ", str(calculate_CV_in_dict(final_list,"swing_t")))
    print("Asymmetry ", ave_symm)

    # figure
    # def plot():
        # axs[1].set_xlabel('time(s)', fontsize=15)
        # axs[1].set_ylabel('Angular Speed', fontsize=15)
        # axs[1].set_title("Angular Speed with Time")
        # axs[0].plot(filted_df["t"],filted_df["Y"],label="Filtered0.8_Y_left", color='red', alpha=0.8)
        # axs[1].plot(filted_df["t"],filted_df["gX"],label="Filtered0.8_GX_left", color='red', alpha=0.8)
        # axs[0].scatter(
        #     filted_df.iloc[acc_extrema_list]["t"],
        #     filted_df.iloc[acc_extrema_list]["Y"],
        #     c='red',
        #     alpha=0.5,
        #     label='minima'
        # )
        # axs[0].scatter(
        #     filted_df.iloc[acc_maxima_list]["t"],
        #     filted_df.iloc[acc_maxima_list]["Y"],
        #     c='black',
        #     alpha=0.5,
        #     label='minima'
        # )
        # axs[0].set_xlabel('time(s)', fontsize=15)
        # axs[0].set_ylabel('Acceleration Y', fontsize=15)
        # axs[0].set_title("Acceleration Y with Time")
        #
        # axs[1].scatter(
        #     filted_df.iloc[gyro_extrema_list]["t"],
        #     filted_df.iloc[gyro_extrema_list]["gX"],
        #     c='blue',
        #     label='minima'
        # )
        # axs[2].plot(filted_df["t"],filted_df["Z"],label="Filtered0.8_Y_left", color='red')
        # axs[2].set_xlabel('time(s)', fontsize=15)
        # axs[2].set_ylabel('Acceleration Z', fontsize=15)
        # axs[2].set_title("Acceleration Z with Time")

        # axs[2].scatter(
        #     filted_df.iloc[accZ_maxima_list]["t"],
        #     filted_df.iloc[accZ_maxima_list]["Z"],
        #     c='blue',
        #     label='maxima'
        # )
        # axs[2].scatter(
        #     filted_df.iloc[accZ_minima_list]["t"],
        #     filted_df.iloc[accZ_minima_list]["Z"],
        #     c='green',
        #     label='minima'
        # )
        # axs[0].scatter(
        #     leftHS_t2,
        #     leftHS_Y,
        #     c='green',
        #     label='right Heel Strike'
        # )
        # axs[0].scatter(
        #     rightTO_t2,
        #     rightTO_Y,
        #     c='purple',
        #     label='left Toe Off'
        # )
        # axs[0].scatter(
        #     rightHS_t2,
        #     rightHS_Y,
        #     c='black',
        #     label='left Heel Strike'
        # )
        # axs[2].scatter(
        #     leftHS_t2,
        #     leftHS_Z,
        #     c='green',
        #     label='right Heel Strike'
        # )
        # axs[2].scatter(
        #     rightTO_t2,
        #     rightTO_Z,
        #     c='purple',
        #     label='left Toe Off'
        # )
        # axs[2].scatter(
        #     rightHS_t2,
        #     rightHS_Z,
        #     c='black',
        #     label='left Heel Strike'
        # )
        # axs[0].legend()
        # axs[1].legend()
        # axs[2].legend()
        # plt.show()
    # plot()

    result = {
        "Double":ave_double*100,
        "SwingVar":calculate_CV_in_dict(final_list,"swing_t"),
        "Asymmetry":ave_symm,
        "time": time
    }
    return result

def get_template(_data):
    data = copy.deepcopy(_data)
    data["t"] = data["t"].map(lambda x: (x - data.iloc[0,0])/1000)

    # lowpass filter data
    b, a = signal.butter(4, 0.7, 'lowpass')
    filtedDataX = signal.filtfilt(b, a, data["X"])
    filtedDataZ = signal.filtfilt(b, a, data["Z"])
    filtedDataY = signal.filtfilt(b, a, data["Y"])
    filtedDataGZ = signal.filtfilt(b,a,data["gZ"])
    filtedDataGX = signal.filtfilt(b,a,data["gX"])
    filtedDataGY = signal.filtfilt(b,a,data["gY"])
    filted_df = pd.DataFrame(data={"t":data["t"],"Y":filtedDataY,"X":filtedDataX,"Z":filtedDataZ,"gZ":filtedDataGZ,"gX":filtedDataGX,"gY":filtedDataGY})

    gyroX_min = min(filtedDataGX)
    accZ_max = max(filtedDataZ)

    if accZ_max > 0.6: accZ_max = 0.3

    # get local extrama list from filtered data
    acc_extrema_list = get_minima(filtedDataY,1,-0.9)
    gyro_extrema_list = get_minima(filtedDataGX,1,gyroX_min*0.7)
    accZ_maxima_list = get_maxima(filtedDataZ, 10, accZ_max)
    accZ_minima_list = get_minima(filtedDataZ, 5, -0.1)

    if not acc_extrema_list or not gyro_extrema_list or not accZ_maxima_list or not accZ_minima_list:
        return pd.DataFrame()

    j = 0
    k = 0
    m = 1

    funda_list = list()
    last_rightHS_t = -1
    for each in accZ_maxima_list:
        n = each
        if gyro_extrema_list[0] > n:
            continue
        while (accZ_maxima_list[j] < n):
            j = j + 1
        HS_t = filted_df.iloc[n]["t"]  # accZ的局部最高为同侧触地
        # HS_Z = filted_df.iloc[n]["Z"]
        # HS_Y = filted_df.iloc[n]["Y"]
        while m < len(gyro_extrema_list) + 1 and gyro_extrema_list[m - 1] < n:
            m = m + 1
        TO_t = filted_df.iloc[gyro_extrema_list[m - 2]]["t"]  # HS前的gyroX局部最低为同侧离地
        # TO_Z = filted_df.iloc[gyro_extrema_list[m - 2]]["Z"]
        # TO_Y = filted_df.iloc[gyro_extrema_list[m - 2]]["Y"]
        while acc_extrema_list[k] < gyro_extrema_list[m - 2]:
            k = k + 1
        t = filted_df.iloc[acc_extrema_list[k - 1]]["t"]  # TO前的accY局部最低为对侧触地
        # Z = filted_df.iloc[acc_extrema_list[k - 1]]["Z"]
        # Y = filted_df.iloc[acc_extrema_list[k - 1]]["Y"]

        # gait parameter
        funda_dict = {}
        rightHS_flag = False
        leftHS_flag = False
        if TO_t - t > 0.1 and TO_t - t < 0.2:  # stance
            stance_t = TO_t - t
            funda_dict["leftHS_t"] = t
            funda_dict["stance_t"] = stance_t
            rightHS_flag = True
        if HS_t - TO_t < 0.6 and HS_t - TO_t > 0.3:  # swing
            swing_t = HS_t - TO_t
            funda_dict["rightHS_t"] = HS_t
            funda_dict["rightTO_t"] = TO_t
            funda_dict["swing_t"] = swing_t
            leftHS_flag = True
            last_rightHS_flag = True
        else:
            last_rightHS_flag = False
        if leftHS_flag and last_rightHS_flag and rightHS_flag and last_rightHS_t > 0:
            left = HS_t - t
            right = t - last_rightHS_t
            symm = left / right
            funda_dict["symmetry"] = abs(1 - symm)
        last_rightHS_t = HS_t
        if bool(funda_dict):
            funda_list.append(funda_dict)
        # max: 0.2/(0.3+0.2)=0.4
        # min: 0.1/(0.6+0.1)=0.14

    delta_t = list()
    template_list = list()
    for i in range(len(funda_list) - 1):
        try:
            _t = funda_list[i + 1]["rightHS_t"] - funda_list[i]["rightHS_t"]
            delta_t.append(_t)
        except:
            pass
    med = calculate_average(delta_t)
    j = 0
    template_list.append([])
    if len(funda_list) == 0:
        return pd.DataFrame()
    template_list[j].append(funda_list[0])
    for i in range(len(funda_list) - 1):
        try:
            _t = funda_list[i + 1]["rightHS_t"] - funda_list[i]["rightHS_t"]
            if _t * 0.8 > med:
                j = j + 1
                template_list.append([])
            template_list[j].append(funda_list[i + 1])
        except:
            pass
    total_len = len(funda_list) - j - 1
    average_Y_list = np.zeros(51)
    p = pd.DataFrame()
    for each_list in template_list:
        for i in range(len(each_list)-1):
            _start = each_list[i]["rightHS_t"]
            _end = each_list[i+1]["rightHS_t"]
            p = cut(data,_start,_end)
            p = normalize_t(p)
            # if i == 1:
            #     plt.plot(p["t"], p["Y"], color='red', label='original')
            #     p = normalize_Y(p)
            #     a = p["Y"]
            #     norm_a = np.linalg.norm(a)
            #     a = a / norm_a
            #     plt.plot(p["t"], a, color='blue',label='normalized')
            #     plt.xlabel("time(s)")
            #     plt.ylabel("Acceleration Y")
            #     plt.legend()
            #     plt.show()
            average_Y_list = average_Y_list + p["Y"]/total_len
    if not p.empty:
        p["Y"] = average_Y_list
        p = normalize_Y(p)
    return p