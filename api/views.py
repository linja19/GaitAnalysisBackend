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
    return user

@api_view(['GET'])
def get_param(request,userID):
    user = get_or_create_user(userID)

    double_list = DoubleSupportTime.objects.filter(userID=user)
    double = list()
    for each in double_list:
        timestamp = math.floor(int(each.timestamp.replace(".0",""))/1000)
        dt_object = datetime.fromtimestamp(timestamp)
        double.append({"date":dt_object.strftime("%m/%d"),"value":each.value})

    swing_list = SwingVariance.objects.filter(userID=user)
    swing = list()
    for each in swing_list:
        timestamp = math.floor(int(each.timestamp.replace(".0", "")) / 1000)
        dt_object = datetime.fromtimestamp(timestamp)
        swing.append({"date": dt_object.strftime("%m/%d"), "value": each.value})

    assym_list = Asymmetry.objects.filter(userID=user)
    assym = list()
    for each in assym_list:
        timestamp = math.floor(int(each.timestamp.replace(".0", "")) / 1000)
        dt_object = datetime.fromtimestamp(timestamp)
        assym.append({"date": dt_object.strftime("%m/%d"), "value": each.value})

    res = {"double":double,"variation":swing,"assym":assym}
    return Response(res)

@api_view(['POST'])
def create_template(request,userID):
    data = request.data
    # print(data)
    df = pd.DataFrame(data)
    res = get_template(df)
    if res.empty:
        return Response({"error":"get template error"})
    json_str = res.to_json(orient="records")
    user = get_or_create_user(userID)
    user.signal = json_str
    user.last_update = str(int(time.time()))
    user.save()
    param = analyze_data(df, res)
    # res = loads(res.to_json(orient="records"))
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
    if not res:
        return Response({"error":"analyze data error"})
    if res["Double"]:
        double = DoubleSupportTime(userID=user,timestamp=res["time"],value=res["Double"])
        double.save()
    if res["Asymmetry"]:
        assym = Asymmetry(userID=user,timestamp=res["time"],value=res["Asymmetry"])
        assym.save()
    if res["SwingVar"]:
        swingVar = SwingVariance(userID=user,timestamp=res["time"],value=res["SwingVar"])
        swingVar.save()
    return Response(res)
# df to jsonStr: df.to_json
# json to str: dumps
# str to json: loads