#%%
from scraper.tools.models import CV_Manager
from trader.analysis.sector_analysis import SectorAnalysis, CodeData

cvm = CV_Manager()
component = cvm.get_component('Memory')

si = SectorAnalysis(component.get_codelist())
si.get_stats(aggregation='d', start_date='2025-01-01')
si.plot()

print(si.ma_rates)
print(si.fr_rates)
#%% 
from trader.analysis.sector_analysis import SectorAnalysis, CodeData
a = CodeData('005930')
print(a.ma_data)
#%% 

import FinanceDataReader as fdr

fdr.DataReader('KS11')
