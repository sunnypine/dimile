from flask import Flask,render_template,request, redirect
from StringIO import StringIO
from bokeh.plotting import figure
from bokeh.embed import components
import pandas as pd
import requests
import datetime
import numpy as np

app = Flask(__name__)

app.vars=['']*3
app.input_err = ''

@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'GET':
        app.vars = ['']*3
        if app.input_err:
            error = app.input_err
            app.input_err = ''
            return render_template('index.html', error = error)
        return render_template('index.html', error = '')
    else:
        app.vars[0]=request.form["ticker"]
        app.vars[1] = request.form['close']
        app.vars[2] = request.form['close adj']
        print app.vars
        if not app.vars[0] or not any(app.vars[1:]):
            app.input_err = 'Invalid input!'
            return redirect('/')

        return redirect('/data')

@app.route('/data')
def data():
    end = datetime.datetime.now().strftime("%Y-%m-%d")
    start = (datetime.datetime.now() - datetime.timedelta(31)).strftime("%Y-%m-%d")
    payload = {'start_date' : start, 'end_date' : end}
    try:
        quandl_back = requests.get('https://www.quandl.com/api/v3/datasets/WIKI/%s.csv'%(app.vars[0]), params = payload, timeout=10)
    except requests.exceptions.RequestException as error:
        if 'timeout' in str(error):
            return 'Server time out. Please try again later!'
        if 'Connection' in str(error):
            return "Can't connect to server. Please try again later!"
    
    if quandl_back.status_code == 404:
        app.input_err = "Couldn't find ticker %s"%(app.vars[0])
        return redirect('/')

    df = pd.read_csv(StringIO(quandl_back.text))
    color = {'Close':'blue', 'Adj. Close':'red', 'Volume':'beige'}

    p1 = figure(x_axis_type = "datetime")
    [p1.line(np.array(df['Date'],'M'), np.array(df[x]), color=color[x], legend=x) \
    for x in app.vars[1:] if x]

    title = '%s daily price'%(app.vars[0])

    p1.title = title
    p1.yaxis.axis_label = 'Price'
    p1.xaxis.axis_label = 'Date'

    script, div = components(p1)

    return render_template('/data.html', title = title, script = script, div = div)

if __name__ == "__main__":
    app.run(debug=True)
