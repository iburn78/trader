#%%
from trader.tools.analysis_tools import dict_to_html, sa_list_to_html
from trader.analysis.sector_analysis import SectorAnalysis

code = '005930'
sa = SectorAnalysis()
sa.process_code(code)
sa.plot()
sa.print()
sa.display_in_html()

code = '000660'
sb = SectorAnalysis()
sb.process_code(code)
sb.plot()
sb.print()
sb.display_in_html()

sa_list_to_html('memory', [sa, sb])