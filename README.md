# Prehospital Selection with Simulation
This is the model description of my MS research. [README.md](README.md) will only show the description of the base simulation model. All of the files are written in Python (version 3.11.2). If one wish to use the code, please be aware of the Python packages and liba.

## Contents
- [**Data Synthesization**](#data_synthesization)
	- [**D1**](#D1)
	- [**D2**](#D2)
	- [**D3**](#D3)
- [**Simulation Model**](#model)
	- [**Settingd**](#settings)
	- [**Transfer of the patients**](#trans_pat)
	- [**Simulation**](#sim)

<h2 id="data_synthesization">💾 Data Synthesization</h2>

Main body of the synthesization is function `pat_data_generator()`：

```python
def pat_data_generator(number_of_data, data_type, iter_no):
    ...
```
Input parameters：
- `number_of_data`：the number of data you wish to generate.
- `data_type`：the type of data synthesization methods you wish to use.
- `iter_no`：random seed input for producibility.

Three of the data synthesization methods (`data_type`) will be abbreviated as `D1`, `D2` and `D3`：

| |**Method Description**|
| --- | --- |
|`D1` |Sampling from the boundaries of the Pingtung County|
|`D2` |Sampling from the boundaries of the Pingtung County's village based on **population**|
|`D3` |Sampling from the boundaries of the Pingtung County's village based on **population density**|

<h3 id="D1">D1</h3>

```python
if(data_type == 1):
    x_min, y_min, x_max, y_max = ping.total_bounds
    x_min=120.42
    while(len(pat_data) < number_of_data):
        re_pat_no = number_of_data - len(pat_data)
        for i in range(re_pat_no):
            x = np.random.uniform(x_min, x_max)
            y = np.random.uniform(y_min, y_max)
            pat_data=pat_data.append(gpd.GeoSeries(Point(x, y)))
        pat_data = pat_data[pat_data.within(ping.at[21,'geometry'])]
```
> `x_min, y_min, x_max, y_max` roughly extract the boundaries of the region. The while-loop will keep generate the data points until the number matched `number_of_data`. At the end of the loop, the loop will check if the data point is really within the region based on the boundary data.

<h3 id="D2">D2</h3>

```python
elif(data_type == 2):
	while(len(pat_data) < number_of_data):
		sam_vill_ind = np.random.choice([i for i in gdf_vill_ping.index], p = vill_sampling_1)
		x_min, y_min, x_max, y_max = gdf_vill_ping['geometry'][sam_vill_ind].bounds
		x = np.random.uniform(x_min, x_max)
		y = np.random.uniform(y_min, y_max)
		pat_data = pat_data.append(gpd.GeoSeries(Point(x, y)))
		pat_data = pat_data[pat_data.within(ping.at[21,'geometry'])]
```

> Same as D1, but will first choose the village first based on the number of the villages' population, the restr is the same.

<h3 id="D3">D3</h3>

```python
elif(data_type == 3):
        while(len(pat_data) < number_of_data):
            sam_vill_ind = np.random.choice([i for i in gdf_vill_ping.index], p = vill_sampling_2)
            x_min, y_min, x_max, y_max = gdf_vill_ping['geometry'][sam_vill_ind].bounds
            x = np.random.uniform(x_min, x_max)
            y = np.random.uniform(y_min, y_max)
            pat_data = pat_data.append(gpd.GeoSeries(Point(x, y)))
            pat_data = pat_data[pat_data.within(ping.at[21,'geometry'])]
```
> Same as [D2](#D2), but the sampling of the villages will based on each villages' population density.

Reference file plz see [here](/data_synthesis_storage.ipynb)

<h2 id="model">🖥 Simulation Model</h2>

Simuation model will be consisted of 2 parts. One is [actions of the simulation](/main.py), the other is the [simulation](/sim_scenario_0.ipynb) itself.

<h3 id="settings">Setings</h3>

Before building the functions, I will first extract the geographic coordinates of the hopitals using the tools of GeoPandas (GPD) and OpenStreetMap (OSM) database. Also build some functions for convenience.

For further calculations, I already output few files of data, such as：
- `dis_mat`：Using GPD and OSM to output the distance matrix of the hositals.
- `time_of_react`：Smapling the time of reaction from historical data.

```python
hosp = pd.read_excel(r'高屏_醫院地址_1.xlsx', header = None)
hosp = hosp.rename(columns = {0: 'HOS_NAME'})
home = gpd.tools.geocode(hosp['HOS_NAME'], Nominatim, user_agent = 'Isochrone calculator')
```
Variables explainations：
- `hosp`：the names of the hospitals for searching in the database of OSM.
- `home`：return the geographic informations of the hospitals and put all of them into a GeoDataFrame.

```python
def read_data_by_sheet(data_type: int, s_name: int):
    data = pd.read_excel(r'data_%s.xlsx'%data_type, sheet_name = 'Sheet%s'%s_name)
    for i in range(len(data)):
        x = float(data['loc'][i][7:-1].split()[0])
        y = float(data['loc'][i][7:-1].split()[1])
        data['loc'][i] = Point(x,y)
    data['time_of_react'] = time_of_react[f'Data{data_type}_{s_name}']
    return data
```
> Read and transform the data based on the requirement, also add another column `time_of_react` from the file.

```python
def find_hosp_index(hosp_index, arr: list):
    for row in range(len(arr)):
        for col in range(len(arr[row])):
            if(arr[row][col] == hosp_index):
                return row,col
```
> Because I will store the results into a nested list, so `find_hosp_index()` will help me keep track of the location of some specific index of the hospital.

<h3 id="trans_pat">Transfer of the paitents</h3>
To this end, the basic seetings are completed. From now on, I will build the actions of the simulation, which includes `first transfer`, `inner tramnsfer` and `intra transfer`.

So, for `first transfer`, we shall decide where the patients be sent to based on the time consumption and travel distance.
```python
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
```
> `inner_cluster_1st()` help me decide the first stop of the patients based the total time duration, which including the time duration of each patients' location to each hospital, time of reaction (and also some fixed parameters which we will not explain here).

After being sent to the first hospital, based on certain crterion, there might be a second transfer. I will talk about the `inner transfer` first. So, after first transfer, the patient is in a network which the transfer within the network will be referred as `inner transfer`. According to the condition of the patients and the level of the hospital, patients will be sent within the network or outside the network which be referred to `intra transfer`. 
```python
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
```
> `inner_cluster_2nd()`：For inner transfer, the logic is alsmost same as `inner_cluster_1st()`, but it will return the location (which hospital) the patients will be sent to and the value of distane (will be later transformed to time duration). If `inner_cluster_2nd` cannot find the eligible hospital for the patients, it will return -1 and -1 for further action (`intra transfer`).

```python
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
```
> `intra_transfer()`：For intra transfer, logic the same as well. The function itself wil return which network the patients were be sent to, which hospital and the value of the distance.

Reference file plz see [here](/main.py)
<h3 id="sim">Simulation</h3>
Based on different scenarios, I will overwrite the function to meet the requirements. The results will be stored at a nested dictionary. I will not explain the simulation itselt too detail because it is too long :laughing:, but the idea is to use for-loop and run the actions based on certain contraints. 

```python
cluster_number = 1
home['cluster'] = cluster_number
KM = KMedoids(n_clusters = cluster_number, init = 'k-medoids++', random_state = 5)
home.iloc[:14]['cluster'] = KM.fit_predict(home.iloc[:14][['lat','long']])
hosp_clus = home.groupby('cluster')
```
> Using `KMedoids` to construct the network, the clustering results will be stored in the dataframe itself for easy snatch. `hosp_clus` will be the results of **groupby("cluster")**.

```python
cluster_hosp_index = [[] for i in range(len(hosp_clus_list))]
for i in range(len(hosp_clus_list)):
    cluster_hosp_index[i] = [h for h in hosp_clus.get_group(i).index]

hosp_loc = [[] for i in range(len(hosp_clus_list))]
for i in hosp_clus_list:
    hosp_loc[i] = [[] for h in range(len(hosp_clus.get_group(i)))]
```
> Because I want to seperate different networks, so I use nested list to not only stored the hopsitals' location in the network and also stored where the paitents be sent to. `cluster_hosp_index` for the reference of hospitals' location, `hosp_loc` for storing the patient (as in the value of the time duration).

Reference file plz see [here](/sim_scenario_0.ipynb)
