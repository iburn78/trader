#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from data_collection.dc05_CompanyHealth import single_company_data_collect
from analysis_tools import *
import matplotlib.pyplot as plt

code = '005930'
fh = single_company_data_collect(code, 'CFS')

#%%
target_account = 'revenue'
num_qts = 6
output_file = f'plots/plot_{target_account[:4]}.png'

# for increment arrow
increment_show = True
increment_start_qts_back = 4 
increment_end_qts_back = 0

unit = 1000 # in 억원
unit_base = 8 # 8 is 억원
unit_in_Korean = '억원'

spine_color = 'lightgray'
background_color = '#001f3f' # deep dark blue
figsize = (16, 9)
ax_size = [0.05, 0.05, 0.9, 0.9]
tick_text_size = 20
text_size = 20
lim_scale_factor = 0.7  # determine axis starting point

plt.rcParams.update({
    'axes.edgecolor':spine_color,
    'axes.labelcolor':spine_color,
    'xtick.color':spine_color,
    'ytick.color':spine_color,
    'xtick.labelsize':tick_text_size,
    'ytick.labelsize':tick_text_size,
    'text.color':spine_color,
})
fig = plt.figure(figsize=figsize)
ax = fig.add_axes(ax_size)
ax_size_in_px = (int(72*figsize[0]*ax_size[2]), int(72*figsize[1]*ax_size[3]))
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.patch.set_facecolor(background_color)  # Figure background color
ax.set_facecolor(background_color)     

unit_text = format(unit, ',')
unit_div = (10**unit_base)*int(unit_text.replace(',',''))
last_quarter = get_last_quarter(fh)
x = get_quarters(last_quarter, num_qts)
xs = get_quarter_simpler_string(x)
bar_distance_px = int(ax_size_in_px[0]/(2+len(x)))
y = (fh.loc[fh['account'] == target_account, x]/unit_div).round(1).values.flatten()
bars = ax.bar(xs,y)

bars[-1].set_color('orange')
for i in range(1, len(bars)+1, 4):
    bars[-i].set_color('orange')

for bar in bars:
    yval = int(bar.get_height())
    ax.text(bar.get_x() + bar.get_width()/2, yval, f'{yval}', ha='center', va='bottom', fontsize = tick_text_size )

ax.set_xlim(-1, len(x))
ymax = max(int(max(y)*1.1), int(max(y)*lim_scale_factor))
ymin = min(int(min(y)*1.1), int(min(y)*lim_scale_factor))
ax.set_ylim(ymin, ymax)  
ax.set_title(target_account.replace('_', ' '), fontsize = text_size)
ax.set_xlabel('quarters', fontsize = tick_text_size)

unit_pt = (-0.5, ymax)
draw_text(ax, unit_pt, f'(x {unit_text} {unit_in_Korean})', text_size = tick_text_size, text_color=spine_color)

if increment_show:
    sp = pt_iqbefore(increment_start_qts_back , x, y)
    ep = pt_iqbefore(increment_end_qts_back, x, y)
    draw_increase(ax, sp, ep, text_offset = (int(bar_distance_px/2)+2, -text_size/2), text_size = text_size)

fig.savefig(output_file, format='png', transparent=True, bbox_inches='tight', pad_inches=0.2)
plt.show()

