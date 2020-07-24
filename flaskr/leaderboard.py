from flask import Flask, render_template, url_for, request, redirect
from cassandra.cluster import Cluster
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
cluster = Cluster(['<private_ip>']) # cassandra cluster


#formats column heading to change according to leaderboard that is displayed
def format_heading(table):
    table_metric = table[11:len(table)]
    if table_metric == 'avgspeed':
        table_metric = table_metric.replace('avgspeed', 'Average Speed')
    elif table_metric == 'avgpace':
    	table_metric = table_metric.replace('avgpace', 'Average Pace')
    else:
        table_metric = table_metric.capitalize()
    return table_metric

#home page, redirects user to leaderboard route which returns the requested leaderboard
@app.route('/',methods=['GET','POST'])
def index():
	if request.method == 'POST':
		table = request.form['metric']
		req_date = request.form['date']		
		return redirect(url_for('leaderboard',table = table, date = req_date))
	else:
		return render_template('index.html')
		
#function is run every 10 seconds to update leaderboard that user requested
#if no 'POST' request are issued to select a different leaderboard, the same leaderboard user originally selected is updated
@app.route('/leaderboard',methods=['GET','POST'])
def leaderboard():
	if request.method == 'POST': # selects different leaderboard
		table = request.form['metric'] 
		req_date = request.form['date'] 
		return redirect(url_for('leaderboard',table = table, date = req_date))
	else: 
		table = request.args.get('table') #request leaderboard user selected from index route
		req_date = request.args.get('date') #request date of leaderboard user selected
	session = cluster.connect('rides') # cassandra keyspace
	metric = table[11:len(table)]
	query = "select id,{0},distance from {1} where leaderboard_date = '{2}' limit 5".format(metric,table,req_date) #formats query based on leaderboard requested
	ans = session.execute(query)
	return render_template('leaderboard.html',results = ans, table = format_heading(table), req_date = req_date)


if __name__ == "__main__":
	sched = BackgroundScheduler() # scheduler object
	sched.add_job(leaderboard,'interval',seconds=60) #runs query every 60 seconds to update leaderboard table
	sched.start()
	app.run(debug=True)


