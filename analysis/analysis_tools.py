#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import *

def get_quarters(this_quarter, num = 5 ):
    year, quarter = this_quarter.split('_')
    year = int(year)
    quarter = int(quarter[0])  # Convert quarter from '2Q' to 2

    # Determine the last quarter
    if quarter == 1:
        last_quarter = f"{year - 1}_4Q"
    else:
        last_quarter = f"{year}_{quarter - 1}Q"

    # Determine the last number of quarters
    quarters = []
    current_year, current_quarter = year, quarter

    for _ in range(num):
        quarters.append(f"{current_year}_{current_quarter}Q")
        if current_quarter == 1:
            current_quarter = 4
            current_year -= 1
        else:
            current_quarter -= 1

    return quarters[::-1]

# Example usage
# this_quarter = '2024_2Q'
# quarters = get_quarters(this_quarter)

def get_quarter_simpler_string(quarters):
    res = []
    for q in quarters: 
        res.append(q[2:4]+'.'+q[5:6])
    return res
        
def draw_arrow(ax, sp, ep, 
            text = '', 
            line_color='white', 
            text_color='white', 
            text_offset=(0, 0),  # in pt (1/72 inch)
            text_size=14, 
            line_width=2, 
            arrowstyle='->'):
    set_KoreaFonts()
    arrowprops = dict(arrowstyle = arrowstyle, lw=line_width, facecolor= line_color, edgecolor= line_color, shrinkA=1, shrinkB=0)
    mid_point = ((sp[0] + ep[0]) / 2, (sp[1] + ep[1]) / 2)
    ax.annotate('', xy=ep, xytext=sp, arrowprops=arrowprops)
    ax.annotate(text, xy=mid_point, xytext=text_offset, textcoords='offset points', ha='center', va='bottom', fontsize=text_size, color=text_color)
    # ax.annotate(text, xy=mid_point, xytext=text_offset, textcoords='offset points', ha='center', va='bottom', fontproperties= font_prop, fontsize=text_size, color=text_color)
    return None

def draw_text(ax, pt, text, **kwargs):
    draw_arrow(ax, pt, pt, text=text, arrowstyle='->', **kwargs)

def draw_line(ax, sp, ep, **kwargs):
    draw_arrow(ax, sp = sp, ep = ep, arrowstyle='-', **kwargs)

def draw_increase(ax, sp, ep, ext = 1, pos = 0.85, **kwargs):
    (spx, spy) = sp
    (epx, epy) = ep
    draw_line(ax, sp, (epx+ext, spy), line_color='whitesmoke', line_width = 1, **kwargs)
    draw_line(ax, ep, (epx+ext, epy), line_color='whitesmoke', line_width = 1, **kwargs)
    if spy*epy > 0:
        increment = str(round((epy/spy-1)*100)) + '%'
    draw_arrow(ax, (epx+ext*pos, spy), (epx+ext*pos, epy), text=increment, line_width=2, **kwargs )
    
def pt_iqbefore(ith, quarters_list, y_values): # ith = 0, this quarter (last bar)
                                                            # quarters_list: return value of get_quarters()
    x_idx = len(quarters_list)-ith-1
    return (x_idx, y_values[x_idx])