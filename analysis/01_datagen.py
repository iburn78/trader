#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
import FinanceDataReader as fdr
from data_collection.dc05_CompanyHealth import single_company_data_collect
from analysis_tools import *
import importlib

code = '005930'
START_DATE = '2014-01-01'

pr = fdr.DataReader(code, START_DATE)['Close']
fh = single_company_data_collect(code)
fh = fh.loc[(fh['fs_div']=='CFS')]

#%%
import matplotlib.pyplot as plt
import analysis_tools
importlib.reload(analysis_tools)
from analysis_tools import *

spine_color = 'lightgray'
background_color = '#001f3f' # deep dark blue
plt.rcParams.update({
    'axes.edgecolor':spine_color,
    'axes.labelcolor':spine_color,
    'xtick.color':spine_color,
    'ytick.color':spine_color,
    'text.color':spine_color,
})
figsize = (12,6)
fig = plt.figure(figsize=figsize)
ax_size = [0.05, 0.05, 0.9, 0.9]
ax = fig.add_axes(ax_size)
ax_size_px_max = (int(72*figsize[0]*ax_size[2]), int(72*figsize[1]*ax_size[3]))

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.patch.set_facecolor(background_color)  # Figure background color
ax.set_facecolor(background_color)     

this_quarter = '2024_2Q'
num = 15
target_account = 'revenue'
unit = 1000 # in 억원
unit_text = format(unit, ',')
unit_div = (10**8)*int(unit_text.replace(',',''))

x = get_quarters(this_quarter, num)
xs = get_quarter_simpler_string(x)
bar_distance_px = int(ax_size_px_max[0]/(2+len(x)))
y = (fh.loc[fh['account'] == target_account, x]/unit_div).round(1).values.flatten()
bars = ax.bar(xs,y)

for i in range(1, len(bars)-1, 4):
    bars[-i].set_color('orange')

ax.set_xlim(-1, len(x)+0.5)  # Increase the x-axis limit
ylim = int(max(y)*1.1)
ax.set_ylim(0, ylim)  # Increase the y-axis limit

text_color = 'white'
unit_pt = (-0.2, ylim*0.97)
draw_text(ax, unit_pt, f'(x {unit_text} 억원)', text_size = 10, text_color=text_color)

sp = pt_iqbefore(8, x, y)
ep = pt_iqbefore(4, x, y)
draw_increase(ax, sp, ep, ext = 1, text_offset = (int(bar_distance_px/2), 0))

output_file = 'plots/my_plot.png'
fig.savefig(output_file, format='png', transparent=True)
plt.show()


