#%% 
# CCA: Company Classification Analysis
from trader.data_collection.dc19_CCA_tools import get_score_trend, post_process, generate_PPT
import pickle

# score_trend, _ = get_score_trend()
# print(score_trend)
# data_dict = post_process(score_trend)

# with open('CCA/temp/data.pkl', 'wb') as f:
#     pickle.dump(data_dict, f)

with open('CCA/temp/data.pkl', 'rb') as f:
    data_dict = pickle.load(f)

# print(data_dict)
print(data_dict['select_codelist'])
generate_PPT(data_dict, summary_only = False)

###_  make it to be able to test a single company - should be an easy one