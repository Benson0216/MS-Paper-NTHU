from sklearn_extra.cluster import KMedoids
import alphashape
from descartes import PolygonPatch
import folium
import geopandas as gpd
from geopy.geocoders import Nominatim
from ipywidgets import interact, fixed, widgets
import matplotlib.pyplot as plt
import seaborn as sns
import igraph as ig
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
from shapely import geometry
from pyproj import CRS
import shapely
from shapely.ops import unary_union
from shapely.geometry import Point, Polygon

import warnings
warnings.filterwarnings("ignore")

# read distance matrix
dis_mat = pd.read_excel('distance_matrix.xlsx', index_col = 0)

# read hospital data and pin point geographic location
hosp = pd.read_excel(r'高屏_醫院地址_1.xlsx', header = None)
hosp = hosp.rename(columns = {0: 'HOS_NAME'})
home = gpd.tools.geocode(hosp['HOS_NAME'], Nominatim, user_agent = 'Isochrone calculator')

# extract latitude and longitude
for i in range(len(home)):
    home.at[i,'lat']=home.loc[i, 'geometry'].y
    home.at[i,'long']=home.loc[i, 'geometry'].x

# set level of hospital
home['level'] = 0
rtpa_hosp_list = [0, 1, 3, 4, 9, 19, 20, 21, 22, 23, 24, 25]
evt_hosp_list = [14, 15, 16, 17, 18]

# set hospital level
for i in [rtpa_hosp_list, evt_hosp_list]:
    if(i[0] == 0):
        for j in i:
            home.at[j,'level'] = 1
    else:
        for j in i:
            home.at[j,'level'] = 2

# set admistration time
home['admin_time'] = 5*60
# set test time
home['test_time'] = 45*60
# set treat time
home['treat_time'] = 15*60

# read time_of_react_file
time_of_react = pd.read_excel("time_of_react_file.xlsx", index_col=0)

## loads of functions
# read data from excel and transform string to Point
def read_data_by_sheet(data_type: int, s_name: int):
    data = pd.read_excel(r'data_%s.xlsx'%data_type, sheet_name = 'Sheet%s'%s_name)
    for i in range(len(data)):
        x = float(data['loc'][i][7:-1].split()[0])
        y = float(data['loc'][i][7:-1].split()[1])
        data['loc'][i] = Point(x,y)
    data['time_of_react'] = time_of_react[f'Data{data_type}_{s_name}']
    return data

# find index of the hospital within the network
def find_hosp_index(hosp_index, arr: list):
    for row in range(len(arr)):
        for col in range(len(arr[row])):
            if(arr[row][col] == hosp_index):
                return row,col

# set patient symptom and severity
def patient_trans(pat_no, hosp_no, pat_pd: pd.DataFrame):
    hosp_level = home.at[hosp_no, 'level']
    pat_sym = pat_pd.at[pat_no, 'sym']
    if(pat_sym == 'm'):
        if(hosp_level == 0):
            return 0
        elif(hosp_level == 1):
            return 1
        elif(hosp_level == 2):
            return 2
    elif(pat_sym == 's'):
        if(hosp_level == 0):
            return 3
        elif(hosp_level == 1):
            return 4
        elif(hosp_level == 2):
            return 5
    elif(pat_sym == 'c'):
        if(hosp_level == 0):
            return 6
        elif(hosp_level == 1):
            return 7
        elif(hosp_level == 2):
            return 8

# for 1st transfer - send to the nearest hospital
def inner_cluster_1st(pat_no, pat_pd: pd.DataFrame):
    M = 10**10
    ind = 10**10
    react_time_value = pat_pd.at[pat_no, 'time_of_react']

    for i in range(len(home)):
        cal_dis = pat_pd.at[pat_no, 'hosp%s'%i]
        cal_time = react_time_value + (cal_dis / 13.8) + home.at[i,'admin_time'] + home.at[i,'test_time'] + home.at[i,'treat_time']
        if(cal_time < M):
            M = cal_time
            ind = i
    return ind, M

# for 2nd tranfer - inner cluster
def inner_cluster_2nd(cluster_no, hosp_ind, pat_type, df_group: pd.DataFrame):
    M = 10**10
    ind = 10**10
    tmp_cluster = df_group.get_group(cluster_no)
    
    if (pat_type == 3):
        hosp_list = [i for i in tmp_cluster[tmp_cluster['level'] > 0].index]
    elif any([pat_type == 6, pat_type == 7]):
        hosp_list = [i for i in tmp_cluster[tmp_cluster['level'] == 2].index]
    # print(hosp_list)
    
    if (len(hosp_list) == 0):
        return -1, -1
    else:
        for i in range(len(hosp_list)):
            cal_time_ = dis_mat.at[hosp_ind, hosp_list[i]]
            cal_time = cal_time_ + home.at[hosp_list[i], 'treat_time']
            if(cal_time < M):
                M = cal_time
                ind = hosp_list[i]
        return ind, M

# for 2nd tranfer - intra cluster
def intra_transfer(hosp_ind, pat_type, arr):
    M = 10**10
    ind = 10**10

    if (pat_type == 3):
        hosp_list = [i for i in home[home['level'] > 0].index]
    elif any([pat_type == 6, pat_type == 7]):
        hosp_list = [i for i in home[home['level'] == 2].index]
    
    for i in range(len(hosp_list)):
        cal_time_ = dis_mat.at[hosp_ind, hosp_list[i]]
        cal_time = cal_time_ + home.at[hosp_list[i],'admin_time'] + home.at[hosp_list[i], 'test_time'] + home.at[hosp_list[i], 'treat_time']
        if(cal_time < M):
            M = cal_time
            ind = hosp_list[i]
    cluster_no, hosp_index = find_hosp_index(ind, arr)
    return cluster_no, hosp_index, M

# set hosptial level
def set_hosp_level(r_list, e_list):
    for i in r_list:
        home.at[i, 'level'] = 1
    for j in e_list:
        home.at[j, 'level'] = 2