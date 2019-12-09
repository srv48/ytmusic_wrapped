import sqlite3
import datetime
import sys, getopt
import json
import requests
import re

expect = datetime.datetime.now().year
verbose = False
duration = False

def flags():
	opts, args = getopt.getopt(sys.argv[2:], "d:v", ["duration="])
	for o, token in opts:
		if o == "-v":
			global verbose
			verbose = True
		elif o in ("-d", "--duration"):
			global duration
			duration = True
			global ytAPIkey
			ytAPIkey = token

def i18n_string(string):
	fr = string[:8]
	en = string[:7]
	if (fr.encode("utf-8") == "A écouté"):
		return True
	elif (en.encode("utf-8") == "Watched"):
		return True
	else:
		return False

def i18n_title(title):
	fr = title[:8]
	en = title[:7]
	if (fr.encode("utf-8") == "A écouté"):
		return title[9:]
	if (en.encode("utf-8") == "Watched"):
		return title[8:]
        
def il8n_url(url):
    str = url[32:]
    return str

def should_not_ignore(title, year, header, expect):
    if (header.encode("utf-8") == "YouTube Music"):
        if (i18n_string(title)):
            if (year[:4].encode("utf-8") == str(expect)):
                return True
            else:
                False
        else:
            return False
    else:
        return False

def open_file():
	if (sys.argv[1].endswith('.json')):
		try:
			file = open(sys.argv[1], "r")
			return file
		except:
			print "Could not open your history file"
			sys.exit()
	else:
		print "Your history file should be a json file"
		sys.exit()

def parse_json(file, cursor):
    json_object = json.load(file)
    for obj in json_object:
        if (should_not_ignore(obj['title'], obj['time'], obj['header'], expect)):
            if ('subtitles' in obj):
                cursor.execute("""INSERT INTO songs(title, artist, year, url) VALUES(?, ?, ?, ?)""", (i18n_title(obj['title']), obj['subtitles'][0]['name'], obj['time'], il8n_url(obj['titleUrl'])))
            elif ('titleUrl' in obj):
                cursor.execute("""INSERT INTO songs(title, artist, year, url) VALUES(?, ?, ?, ?)""", ("parseme", "parseme", obj['time'], il8n_url(obj['titleUrl'])))

def print_db(cursor):
	#Print results from DB
    print ("####################Full List#####################")
    cursor.execute("""SELECT id, artist, title, url, year FROM songs""")
    rows = cursor.fetchall()
    for row in rows:
        datetime.datetime.now()
        print('{0} : {1} - {2} - {4} - {3}'.format(row[0], row[1].encode("utf-8"), row[2].encode("utf-8"), row[3].encode("utf-8"), row[4]))
    print ("####################Non-Duplicate List#####################")
    cursor.execute("""SELECT id, artist, title, url, occurence FROM report""")
    rows = cursor.fetchall()
    for row in rows:
        datetime.datetime.now()
        print('{0} : {1} - {2} - {3} - {4}'.format(row[0], row[1].encode("utf-8"), row[2].encode("utf-8"), row[3].encode("utf-8"), row[4]))

def prepare_tops(cursor):
	#Artist top
    cursor.execute("""SELECT artist FROM report GROUP BY artist""")
    result = cursor.fetchall()
    for res in result:
        occurences = 0
        cursor.execute("""SELECT occurence FROM report WHERE artist = ?""", (res[0],))
        artocc = cursor.fetchall()
        for occ in artocc:
            occurences += occ[0]
        cursor.execute("""INSERT INTO artist_count(artist, occurence) VALUES(?, ?)""", (res[0], occurences))

	#Song Top
    cursor.execute("""SELECT title, occurence FROM report GROUP BY url""")
    result_song = cursor.fetchall()
    for res_song in result_song:
        cursor.execute("""INSERT INTO songs_count(title, occurence) VALUES(?, ?)""", (res_song[0], res_song[1]))

def delete_duplicate(cursor):
	#Doublon Deletor
    cursor.execute("""SELECT title, COUNT(*), artist, url FROM songs GROUP BY url""")
    result_doublon = cursor.fetchall()
    for res_doublon in result_doublon:
        cursor.execute("""INSERT INTO report(title, artist, occurence, url, duration) VALUES(?, ?, ?, ?, 0)""", (res_doublon[0], res_doublon[2], res_doublon[1], res_doublon[3]))
    cursor.execute("""SELECT id, artist, title, url FROM report""")
    rows = cursor.fetchall()
    for row in rows:
        if (row[2].encode("utf-8") == "parseme"):
           cursor.execute("""SELECT artist, title FROM songs WHERE url = ? AND title != ?""",(row[3],"parseme"))
           match = cursor.fetchone()
           if match:
               cursor.execute("""UPDATE report SET artist = ?, title = ? WHERE id = ?""",(match[0],match[1],row[0]))
    if not duration:
        cursor.execute("""DELETE FROM report WHERE title = 'parseme'""")
        
def print_full_tops(cursor):
	print ("####################Top Artists#####################")
	cursor.execute("""SELECT artist, occurence FROM artist_count ORDER by occurence DESC""")
	rows = cursor.fetchall()
	for row in rows:
		datetime.datetime.now()
		print('{0} - {1}'.format(row[0].encode("utf-8"), row[1]))

	print ("####################Top Songs#####################")
	cursor.execute("""SELECT title, occurence FROM songs_count ORDER by occurence DESC""")
	rows = cursor.fetchall()
	for row in rows:
		datetime.datetime.now()
		print('{0} - {1}'.format(row[0].encode("utf-8"), row[1]))
        
def parse_duration(duration):
    timestr = duration.encode("utf-8")
    time = re.findall(r'\d+', timestr) 
    length = len(time)
    if length > 4:
        return 0
    if length == 4:
        return ((int(time[0])*24*60*60)+(int(time[1])*60*60)+int(time[2]*60)+(int(time[3])))
    elif length == 3:
        return ((int(time[0])*60*60)+(int(time[1])*60)+(int(time[2])))
    elif length == 2:
        return ((int(time[0])*60)+(int(time[1])))
    elif length == 1:
        return (int(time[0]))
    else:
        return 0

def get_duration(cursor):
    #Count duration
    cursor.execute("""SELECT id, artist, title, url FROM report""")
    rows = cursor.fetchall()
    for row in rows:
        datetime.datetime.now()
        artist = row[1]
        title = row[2]
        if (row[2].encode("utf-8")=="parseme"):
            parameters = {"part": "contentDetails,snippet", "id": row[3].encode("utf-8"), "key": ytAPIkey}
        else:
            parameters = {"part": "contentDetails", "id": row[3].encode("utf-8"), "key": ytAPIkey}
        response = requests.get("https://www.googleapis.com/youtube/v3/videos", params=parameters)
        if (response.status_code == 200):
            json_parsed = response.json()
            if (json_parsed['pageInfo']['totalResults'] == 0):
                print "video not found"
                if (row[1].encode("utf-8")=="parseme"):
                    title = "Unavailable Video"
                    artist = "Unknown Artist"
                    cursor.execute("""UPDATE report SET duration = ?, artist = ?, title = ? WHERE id = ?""", (0, artist, title, row[0]))
                    continue
            else:
                if verbose:
                    print ('duration {0}'.format(row[0]))
                duration = parse_duration(json_parsed['items'][0]['contentDetails']['duration'])
                if (row[1].encode("utf-8")=="parseme"):
                    artist = json_parsed['items'][0]['snippet']['channelTitle']
                    title = json_parsed['items'][0]['snippet']['title']
                    cursor.execute("""UPDATE report SET duration = ?, artist = ?, title = ? WHERE id = ?""", (duration, artist, title, row[0]))
                    
    #Calcul total duration
    if verbose:
        print ("####################Full List WITHOUT DOUBLON AND DURATION#####################")
    total_duration = 0
    error_rate = 0
    cursor.execute("""SELECT id, artist, title, duration, occurence FROM report""")
    rows = cursor.fetchall()
    for row in rows:
        datetime.datetime.now()
        song_count = row[0]
        if verbose:
            print('{0} : {1} - {2}- {3} - occurence : {4}'.format(row[0], row[1].encode("utf-8"), row[2].encode("utf-8"), row[3], row[4]))
        total_duration += row[3] * row[4]
        if row[3] == 0:
            error_rate = error_rate + 1
    return (total_duration, error_rate, song_count)

def gen_html_report(cursor, data, expect):
	sys.stdout = open('report.html', 'w')
	print ("""<!DOCTYPE html><html><head><title>Wrapped</title><style type="text/css">body{background-color: #000000;}.center-div{position: absolute; margin: auto; top: 0; right: 0; bottom: 0; left: 0; width: 50%; height: 90%; background-color: #000000; border-radius: 3px; padding: 10px;}.ytm_logo{width: 15%;position: relative;top: 30px;left: 40px;}.title_logo{width: 30%;position: relative;top: 30px;left: 60px;}.right_title{position: absolute;font-family: "Product Sans";top: 55px;right: 10%;font-size: 2em;color: #ffffff;}.container{position: relative;top: 13%;left: 53px;}.minutes_title{font-family: "Product Sans";font-size: 2em;color: #ffffff;}.minutes{font-family: "Product Sans";font-size: 6em;color: #ffffff;}.row{display: flex;}.column{flex: 50%;}.list{font-family: "Roboto";font-size: 1.5em;line-height: 30px;color: #ffffff;}</style></head><body><div class="center-div"><img src="ytm_logo.png" class="ytm_logo"><img src="title.png" class="title_logo"/><span class="right_title">""")
	print (expect)
	print (""" Wrapped</span><div class="container"><div class="minutes_title">Minutes Listened</div><div class="minutes">""")
	if duration:
		print (data[0]/60)
	else:
		print("N/A")
	print ("""</div><br><br><div class="row"><div class="column"><div class="minutes_title">Top Artists</div><div class="list">""")
	cursor.execute("""SELECT artist, occurence FROM artist_count ORDER by occurence DESC LIMIT 10""")
	rows = cursor.fetchall()
	for row in rows:
		print ("<br>")
		print('{0} - {1} songs'.format(row[0].encode("utf-8"), row[1]))
	print ("""</div></div><div class="column"><div class="minutes_title">Top Songs</div><div class="list">""")
	cursor.execute("""SELECT title, occurence FROM songs_count ORDER by occurence DESC LIMIT 10""")
	rows = cursor.fetchall()
	for row in rows:
		print ("<br>")
		print ('{0} - {1} plays'.format(row[0].encode("utf-8"), row[1]))
	print ("""</div></div></div></div></div></body></html>""")
	sys.stdout.close()

def gen_report(cursor, data, expect):
	#Top 10 Report
	sys.stdout = open('report.dat', 'w')
	print ("#################### Top Artists #####################")
	cursor.execute("""SELECT artist, occurence FROM artist_count ORDER by occurence DESC LIMIT 10""")
	rows = cursor.fetchall()
	for row in rows:
		datetime.datetime.now()
		print('{0} - {1}'.format(row[0].encode("utf-8"), row[1]))

	print ("#################### Top Songs #####################")
	cursor.execute("""SELECT title, occurence FROM songs_count ORDER by occurence DESC LIMIT 10""")
	rows = cursor.fetchall()
	for row in rows:
		datetime.datetime.now()
		print('{0} - {1}'.format(row[0].encode("utf-8"), row[1]))

	if duration:
		print ("\n#################### Duration #####################")
		print ('Total duration : {0}', data[0])
		print ('Total song count : ', data[2])
		print ('Error count : ', data[1])
		print ('Error rate : {0}%'.format((float(data[1])/data[2])*100))
	sys.stdout.close()
	gen_html_report(cursor, data, expect)

def main():
    flags()
    conn = sqlite3.connect('gmusic.db')
    cursor = conn.cursor()
    with open('schema.sql') as fp:
        cursor.executescript(fp.read())
    data = ""

    file = open_file()

    print ("Welcome to YouTube Music Year Wrapper.")
    print ("We are now processing your file.")
    print ("No more informations will be displayed during this process. You can check log.dat at any time to check progression.")

    if verbose:
        sys.stdout = open('log.dat', 'w')
    parse_json(file, cursor)
    delete_duplicate(cursor)
    
    if verbose:
        print_db(cursor)
	prepare_tops(cursor)
	if verbose:
		print_full_tops(cursor)
	if duration:
		data = get_duration(cursor)
    if verbose:
        sys.stdout.close()
    gen_report(cursor, data, expect)

if __name__ == "__main__":
	main()