#%% 
# CCA: Company Classification Analysis
from trader.data_collection.dc19_CCA_tools import get_score_trend, post_process, generate_PPT
import pickle

score_trend, _ = get_score_trend()
data_dict = post_process(score_trend)

with open('CCA/temp/data.pkl', 'wb') as f:
    pickle.dump(data_dict, f)

with open('CCA/temp/data.pkl', 'rb') as f:
    data_dict = pickle.load(f)

generate_PPT(data_dict, summary_only = False)

#%% 

