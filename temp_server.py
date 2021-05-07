import os
import io

import numpy as np
import pandas as pd

from bokeh.plotting import figure
from bokeh.models import Span
from bokeh.resources import CDN, INLINE
from bokeh.embed import file_html
from bokeh.io.export import get_screenshot_as_png

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from flask import Flask, send_file, jsonify
app = Flask(__name__)

app.config['DATA_FILE'] = os.environ.get('TEMP_SERVER_DATA_FILE', 'temp_data')

EMERGE_TEMP_F = 64

app.config['UTC_OFFSET'] =  os.environ.get('TEMP_SERVER_UTC_OFFSET', -4)

app.config['EMERGE_TEMP_F'] =  os.environ.get('TEMP_SERVER_EMERGE_TEMP_F', 64)
app.config['TREND_FPERHR'] =  os.environ.get('TEMP_SERVER_TREND_FPERHR', .1)

def f_to_c(degf):
    return (degf - 32)*5/9
def c_to_f(degc):
    return degc*9/5 + 32

@app.route('/')
def index():
    with open(app.config['DATA_FILE']) as f:
        header = next(iter(f))
        header_names = header.split()
        if 'timestamp' in header_names:
            header_names.remove('timestamp')
    return 'try /latest/<colname>, /latestjson/<colname>, /plot/<colname>, /png/<colname>.  <colname> can be: ' + str(header_names)

@app.route('/latestjson/<colname>')
def latest_json(colname):
    x, y = get_data(colname)[:2]

    latest_time_idx = np.argmax(x)
    latest_val = y[latest_time_idx]

    dt = np.datetime64('now') - x.to_numpy()
    hr_since = dt.astype(float)/3.6e12 + app.config['UTC_OFFSET']

    dct = dict(column_name=colname, latest_val=latest_val,
                sec_since=int(hr_since[latest_time_idx]*3600))

    msk24hr = hr_since < 24
    y24 = y[msk24hr]
    dct['min_24hr'] = y24.min()
    dct['max_24hr'] = y24.max()

    if colname.startswith('temp'):
        if colname == 'temp_c':
            emergence_temp = f_to_c(app.config['EMERGE_TEMP_F'])
            slope_threshold = f_to_c(app.config['TREND_FPERHR'])
        elif colname == 'temp_f':
            emergence_temp = app.config['EMERGE_TEMP_F']
            slope_threshold = app.config['TREND_FPERHR']
        else:
            return f"Invalid temp! {colname}"
        dct['temp_diff'] = emergence_temp - latest_val
        dct['emergence_imminent'] = int(dct['temp_diff'] < 0)

        msk2hr = hr_since < 2
        slope, intercept = np.polyfit(-hr_since[msk2hr], y[msk2hr], 1)
        dct['slope_2hr'] = slope
        dct['trend_2hr'] = 0
        if slope > slope_threshold:
            dct['trend_2hr'] = 1
        elif slope < -slope_threshold:
            dct['trend_2hr'] = -1


    return jsonify(dct)

@app.route('/latest/<colname>')
def latest(colname):
    j = latest_json(colname).json
    extra = ' which is {temp_diff:.3} deg below the emergence temperature.'.format(**j)
    if j['emergence_imminent']:
        extra  = extra + ' EMERGENCE IMMINENT!'

    return ('Latest value for column "{column_name}" was {latest_val:.4}, '
            '{sec_since} seconds ago. '.format(**j) + extra)

@app.route('/plot/<colname>')
def plot_column(colname):
    x, y = get_data(colname)[:2]

    p = figure(plot_width=1000, plot_height=600,
            x_axis_type="datetime", tools="pan,wheel_zoom,box_zoom,reset")

    p.line(x, y)

    span_temp = None
    if colname == 'temp_c':
        span_temp = f_to_c(app.config['EMERGE_TEMP_F'])
    elif colname == 'temp_f':
        span_temp = app.config['EMERGE_TEMP_F']

    if span_temp is not None:
        p.add_layout(Span(location=span_temp,
                          dimension='width', line_color='red',
                          line_dash='dotted', line_width=1))

    return file_html(p, CDN, "temp_server: " + colname)


PRETTY_COLNAMES = {'temp_f': 'Temp (F)', 'temp_c':'Temp (C)'}

@app.route('/png/<colname>')
def png_column(colname):
    x, y = get_data(colname)[:2]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, y, c='C0')

    if colname == 'temp_c':
        ax.axhline(f_to_c(app.config['EMERGE_TEMP_F']), c='C1', ls='-', lw=2, alpha=.8)
    elif colname == 'temp_f':
        ax.axhline(app.config['EMERGE_TEMP_F'], c='C1', ls='-', lw=2, alpha=.8)

    ax.set_ylabel(PRETTY_COLNAMES.get(colname, colname), fontsize=24)
    ax.yaxis.set_tick_params(rotation=0, labelsize=16)

    ax.set_xlabel('Date & Time', fontsize=24)
    locator = mdates.AutoDateLocator(minticks=4, maxticks=7)
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_tick_params(labelsize=16)
    ax.xaxis.get_offset_text().set_size(16)

    fig.tight_layout()

    bio = io.BytesIO()
    plt.savefig(bio, format='png')

    bio.seek(0)
    return send_file(bio, mimetype='image/png')


def get_data(column_name):
    df = pd.read_table(app.config['DATA_FILE'], ' ', parse_dates=['timestamp'])

    x = df['timestamp']
    if column_name == 'temp_f' and 'temp_f' not in df:
        y = c_to_f(df['temp_c'])
    else:
        y = df[column_name]

    return x, y, df
