#%% 
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import set_KoreanFonts
from tools.koreainvest_module import *
from analysis_tools import *
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import matplotlib.animation as animation
import pandas as pd
from broker import Broker

class Drawer:
    def __init__(
            self, 
            spine_color = 'lightgray',
            # background_color = '#001f3f',  # deep dark blue
            background_color = 'black',  # deep dark blue
            figsize = (16, 9),
            ax_size = [0.05, 0.05, 0.9, 0.9],
            text_size = 18,
            tick_text_size = 15,
            label_text_color = 'gray',
            lang = 'E',
            eng_name = None,
        ):
        self.spine_color = spine_color
        self.background_color = background_color
        self.figsize = figsize
        self.ax_size = ax_size
        self.text_size = text_size
        self.tick_text_size = tick_text_size
        self.label_text_color = label_text_color
        self.lang = lang
        self.eng_name = eng_name

        set_KoreanFonts()
        plt.rcParams.update({
            'axes.edgecolor': self.spine_color,
            'axes.labelcolor': self.spine_color,
            'xtick.color': self.spine_color,
            'ytick.color': self.spine_color,
            'xtick.labelsize': self.tick_text_size,
            'ytick.labelsize': self.tick_text_size,
            'text.color': self.spine_color,
        })
    
    def _init_fig(self):
        self.fig = plt.figure(figsize=self.figsize)
        self.ax = self.fig.add_axes(self.ax_size)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.fig.patch.set_facecolor(self.background_color)  # Figure background color
        self.ax.set_facecolor(self.background_color)
    
    def _init_twinx(self):
        self.tax = self.ax.twinx()
        self.tax.spines['top'].set_visible(False)
        self.tax.set_facecolor(self.background_color)
        
    def draw_arrow(self, sp, ep, 
                text = '', 
                line_color='yellow', 
                text_color='orange', 
                text_offset=(0, 0),  # in pt (1/72 inch)
                text_size=14, 
                line_width=2, 
                line_style = 'solid', 
                arrowstyle='->',
                vertical=True):
        arrowprops = dict(arrowstyle = arrowstyle, lw=line_width, linestyle=line_style, facecolor= line_color, edgecolor= line_color, shrinkA=1, shrinkB=0)
        mid_point = (sp[0] + (ep[0]-sp[0]) / 2, sp[1] + (ep[1]-sp[1]) / 2)  # this works even for Timestamp instances
        self.ax.annotate('', xy=ep, xytext=sp, arrowprops=arrowprops)
        if vertical:
            self.ax.annotate(text, xy=mid_point, xytext=text_offset, textcoords='offset points', ha='left', va='center', fontsize=text_size, color=text_color)
        else:
            self.ax.annotate(text, xy=mid_point, xytext=text_offset, textcoords='offset points', ha='center', va='bottom', fontsize=text_size, color=text_color)
        return None

    def draw_text(self, pt, text, **kwargs):
        self.draw_arrow(pt, pt, text=text, arrowstyle='->', **kwargs)

    def draw_line(self, sp, ep, **kwargs):
        self.draw_arrow(sp = sp, ep = ep, arrowstyle='-', **kwargs)

    def draw_dash(self, sp, ep, **kwargs):
        self.draw_arrow(sp = sp, ep = ep, arrowstyle='-', line_style='dashed', **kwargs)
    
    # si: start_index, ei: end_index (counted backward, zero based)
    def draw_increase_bar(self, si, ei, bars):
        sp = self.pt_ith_before(si, bars)
        ep = self.pt_ith_before(ei, bars)
        (spx, spy) = sp
        (epx, epy) = ep
        ext = bars[-1].get_x() - bars[-2].get_x() - bars[-2].get_width()/2
        lp = bars[-1].get_x() + bars[-1].get_width()/2
        ext = min(self.ax.get_xlim()[1]-lp, ext)
        pos = (ext - bars[-1].get_width()/2)/2 + bars[-1].get_width()/2
        x_to_pt = (self.ax.transData.transform((1, 0))[0] - self.ax.transData.transform((0, 0))[0])*72/self.fig.dpi
        text_offest = (ext - bars[-1].get_width()/2)/2*x_to_pt
        self.draw_dash(sp, (epx+ext, spy), line_color = 'gray', line_width = 1.5)
        self.draw_dash(ep, (epx+ext, epy), line_color = 'gray', line_width = 1.5)
        if spy != 0:
            increment = str(round((epy/spy-1)*100)) + '%'
        else: 
            increment = 'N/A'
        kwargs = {
            'line_color': 'orange', 
            'text': increment, 
            'line_width': 2, 
            'text_offset': (text_offest, 0), 
            'text_size': self.text_size,
        }
        self.draw_arrow((epx+pos, spy), (epx+pos, epy), **kwargs)

    # si: start_index, ei: end_index (counted from top, zero based)
    def draw_increase_barh(self, si, ei, bars):
        sp = self.pt_ith_before_hor(si, bars)
        ep = self.pt_ith_before_hor(ei, bars)
        (spx, spy) = sp
        (epx, epy) = ep
        ext = bars[-1].get_y() - bars[-2].get_y() - bars[-2].get_height()/2
        lp = bars[-1].get_y() + bars[-1].get_height()/2
        ext = min(self.ax.get_ylim()[1]-lp, ext)
        pos = (ext - bars[-1].get_height()/2)/2 + bars[-1].get_height()/2
        y_to_pt = (self.ax.transData.transform((0, 1))[1] - self.ax.transData.transform((0, 0))[1])*72/self.fig.dpi
        text_offest = (ext - bars[-1].get_height()/2)/2*y_to_pt
        self.draw_dash(sp, (spx, epy+ext), line_color = 'gray', line_width = 1.5)
        self.draw_dash(ep, (epx, epy+ext), line_color = 'gray', line_width = 1.5)
        if spy != 0:
            increment = str(round((epx/spx-1)*100)) + '%'
        else: 
            increment = 'N/A'
        kwargs = {
            'line_color': 'orange', 
            'text': increment, 
            'line_width': 2, 
            'text_offset': (0, text_offest), 
            'text_size': self.text_size,
            'vertical': False,
        }
        self.draw_arrow((spx, epy+pos), (epx, epy+pos), **kwargs)

    def pt_ith_before(self, ith, bars): # ith = 0, last bar
        idx = len(bars)-ith-1
        x_pos = bars[idx].get_x() + bars[idx].get_width()/2
        y_pos = bars[idx].get_height()
        return (x_pos, y_pos)

    def pt_ith_before_hor(self, ith, bars): # ith = 0, last bar
        idx = len(bars)-ith-1
        x_pos = bars[idx].get_width()
        y_pos = bars[idx].get_y() + bars[idx].get_height()/2
        return (x_pos, y_pos)

    def _format_quarter(x, pos=None): 
        date = mdates.num2date(x)
        year_short = date.year % 100  
        quarter = (date.month - 1) // 3 + 1
        return quarter_format(year_short, quarter)

    def _get_unit_base(self, unit_base):
        unit_dict = {1: lang_formatter('KRW', self.lang), 3: lang_formatter('K KRW', self.lang), 6: lang_formatter('M KRW', self.lang), 8: lang_formatter('100M KRW', self.lang), 9: lang_formatter('B KRW', self.lang), 12: lang_formatter('T KRW', self.lang)}
        return unit_dict.get(unit_base, 'UNIT_ERROR')
    
    def _savefig(self, output_file): 
        # output_file = output_file[:-4]+'_'+self.lang+output_file[-4:]
        self.fig.savefig(output_file, format='png', transparent=True, bbox_inches='tight', pad_inches=0.2)
    
    def free_plot(self):
        self._init_fig()
        return

    def bar_plot(self, x, y,  increment_FT = None, save=True, output_file = None, highlights = None, highlights_gray = None, highlights_red = None, scale=False, scale_factor=0.7): 
        self._init_fig()
        bars = self.ax.bar(x, y)
        
        if highlights != None: 
            for i in highlights:
                bars[-i].set_color('orange')

        if highlights_gray != None: 
            for j in highlights_gray:
                bars[-j].set_color('gray')

        if highlights_red != None: 
            for j in highlights_red:
                bars[-j].set_color('red')

        for bar in bars:
            yval = precision_adjust(bar.get_height())
            self.ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{format(yval, ",")}', ha='center', va='bottom', fontsize = self.tick_text_size)

        if increment_FT != None: 
            if increment_FT[0] != increment_FT[1]:
                self.draw_increase_bar(increment_FT[0], increment_FT[1], bars)

        if scale: 
            if all(i>0 for i in y):
                ymin = min(y)*scale_factor
                ymax = self.ax.get_ylim()[1]
                self.ax.set_ylim(ymin, ymax)  
            elif all(i<0 for i in y): 
                ymin = self.ax.get_ylim()[0]
                ymax = max(y)*scale_factor
                self.ax.set_ylim(ymin, ymax)  
            else: 
                pass

        if save:  
            if output_file != None:
                self._savefig(output_file)
            else: 
                self._savefig(gen_output_plot_path_file('bar'))

        plt.show()
        plt.close(self.fig)
    
    def barh_plot(self, items, values, increment_FT = None, save=True, output_file = None, highlights = None, highlights_gray = None, highlights_red = None, scale=False, scale_factor=0.7, display_x_axis = True): 
        self._init_fig()
        bars = self.ax.barh(items, values)
        self.ax.xaxis.set_visible(display_x_axis)
        self.ax.spines['bottom'].set_visible(display_x_axis)
        
        if highlights != None: 
            for i in highlights:
                bars[-i].set_color('orange')

        if highlights_gray != None: 
            for j in highlights_gray:
                bars[-j].set_color('gray')

        if highlights_red != None: 
            for j in highlights_red:
                bars[-j].set_color('red')

        for bar in bars:
            val = precision_adjust(bar.get_width())
            self.ax.text(bar.get_width(), bar.get_y()+bar.get_height()/2, f'{format(val, ",")}', va='center', fontsize = self.tick_text_size)

        if increment_FT != None: 
            if increment_FT[0] != increment_FT[1]:
                self.draw_increase_barh(increment_FT[0], increment_FT[1], bars)

        if scale: 
            if all(i>0 for i in values):
                val_min = min(values)*scale_factor
                val_max = self.ax.get_xlim()[1]
                self.ax.set_xlim(val_min, val_max)  
            elif all(i<0 for i in values): 
                val_min = self.ax.get_xlim()[0]
                val_max = max(values)*scale_factor
                self.ax.set_xlim(val_min, val_max)  
            else: 
                pass

        if save:  
            if output_file != None:
                self._savefig(output_file)
            else: 
                self._savefig(gen_output_plot_path_file('barh'))

        plt.show()
        plt.close(self.fig)

    def quarterly_bar_plot(self, code, target_account, num_qts, unit_base, unit=1, increment_FT=(0,0), lim_scale_factor=0.7, save=True, output_file=None, highlights = None, highlights_gray = None):
        self._init_fig()
        fh = retrieve_quarterly_data_code(code)
        x = get_quarters(get_last_quarter(fh), num_qts)
        xs = get_quarter_simpler_string(x)
        y = (fh.loc[fh['account'] == target_account, x]/((10**unit_base)*unit)).round(1).values.flatten()
        bars = self.ax.bar(xs,y)

        if highlights == None: 
            bars[-1].set_color('orange')
            for i in range(1, len(bars)+1, 4):
                bars[-i].set_color('orange')
        else: 
            for i in highlights:
                bars[-i].set_color('orange')

        if highlights_gray != None: 
            for j in highlights_gray:
                bars[-j].set_color('gray')

        for bar in bars:
            yval = bar.get_height()
            if yval < 100:
                yval = round(yval, 1)
            else:
                yval = int(yval)
            self.ax.text(bar.get_x() + bar.get_width()/2, yval, f'{format(yval, ",")}', ha='center', va='bottom', fontsize = self.tick_text_size)

        self.ax.set_xlim(-1, len(x))
        ymax = max(max(y)*1.07, max(y)*lim_scale_factor)
        ymin = min(min(y)*1.07, min(y)*lim_scale_factor)
        self.ax.set_ylim(ymin, ymax)  
        self.ax.set_title(lang_formatter(target_account.replace('_', ' '), self.lang), fontsize = self.text_size)
        # self.ax.set_xlabel(lang_formatter('quarters', self.lang), fontsize = self.tick_text_size, color= self.label_text_color)

        # self.draw_text((-0.5, ymax), f'(x {format(unit, ",")} {self._get_unit_base(unit_base)})', text_size = self.tick_text_size, text_color=self.label_text_color)
        self.ax.set_ylabel(f'(x {format(unit, ",")}{" " if unit_base == 8 else ""}{self._get_unit_base(unit_base)})', fontsize = self.tick_text_size, color=self.label_text_color) 
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(precision_formatter))

        if increment_FT != None:
            if increment_FT[0] != increment_FT[1]:
                self.draw_increase_bar(increment_FT[0], increment_FT[1], bars)

        if save:  
            if output_file != None:
                self._savefig(output_file)
            else: 
                self._savefig(gen_output_plot_path_file(code+'_'+target_account))
        plt.show()
        plt.close(self.fig)

    # just the same as plot function but with Drawer format and grid
    # multi line possible as in the original plot
    # d.line_plot(x1, y1, '-o', x2, y2, ':^')
    def line_plot(self, *args, save=True, output_file=None): 
        self._init_fig()
        self.ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
        self.ax.plot(*args)

        if save:  
            if output_file != None:
                self._savefig(output_file)
            else: 
                self._savefig(gen_output_plot_path_file('line'))

        plt.show()
        plt.close(self.fig)

    def quarterly_line_plot(self, code, qtrs_back, type, subgraph = 'average', save = True, output_file = None):  
        self._init_fig()

        # type : price, PER, PBR
        # subgraph : quarterly, average
        if type == 'price':
            unit_text = lang_formatter('KRW', self.lang)
            precision = 0
            data = get_last_N_quarter_price(code, qtrs_back)
        elif type == 'PER':
            unit_text = lang_formatter('multiple', self.lang)
            precision = 2
            fh = retrieve_quarterly_data_code(code)
            fhr = L4_addition(fh, 'net_income') # last 4 quarters data addition, i.e., quarterly rolling
            PER = get_PER_rolling(code, fhr, qtrs_back)
            # fhr = L4_addition(fh, 'operating_income') # last 4 quarters data addition, i.e., quarterly rolling
            # PER = get_PER_rolling(code, fhr, qts_back, target_account='operating_income')
            data = PER
        elif type == 'PBR': 
            unit_text = lang_formatter('multiple', self.lang)
            precision = 3
            fh = retrieve_quarterly_data_code(code)
            PBR = get_PBR(code, fh, qtrs_back)
            data = PBR
        else: 
            pass

        self.ax.text(0, 1.01, f'({unit_text})', fontsize=self.tick_text_size, color=self.label_text_color, ha='right', va='bottom', transform=self.ax.transAxes)
        self.ax.text(1, 1.01, f'({data.index[-1].date()})', fontsize=self.tick_text_size, color=self.label_text_color, ha='right', va='bottom', transform=self.ax.transAxes)
        self.ax.set_title(lang_formatter(type, self.lang), fontsize=self.text_size, weight='bold')
        # self.ax.set_xlabel(lang_formatter('quarters', self.lang), fontsize=self.tick_text_size)
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(precision_formatter))

        self.ax.plot(data)
        if subgraph == 'quarterly':
            self._quarterly_average_plot(data, precision=precision)
        elif subgraph == 'average':
            self._average_plot(data, precision=precision)
        else:
            pass
        if save: 
            if output_file != None:
                self._savefig(output_file)
            else: 
                self._savefig(gen_output_plot_path_file(code+'_'+type, subgraph))
        plt.show()
        plt.close(self.fig)

    # Check if x-tick labels are overlapping
    def _check_xtick_label_overlap(self):
        labels = self.ax.get_xticklabels()
        if not labels:
            return False

        # Get the bounding boxes of the labels
        bboxes = [label.get_window_extent(renderer=self.ax.figure.canvas.get_renderer()) for label in labels]
        # Check if any bounding boxes overlap
        for i in range(len(bboxes) - 1):
            if bboxes[i].overlaps(bboxes[i + 1]):
                return True
        return False

    def _price_xtick_formatter(self, pr):
        quarters = pd.to_datetime(pr.index).to_period('Q')
        # Generate tick positions at the center of each quarter
        tick_positions = [(pd.to_datetime(str(q.start_time)) + (pd.to_datetime(str(q.end_time)) - pd.to_datetime(str(q.start_time))) / 2) for q in quarters.unique()]

        # Set tick positions and custom tick formatter
        self.ax.set_xticks(tick_positions)
        self.ax.xaxis.set_major_formatter(plt.FuncFormatter(Drawer._format_quarter))

        if self._check_xtick_label_overlap(): 
            self.ax.xaxis.set_major_locator(mdates.YearLocator())  # Set major ticks to years
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))  # Format ticks to show only the year

            # self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # Automatically set date ticks
            # self.ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(self.ax.xaxis.get_major_locator()))  # Set date formatter

    # price to be the result from the function get_last_N_quarter_price
    def _quarterly_average_plot(self, pr, precision=0):
        fontsize = self.tick_text_size
        quarters = pd.to_datetime(pr.index).to_period('Q')
        for quarter in quarters.unique():
            start = pd.to_datetime(str(quarter.start_time))
            end = pd.to_datetime(str(quarter.end_time))
            if precision == 0:
                avg_value = int(pr.loc[quarter.start_time:quarter.end_time].mean().round())  # Get the average for the quarter
            else: 
                avg_value = pr.loc[quarter.start_time:quarter.end_time].mean().round(precision)  
            self.ax.hlines(avg_value, xmin=start, xmax=end, color='orange', linewidth=2, label='quarterly average' if quarter == quarters.unique()[0] else "")
            # Display the average value above the line
            mid_point = start + (end - start) / 2  # Midpoint of the quarter
            self.ax.text(mid_point, avg_value + (avg_value * 0.01), f'{avg_value}', color='orange', ha='center', va='bottom', fontsize=fontsize)

        last_pt_color='orangered'
        self.ax.scatter(pr.index[-1], pr.iloc[-1], color=last_pt_color, edgecolor=last_pt_color, s=30)
        self.ax.text(pr.index[-1], pr.values[-1], f' {pr.values[-1].round(precision)}', ha='left', va='center', weight='bold', fontsize = fontsize, color=last_pt_color)
        # Iterate over each quarter and highlight even-numbered quarters
        for i, quarter in enumerate(quarters.unique()):
            if quarter.quarter % 2 == 0:  # Check if it is an even-numbered quarter
                start = pd.to_datetime(str(quarter.start_time))
                end = pd.to_datetime(str(quarter.end_time))
                self.ax.axvspan(start, end, facecolor='gray', alpha=0.2)  # Fill with a white box
        self._price_xtick_formatter(pr)

    def _average_plot(self, pr, precision = 0, n_sigma=1):
        fontsize = self.tick_text_size
        if precision == 0:
            avg_value = int(pr.mean().round())  # Get the average for the quarter
            std_value = int(pr.std().round())
        else: 
            avg_value = pr.mean().round(precision)  
            std_value = pr.std().round(precision)
        start = pr.index[0]
        end = pr.index[-1]
        upper_value = round(avg_value+n_sigma*std_value, precision)
        lower_value = round(avg_value-n_sigma*std_value, precision)
        self.ax.hlines(avg_value, xmin=pr.index[0], xmax=pr.index[-1], color='orange', linewidth=4)
        self.ax.hlines(upper_value, xmin=pr.index[0], xmax=pr.index[-1], color='orange', linewidth=1)
        self.ax.hlines(lower_value, xmin=pr.index[0], xmax=pr.index[-1], color='orange', linewidth=1)
        last_pt_color='orangered'
        self.ax.scatter(pr.index[-1], pr.iloc[-1], color=last_pt_color, edgecolor=last_pt_color, s=30)
        self.ax.text(pr.index[-1], pr.values[-1], f' {pr.values[-1].round(precision)}', ha='left', va='center', weight='bold', fontsize = fontsize, color=last_pt_color)
        mid_point = start + (end - start) / 2  # Midpoint of the quarter
        self.ax.text(mid_point, avg_value + (avg_value * 0.01), f'{avg_value}', color='orange', ha='center', va='bottom', fontsize=fontsize)
        self.ax.text(mid_point, upper_value + (upper_value * 0.01), f'{upper_value}', color='orange', ha='center', va='bottom', fontsize=fontsize)
        self.ax.text(mid_point, lower_value + (lower_value * 0.01), f'{lower_value}', color='orange', ha='center', va='bottom', fontsize=fontsize)
        arrow_point = int(len(pr)*3/4)
        self.draw_arrow((pr.index[arrow_point], avg_value*(1.0)), (pr.index[arrow_point], upper_value), '+1$\sigma$', text_offset=(17, 0))
        self.draw_arrow((pr.index[arrow_point], avg_value*(1.0)), (pr.index[arrow_point], lower_value), '-1$\sigma$', text_offset=(17, 0))
        self._price_xtick_formatter(pr)

    def plot_fownership(self, fo, cr, period='D', save=True, output_file=None):
        # period = 'D', 'W', 'M'
        self._init_fig()
        self._init_twinx()

        self.ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
        x_locs = range(len(fo))
        self.ax.plot(x_locs, fo['price'], '-o', linewidth = 1, label = 'price')
        self.ax.set_xticks(x_locs)  # Set the tick locations
        self.ax.set_xticklabels(fo.index.strftime('%m-%d'), rotation=45)  # Set the tick labels with rotation
        self.tax.plot(x_locs, fo['fo'], ':o', color='r', linewidth = 2, label=lang_formatter('foreigner', self.lang))

        # self.ax.set_xlabel('Dates', fontsize = self.tick_text_size, color=self.label_text_color)
        self.ax.set_ylabel(f'Price({lang_formatter("KRW", self.lang)})', fontsize = self.tick_text_size, color=self.label_text_color)

        if self.lang == 'K':
            period_dict = {'D': '(최근 30일)', 'W': '(최근 30주)', 'M': '(최근 30개월)'}
            title = '주가, 외국인 보유율 '
            ylabel = '외국인 보유율(%)'
            corr_text = '상관계수'
        else: 
            period_dict = {'D': '(Last 30 days)', 'W': '(Last 30 weeks)', 'M': '(Last 30 months)'}
            title = 'Price and Foreign ownership'
            ylabel = 'Foreign ownership ratio(%)'
            corr_text = 'Correlation coefficient'
        
        self.ax.set_title(title+period_dict[period], fontsize = self.text_size)
        self.tax.set_ylabel(ylabel, fontsize = self.tick_text_size, color=self.label_text_color)
        self.ax.legend(framealpha=0, loc='upper left', fontsize = self.tick_text_size, bbox_to_anchor=(0,1.05))
        self.tax.legend(framealpha=0, loc='upper right', fontsize = self.tick_text_size, bbox_to_anchor=(1,1.05))
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))

        name = lookup_name_onetime(fo['code'].iloc[0], self.lang, self.eng_name)
        if name != '': name += ' '
        self.ax.text(0.5, 0.07, f'{name}{corr_text}: '+str(round(cr, 2)), ha='center', va='center', transform=self.ax.transAxes,  # Use axes coordinates
                bbox=dict(facecolor='green', edgecolor='none', boxstyle='round,pad=0.3'),
                fontsize=self.text_size, color='white', zorder=5)  # Ensure text is on top
        if save: 
            if output_file != None:
                self._savefig(output_file)
            else: 
                self._savefig(gen_output_plot_path_file(f'frn_ownership_{fo["code"].iloc[0]}_{period}'))

        plt.show()
        plt.close(self.fig)

    def corr_comparison_plot(self, broker, code, period = 'M', num_to_plot = 400, text_label = True, save=True, output_file=None, scale=True, scale_factor=0.85):
        y_tick_removal_threshold = 45
        self._init_fig()

        corr_data_file = 'data/corr_fownership.feather'
        corr = read_or_regen(corr_data_file, broker.generate_corr_data)

        if self.lang == 'K':
            title = '외국인 보유율과 주가 상관관계'
            text_01 = f'시총>{format(int(Broker.MARCAP_THRESHOLD/10**8),",")}억원, 상장>{int(Broker.IPO_YEAR_THRESHOLD)}년인 상장사 총{len(corr)}개 중 상관계수 상위{min(len(corr), num_to_plot)}개 표시'
        else: 
            title = 'Share price and Foreign ownership correlation '
            text_01 = f'total {len(corr)} public companies are Market Cap > {format(int(Broker.MARCAP_THRESHOLD/10**9),",")}B KRW, IPO > {int(Broker.IPO_YEAR_THRESHOLD)} years, and top {min(len(corr), num_to_plot)} are shown'

        sorted_corr = corr.sort_values(period, ascending=True)[-num_to_plot:].reset_index(drop=True)
        bars = self.ax.barh(sorted_corr['name'], sorted_corr[period])
        self.ax.set_ylim(-0.5, len(bars)-0.5)
        self.ax.text(1, 1.01, f'{corr.loc[0, "date"].strftime("%Y-%m-%d")}', fontsize=self.tick_text_size, color=self.label_text_color, ha='right', va='bottom', transform=self.ax.transAxes)
        self.ax.set_title(title, fontsize=self.text_size)
        if text_label: 
            self.ax.text(0.5, 0.05, text_01, ha='center', va='center', transform=self.ax.transAxes,  # Use axes coordinates
                    bbox=dict(facecolor='orange', edgecolor='none', boxstyle='round,pad=0.3'),
                    fontsize=self.tick_text_size, color='black', zorder=5)  # Ensure text is on top

        target_row = sorted_corr.loc[sorted_corr['code'] == code]
        if len(target_row)>0:
            code_loc = target_row.index[0]
            bars[code_loc].set_color('orange')

            target_name = lookup_name_onetime(code, self.lang, self.eng_name)
            if target_name != '': target_name += ': ' 
            target_ranking = len(sorted_corr) - code_loc
            if self.lang == 'K':
                text_02 = f'{target_name}{target_ranking}번째로 상관관계 높음'
            else: 
                text_02 = f'{target_name}Top {target_ranking} in terms of correlation coefficient'

            if text_label:
                self.ax.text(0.5, 0.10, text_02, ha='center', va='center', transform=self.ax.transAxes,  # Use axes coordinates
                        bbox=dict(facecolor='green', edgecolor='none', boxstyle='round,pad=0.3'),
                        fontsize=self.text_size, color='white', zorder=5)  # Ensure text is on top

        if num_to_plot > y_tick_removal_threshold: 
            self.ax.set_yticks([]) 
        else: 
            for bar in bars:
                xval = bar.get_width()
                xval_p = round(xval, 2)
                yval = bar.get_y() + bar.get_height()/2
                self.ax.text(xval*1.005, yval, f'{xval_p}', va='center', ha='left', fontsize = self.tick_text_size )

        if scale: 
            if all(i>0 for i in sorted_corr[period]):
                val_min = min(sorted_corr[period])*scale_factor
                val_max = self.ax.get_xlim()[1]
                self.ax.set_xlim(val_min, val_max)  
            elif all(i<0 for i in sorted_corr[period]): 
                val_min = self.ax.get_xlim()[0]
                val_max = max(sorted_corr[period])*scale_factor
                self.ax.set_xlim(val_min, val_max)  
            else: 
                pass

        if save: 
            if output_file != None:
                self._savefig(output_file)
            else: 
                self._savefig(gen_output_plot_path_file(f'frn_ownership_compare_{code}_{period}'))

        plt.show()
        plt.close(self.fig)
    
    def line_animate(self, x, y, speed = 1, output_file=None):
        self._init_fig()
        line, = self.ax.plot([], [], lw=3, color='yellow')
        self.ax.set_xlim(min(x), max(x))
        self.ax.set_ylim(min(y), max(y))
        def init():
            line.set_data([], [])
            return line,

        # Function to animate each frame (two points at a time)
        def animate(i):
            idx = i * speed
            # Set x-data and y-data to include more points
            line.set_data(x[:idx+1], y[:idx+1])
            return line,

        frames = len(y) // speed  # Adjust the number of frames, since we add two points per frame
        ani = animation.FuncAnimation(self.fig, animate, frames=frames, init_func=init, blit=True, interval=50)

        if output_file != None:
            ani.save(output_file, writer='ffmpeg', fps=24)

        plt.show()

    def double_line_animate(self, x1, y1, x2, y2, speed=1, output_file=None):
        self._init_fig()
    
        # Initialize two lines
        line1, = self.ax.plot([], [], lw=3, color='white', label='Line 1')
        line2, = self.ax.plot([], [], lw=3, color='orange', label='Line 2')

        # Set axis limits
        self.ax.set_xlim(min(min(x1), min(x2)), max(max(x1), max(x2)))
        self.ax.set_ylim(min(min(y1), min(y2)), max(max(y1), max(y2)))
        self.ax.margins(x=0.1, y=0.1)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

        # Initialize function for animation
        def init():
            line1.set_data([], [])
            line2.set_data([], [])
            return line1, line2

        # Function to animate each frame
        def animate(i):
            idx = i * speed
            # Set x and y data for both lines
            line1.set_data(x1[:idx+1], y1[:idx+1])
            line2.set_data(x2[:idx+1], y2[:idx+1])
            return line1, line2

        frames = min(len(y1), len(y2)) // speed  # Adjust the number of frames based on the shortest line

        ani = animation.FuncAnimation(self.fig, animate, frames=frames, init_func=init, blit=True, interval=50)

        if output_file is not None:
            ani.save(output_file, writer='ffmpeg', fps=24)

        plt.show()

    def triple_line_animate(self, x1, y1, x2, y2, x3, y3, speed=1, output_file=None):
        self._init_fig()
    
        # Initialize two lines
        line1, = self.ax.plot([], [], lw=3, color='white', label='Line 1')
        line2, = self.ax.plot([], [], lw=3, color='orange', label='Line 2')
        line3, = self.ax.plot([], [], lw=3, color='cyan', label='Line 3')

        # Set axis limits
        self.ax.set_xlim(min(min(x1), min(x2), min(x3)), max(max(x1), max(x2), max(x3)))
        self.ax.set_ylim(min(min(y1), min(y2), min(y3)), max(max(y1), max(y2), max(y3)))
        self.ax.margins(x=0.1, y=0.1)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

        # Initialize function for animation
        def init():
            line1.set_data([], [])
            line2.set_data([], [])
            line3.set_data([], [])
            return line1, line2, line3 

        # Function to animate each frame
        def animate(i):
            idx = i * speed
            # Set x and y data for both lines
            line1.set_data(x1[:idx+1], y1[:idx+1])
            line2.set_data(x2[:idx+1], y2[:idx+1])
            line3.set_data(x3[:idx+1], y3[:idx+1])
            return line1, line2, line3 

        frames = min(len(y1), len(y2), len(y3)) // speed  # Adjust the number of frames based on the shortest line

        ani = animation.FuncAnimation(self.fig, animate, frames=frames, init_func=init, blit=True, interval=50)

        if output_file is not None:
            ani.save(output_file, writer='ffmpeg', fps=24)

        plt.show()

if __name__ == '__main__': 
    x = ['11/11', '11/12', '11/13', '11/14', '11/15']
    y = [19298.76, 19281.40, 19230.72,	19107.65, 18680.12]

    d = Drawer(
        figsize = (12, 4), 
        tick_text_size = 16,
        text_size = 20,
        )

    y2 = [i*1.1 for i in y]
    pass