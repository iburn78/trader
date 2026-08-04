#%%
from scraper.tools.models import CV_Manager
from trader.analysis.sector_analysis import SectorAnalysis

cvm = CV_Manager()
component = cvm.get_component('Memory')

si = SectorAnalysis()
si.from_codelist(component.get_codelist())
si.get_stats(aggregation='d', start_date='2025-01-01')
si.plot()
print(si.ma_rates)
print(si.fr_rates)

si = SectorAnalysis()
si.from_index('KOSPI')
si.get_stats(aggregation='w', start_date='2025-01-01')
si.plot()
print(si.ma_rates)
#%% 

