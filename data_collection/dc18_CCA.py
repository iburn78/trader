#%% 
# CCA: Company Classification Analysis
import pandas as pd
from trader.data_collection.dc18_CCA_tools import get_score_trend, generate_PPT, get_latest_close_PER, get_current_price_marcap

score_trend, _ = get_score_trend()
# generate_PPT(score_trend, topN = 50)
display(score_trend)

codelist = ['082920', '259960', '408920', '067160', '000240','101160','080010','136410','226400','214180','044450','340570','236200','004590','054950','031330','052420','183300','161390']

# took some time: may optimize
for code in codelist:
    print(code)
    PER = get_latest_close_PER(code)
    print(PER)
    pr, mc = get_current_price_marcap(code)
    print(pr, mc)
