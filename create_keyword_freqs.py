
# coding: utf-8

# In[1]:

import os
import pandas as pd
from collections import Counter


# In[2]:

metadata = pd.read_excel("./data/COH DechArch Metadata.xlsx", sheetname="Italian",skiprows=[1])


# In[3]:

metadata.columns


# In[4]:

metadata.head(5)


# In[5]:

for v in metadata.Luogo.tolist():
    print(v)


# # Luogo keywords

# In[6]:

cnt = Counter(metadata.Luogo.tolist())
cnt.most_common(30)


# In[81]:

header = "== '''Luogo''' (place) ==\n"
header_row = """{| class="wikitable sortable" style="width: 60%; height: 200px;"
! Luogo
! frequency
! category
! wikidata
|-\n"""

data_rows = []
for l, count in cnt.most_common(1000):
    luogo = "| " + l + "\n"
    
    freq = "| " + str(count) + "\n"
    the_rest = "| \n| \n|-"
        
    row = luogo + freq + the_rest
    
    data_rows.append(row)
        
table_ending = "\n|}"
#print(data_rows)
luogo_wikitable = header + header_row + "\n".join(data_rows) + table_ending
print(luogo_wikitable)


# # Special place (Nome monumento + Luogo)

# In[31]:

all_comb = zip(list(metadata["Nome monumento"]), list(metadata["Luogo"]))
all_comb = list(all_comb)
all_comb[5:10]


# In[34]:

special = Counter(all_comb)
special.most_common(5)


# In[67]:

header = "== Specific places (combination of '''Nome Monumento''' and '''Luogo''') ==\n"
header_row = """{| class="wikitable sortable" style="width: 60%; height: 200px;"
! Nome_monumento
! Luogo
! frequency
! category
! wikidata
|-\n"""


# make sure the values are sorted when printed, since wikitable syntax doesn't allow pre-sorted field
# http://stackoverflow.com/questions/16140758/default-sort-column-in-wikipedia-table
df = pd.DataFrame()
for *tup, cnt in special.items():
    for n, l in tup:
        row_data = pd.DataFrame([{"nome":n, "luogo":l, "freq":cnt}])
    df = df.append(row_data,ignore_index=True)

df.sort_values(by="freq", ascending=False, inplace=True)  
#print(df.head())

# Now create strings to form wikitable rows in sorted order
data_rows = []
for index, row in df.iterrows():
    nome = "| " + str(row["nome"]) + "\n"
    luogo = "| " + str(row["luogo"]) + "\n"
    freq = "| " + str(row["freq"]) + "\n"
    the_rest = "| \n| \n|-"
        
    new_row = nome + luogo + freq + the_rest
    
    if pd.notnull(row["nome"]) and pd.notnull(row["luogo"]) and row["nome"] != row["luogo"]:
        data_rows.append(new_row)
    else:
        continue
        
table_ending = "\n|}"
#print(data_rows)
special_wikitable = header + header_row + "\n".join(data_rows) + table_ending
print(special_wikitable)


# In[ ]:



