# NTHU
This is the model description of my MS research. [README.md](README.md) will only show the description of the base simulation model. All of the files are written in Python. If one wish to use the code, please be aware of the Python packages.

## Contents
- [**Data Synthesization**](#data_synthesization)
	- [**D1**](#D1)
	- [**D2**](#D2)
	- [**D3**](#D3)
- [**Simulation Model**](#model)
	- [**Simulation functions**](#sim_func)

<h2 id="data_synthesization">💾 Data Synthesization</h2>

Main body of the synthesization is function `pat_data_generator()`：

```python
def pat_data_generator(number_of_data, data_type, iter_no):
    ...
```
Input parameters：
- `number_of_data`：the number of data we wish to generate
- `data_type`：the type of data synthesization methods we wish to use
- `iter_no`：random seed input for producibility

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
> `x_min, y_min, x_max, y_max` roughly extract the boundaries of the region. The while-loop will keep generate the data points until the number matched `number_of_data`. At the end of the loop, we will check if the data point is really within the region based on the boundary data.

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

> Same as D1, but we will first choose the village first based on the number of the villages' population, the restr is the same.

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
Our simuation model will be consisted of 2 parts. One is the [main.py](#main.py), which is the actions of the simulation. The other is the simulation process

<h3 id="sim_func">Simulation Functions</h3>
