#%%
from scraper.tools.models import CV_Manager, Component
from trader.analysis.sector_analysis import SectorAnalysis

cvm = CV_Manager()
component: Component = cvm.get_component('Memory')
sa = SectorAnalysis().from_component(component)
code = '251970'
code = '011200'
sb = SectorAnalysis().from_code(code)
sm = SectorAnalysis().from_index('KOSPI')

sa.print()
sb.print()

code = '009830' 
code = '020150'
code = '021240'
sc = SectorAnalysis().from_code(code)
sc.save_financials_to_json()
