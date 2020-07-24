CREATE KEYSPACE rides WITH replication = {'class': 'SimpleStrategy', 'replication_factor' : 1};

USE rides;

CREATE TABLE leaders_by_avgpace (id int, userId int, avgspeed float, max_speed float, avg_heart_rate int, max_heart_rate int, distance float, 
	duration varchar, avgpace varchar, leaderboard_date date, PRIMARY KEY (leaderboard_date,avgpace,userid,id))
	WITH CLUSTERING ORDER BY (avgpace ASC);

CREATE TABLE leaders_by_avgspeed (id int, userId int, avgspeed float, max_speed float, avg_heart_rate int, max_heart_rate int, distance float, 
	duration varchar, avgpace varchar, leaderboard_date date, PRIMARY KEY (leaderboard_date,avgspeed,userid,id))
	WITH CLUSTERING ORDER BY (avgspeed DESC);

CREATE TABLE leaders_by_duration (id int, userId int, avgspeed float, max_speed float, avg_heart_rate int, max_heart_rate int, distance float, 
	duration varchar, avgpace varchar, leaderboard_date date, PRIMARY KEY (leaderboard_date,duration,userid,id))
	WITH CLUSTERING ORDER BY (duration DESC);

CREATE TABLE leaders_by_distance (id int, userId int, avgspeed float, max_speed float, avg_heart_rate int, max_heart_rate int, distance float, 
	duration varchar, avgpace varchar, leaderboard_date date, PRIMARY KEY (leaderboard_date,distance,userid,id))
	WITH CLUSTERING ORDER BY (distance DESC);


