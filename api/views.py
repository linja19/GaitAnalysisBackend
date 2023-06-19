from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
import pandas as pd
from .analysis import *
from json import loads, dumps
from .models import *
import time
from datetime import datetime
import math

@api_view(['GET'])
def get_data(request):
    res = {"1":1}
    return Response(res)

def get_or_create_user(userID):
    try:
        user = User.objects.get(userID=userID)
    except:
        user = User(userID=userID)
        user.save()
    return user

@api_view(['GET'])
def get_param(request,userID):
    user = get_or_create_user(userID)

    double_list = DoubleSupportTime.objects.filter(userID=user)
    double = list()
    for each in double_list:
        timestamp = math.floor(int(each.timestamp.replace(".0",""))/1000)
        # dt_object = datetime.fromtimestamp(timestamp)
        double.append({"timestamp":timestamp,"value":each.value})

    swing_list = SwingVariance.objects.filter(userID=user)
    swing = list()
    for each in swing_list:
        if each.value=='NaN':
            each.delete()
        else:
            timestamp = math.floor(int(each.timestamp.replace(".0", "")) / 1000)
            dt_object = datetime.fromtimestamp(timestamp)
            swing.append({"timestamp":timestamp, "value": each.value})

    assym_list = Asymmetry.objects.filter(userID=user)
    assym = list()
    for each in assym_list:
        timestamp = math.floor(int(each.timestamp.replace(".0", "")) / 1000)
        dt_object = datetime.fromtimestamp(timestamp)
        assym.append({"timestamp":timestamp, "value": each.value})

    res = {"double":double,"variation":swing,"asymm":assym}
    return Response(res)

@api_view(['POST'])
def create_template(request,userID):
    user = get_or_create_user(userID)
    data = request.data
    # print(data)
    df = pd.DataFrame(data)
    df_json_str = df.to_json(orient="records")
    exp = Experiment(userID=user, signal=df_json_str)
    exp.save()
    param = {}
    try:
        res = get_template(df)
        if res.empty:
            return Response({"error":"get template error"})
        json_str = res.to_json(orient="records")
        user.signal = json_str
        user.last_update = str(int(time.time()))
        user.save()
        param = analyze_data(df, res)
        # res = loads(res.to_json(orient="records"))
        df_json_str = df.to_json(orient="records")
        exp = Experiment(userID=user,signal=df_json_str,double=param["Double"],swing=param["SwingVar"],asymm=param["Asymmetry"],timestamp=param["time"])
        exp.save()
    except:
        pass
    return Response(param)

@api_view(['POST'])
def upload_data(request,userID):
    data = request.data
    df = pd.DataFrame(data)
    user = get_or_create_user(userID)
    if user.signal=="":
        return Response({"error":"Didn't found user template signal"})
    template = pd.DataFrame(loads(user.signal))
    res = analyze_data(df,template)
    flag = False
    if not res:
        return Response({"error":"analyze data error"})
    if res["Double"]:
        double = DoubleSupportTime(userID=user,timestamp=res["time"],value=res["Double"])
        double.save()
        flag = True
    if res["Asymmetry"]:
        assym = Asymmetry(userID=user,timestamp=res["time"],value=res["Asymmetry"])
        assym.save()
        flag = True
    if res["SwingVar"] and not res["SwingVar"]=='NaN':
        swingVar = SwingVariance(userID=user,timestamp=res["time"],value=res["SwingVar"])
        swingVar.save()
        flag = True
    if flag:
        return Response(res)
    else:
        return Response({"error": "cannot analyze"})
# df to jsonStr: df.to_json
# json to str: dumps
# str to json: loads

@api_view(['GET'])
def calculate_data(request,experimentID):
    exp = Experiment.objects.get(pk=experimentID)
    df = pd.DataFrame(loads(exp.signal))
    temp = get_template(df)
    res = analyze_data(df,temp)
    return Response(res)

@api_view(['POST'])
def draw(request):
    data = request.data
    df = pd.DataFrame(data)
    plot_diagram(df)
    return Response({})
