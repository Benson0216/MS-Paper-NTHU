# NTHU
This is the model description of my MS research. [README.md](README.md) will only show basic description of the simulation process. All of the files are written in Python. If one wish to use the code, please be aware of the Python packages.

## Contents
- [**Data Synthesization**](#data_synthesization)
- [**Simulation Model**](#model)

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

Three of the data synthesization methods will be abbreviated as `D1`, `D2` and `D3`：

| |**Method Description**|
| --- | --- |
|`D1` |Sampling from the boundaries of the Pingtung County|
|`D2` |Sampling from the boundaries of the Pingtung County's village based on **population**|
|`D3` |Sampling from the boundaries of the Pingtung County's village based on **population density**|

Reference file plz see [here](/data_synthesis_storage.ipynb)

<h2 id="model">🖥 Simulation Model</h2>
