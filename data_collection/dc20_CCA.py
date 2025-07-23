#%% 
# CCA: Company Classification Analysis
from trader.data_collection.dc19_CCA_tools import get_score_trend, generate_PPT

score_trend, _ = get_score_trend()
# display(score_trend)
# codelist = ['082920', '259960', '408920', '067160', '000240','101160','080010','136410','226400','214180','044450','340570','236200','004590','054950','031330','052420','183300','161390']
codelist = ['082920', '259960', '408920', '067160', '000240']
generate_PPT(score_trend, codelist=codelist, topN = 50)

