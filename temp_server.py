import os
import io

import numpy as np
import pandas as pd

from bokeh.plotting import figure
from bokeh.models import Span
from bokeh.resources import CDN, INLINE
from bokeh.embed import file_html
from bokeh.io.export import get_screenshot_as_png

from matplotlib import pyplot as plt

from flask import Flask, send_file
app = Flask(__name__)

app.config['DATA_FILE'] = os.environ.get('TEMP_SERVER_DATA_FILE', 'temp_data')

EMERGE_TEMP_F = 64
EMERGE_TEMP_C = (EMERGE_TEMP_F - 32)*5/9

app.config['UTC_OFFSET'] =  os.environ.get('TEMP_SERVER_UTC_OFFSET', -4)


@app.route('/')
def index():
    with open(app.config['DATA_FILE']) as f:
        header = next(iter(f))
        header_names = header.split()
        if 'timestamp' in header_names:
            header_names.remove('timestamp')
    return 'try /latest/<colname>, /plot/<colname>, /png/<colname>.  <colname> can be: ' + str(header_names)

@app.route('/latest/<colname>')
def latest(colname):
    x, y = get_data(colname)[:2]

    latest_time_idx = np.argmax(x)
    latest_val = y[latest_time_idx]

    dt = np.datetime64('now') - x[latest_time_idx].to_numpy()
    sec_since = dt.astype('timedelta64[s]') + 3600*app.config['UTC_OFFSET']

    extra = ''
    if colname.startswith('temp'):
        if colname == 'temp_c':
            emergence_temp = EMERGE_TEMP_C
        elif colname == 'temp_f':
            emergence_temp = EMERGE_TEMP_F
        else:
            return f"Invalid temp! {colname}"
        diff = emergence_temp - latest_val
        extra = f' which is {diff:.3} below the emergence temperature.'
        if diff < 0:
            extra  = extra + ' EMERGENCE IMMINENT!'

    return f'Latest value for column {colname} was {latest_val:.4}, {sec_since} ago. ' + extra

@app.route('/plot/<colname>')
def plot_column(colname):
    x, y = get_data(colname)[:2]

    p = figure(plot_width=1000, plot_height=600,
            x_axis_type="datetime", tools="pan,wheel_zoom,box_zoom,reset")

    p.line(x, y)

    span_temp = None
    if colname == 'temp_c':
        span_temp = EMERGE_TEMP_C
    elif colname == 'temp_f':
        span_temp = EMERGE_TEMP_F

    if span_temp is not None:
        p.add_layout(Span(location=span_temp,
                          dimension='width', line_color='red',
                          line_dash='dotted', line_width=1))

    return file_html(p, CDN, "temp_server: " + colname)

@app.route('/png/<colname>')
def png_column(colname):
    x, y = get_data(colname)[:2]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(x, y)

    if colname == 'temp_c':
        ax1.axhline(EMERGE_TEMP_C, c='r', ls=':', alpha=.5)
    elif colname == 'temp_f':
        ax1.axhline(EMERGE_TEMP_F, c='r', ls=':', alpha=.5)

    ax1.set_ylabel(colname)

    fig.tight_layout()

    bio = io.BytesIO()
    plt.savefig(bio, format='png')

    bio.seek(0)
    return send_file(bio, mimetype='image/png')


def get_data(column_name):
    df = pd.read_table(app.config['DATA_FILE'], ' ', parse_dates=['timestamp'])

    x = df['timestamp']
    if column_name == 'temp_f' and 'temp_f' not in df:
        y = df['temp_c']*9/5 + 32
    else:
        y = df[column_name]

    return x, y, df
