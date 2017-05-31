#building off of calc/contracts/management/commands
import os
import logging
import asyncio
import pandas as pd
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.core.management import BaseCommand
from optparse import make_option
from django.core.management import call_command
import statistics as st
import numpy as np
from price_prediction.models import LaborCategory, OverallSpread
import shutil
from scipy import stats
import json
import plotly
from plotly.graph_objs import Bar,Layout,Scatter, Box, Annotation,Marker,Font,XAxis,YAxis
    

#write tests for this -

# make sure each of these functions performs appropriately
# - smoke test
# - (minimal) doc tests
# - edge cases
# - check to make sure data is saved to the database

def is_nan(obj):
    if type(obj) == type(float()):
        return math.isnan(obj)
    else:
        return False


def count_outliers(data):
    outliers_num = 0
    mean = st.mean(data)
    stdev = st.stdev(data)
    for elem in data:
        if (elem > mean + (2*stdev)) or (elem < mean - (2*stdev)):
            outliers_num += 1
    return outliers_num

def first_quartile(List):
    if len(List) >= 4:
        List.sort()
        if len(List) % 2 != 0:
            middle_number = st.median(List)
            return st.median(List[:List.index(middle_number)])
        else:
            middle_index = len(List)//2
            middle_number = List[middle_index]
            return st.median(List[:List.index(middle_number)])
    else:
        return None    

#Question 9
#Write a python function implementing a function that returns the first quantile of a set of numbers
def third_quartile(List):
    if len(List) >= 4:
        List.sort()
        if len(List) % 2 != 0:
            middle_number = st.median(List)
            return st.median(List[List.index(middle_number):])
        else:
            middle_index = len(List)//2
            middle_number = List[middle_index]
            return st.median(List[List.index(middle_number):])
    else:
        return None    

def quartile_analysis(data):
    q1 = first_quartile(data)
    q3 = third_quartile(data)
    median = st.median(data)
    if abs(median - q1) > abs(median - q3):
        return abs(median - q1)
    else:
        return abs(median - q3)

def big_picture_analysis(labor_data):
    categories = set([elem.labor_category for elem in labor_data])
    central_tendency = []
    spread = []
    outliers = []
    iqrs = []
    for category in categories:
        data = LaborCategory.objects.filter(labor_category=category).all()
        prices = [round(float(elem.price),2) for elem in data]
        if len(prices) > 5 and stats.normaltest(prices).pvalue > 0.05:
            spread.append([category, st.stdev(prices)])
            central_tendency.append([category, st.mean(prices)])
        else:
            try:
                spread.append([category, quartile_analysis(prices)])
            except:
                spread.append([category, min_max(prices)])
            central_tendency.append([category, st.median(prices)])
        outliers.append([category, count_outliers(prices)])
    sorted(central_tendency, key=lambda x: x[1])
    sorted(spread, key=lambda x: x[1])
    sorted(outliers, key=lambda x: x[1])
    bar_plot(central_tendency,"center.html")
    bar_plot(spread,"spread.html")
    bar_plot(outliers,"outlier_count.html")
    print("central tendency",st.median([elem[1] for elem in  central_tendency]))
    print("spread",st.median([elem[1] for elem in spread]))
    print("outliers",st.median([elem[1] for elem in outliers]))

def bar_plot(data,filename):
    filename = "/Users/ericschles/Documents/projects/calc/price_prediction/"+filename
    x_vals = [elem[0] for elem in  data]
    y_vals = [elem[1] for elem in data]
        
    plotly.offline.plot({
        "data":[Bar(x=x_vals,y=y_vals)],
        "layout":Layout(
            title=filename.split(".")[0]
        )
    },auto_open=False)
    shutil.move("temp-plot.html",filename)

def min_max(data):
    data.sort()
    return abs(data[-1] - data[0])

def plot_individual_timeseries(data,years,category):
    x_vals = []
    y_vals = []
    for year in years:
        try:
            y_vals.append(data[year])
            x_vals.append(year)
        except:
            continue
    plotly.offline.plot({
        "data":[Scatter(x=x_vals,y=y_vals)],
        "layout":Layout(
            title=category
        )
    },auto_open=False)
    category = category.replace("/","_").replace(",","_")
    
    category = "_".join(category.lower().split())
    if len(category) > 40:
        category = category.split("_")[0]
    shutil.move("temp-plot.html","/Users/ericschles/Documents/projects/calc/price_prediction/viz/"+category+".html")     

def timeseries_plot(data,filename,city):
    scatters = []
    for key in data.keys():
        x_vals = [elem[0] for elem in data[key]]
        y_vals = [elem[1] for elem in data[key]]
        scatters.append(Scatter(x=x_vals, y=y_vals,name=key,mode='lines'))
    plotly.offline.plot({
        "data":scatters,
        "layout":Layout(
            title="Time Series analysis of human trafficking cases, in "+city
        )
    },auto_open=False)
    shutil.move("temp-plot.html",filename)

def newyork_totals(escalation):
    """
    Start year is assumed to be 2012
    """
    number_of_cases_per_month = 200
    escalation_rate_per_year = escalation

    yearly_total = number_of_cases_per_month * 12
    totals_year_over_year = []
    start_year = 2012
    for _ in range(10):
        totals_year_over_year.append([start_year,yearly_total])
        yearly_total *= escalation_rate_per_year
        start_year += 1

    return totals_year_over_year


# if __name__ == '__main__':
#     nyc_escalation_rates = {
#         "Post Calc % escalation":newyork_totals(0.46),
#         "5% escalation":newyork_totals(2.58),
#         "7% escalation":newyork_totals(1.07),
#         "10% escalation":newyork_totals(1.10),
#     }
    

#     timeseries_plot(nyc_escalation_rates,"nyc_humantrafficking.html","NYC")
    
class Command(BaseCommand):
    #do year over year analysis
    def handle(self, *args, **options):
        #labor_data = LaborCategory.objects.all()
        #big_picture_analysis(labor_data)
        spread_data = OverallSpread.objects.all()
        categories = list(set([elem.labor_category for elem in spread_data]))
        overall_spread = []
        data_by_year = {}
        for category in categories:
            tmp = []
            objects = OverallSpread.objects.filter(labor_category=category).order_by("year").all()
            for obj in objects:
                if not is_nan(float(obj.spread)):
                    tmp.append(round(float(obj.spread), 2))
                    if not obj.year in data_by_year.keys():
                        data_by_year[int(obj.year)] = [round(float(obj.spread), 2)]
                    else:
                        data_by_year[int(obj.year)].append(round(float(obj.spread), 2))
                    
            overall_spread.append(tmp)
        spread_change_first_to_last = []
        most_recent_change = []
        for elem in overall_spread:
            spread_change_first_to_last.append(elem[-1] - elem[0])
            if len(elem) >= 2:
                most_recent_change.append(elem[-1] - elem[-2])
        #for index,val in enumerate(data[1:]):
        #     tmp.append(data[index] - data[index-1])
        years = list(data_by_year.keys())
        years.sort()
        import code
        code.interact(local=locals())
        print("analysis of change in spread from beginning to end by labor category:")
        print("average change in spread from beginning of record to end",st.median(spread_change_first_to_last))
        print("analysis of change in spread from beginning to end by year:")
        print("average change in spread from beginning of record to end",st.median(data_by_year[years[-1]]) - st.median(data_by_year[years[0]]))
        
        print("analysis of most recent change in spread by labor category:")
        print("most recent average change in spread over average",st.median(most_recent_change))
        print("analysis of most recent change in spread by year:")
        print("most recent average change in spread over average by year",st.median(data_by_year[years[-1]]) - st.median(data_by_year[years[-2]]))
        print("analysis of change in spread year over year:")
        for index in range(len(years)):
            try:
                print(years[index],"-",years[index+1],":",st.median(data_by_year[years[index+1]]) - st.median(data_by_year[years[index]]))
            except:
                break
        import code
        code.interact(local=locals())