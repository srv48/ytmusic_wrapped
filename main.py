﻿import sqlite3
import datetime
import sys
import getopt
import json
import requests
import re

analyzeYear = "2020"#datetime.datetime.now().year
verbose = False
duration = False
moreDetails = False
log = open('log.dat', 'w', encoding="utf8")

def flags():
    opts, args = getopt.getopt(sys.argv[2:], "d:y:mv", ["duration=", "year="])
    for o, token in opts:
        if o == "-v":
            global verbose
            verbose = True
        elif o == "-m":
            global moreDetails
            moreDetails = True
        elif o in ("-d", "--duration"):
            global duration
            duration = True
            global ytAPIkey
            ytAPIkey = token
        elif o in ("-y", "--year"):
            global analyzeYear
            analyzeYear = token

def should_not_ignore(title, year, header, analyzeYear):
    if (header == "YouTube Music"):
        if (title[:7] == "Watched"):
            if (year[:4] == str(analyzeYear)):
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
            file = open(sys.argv[1], "r", encoding="utf8")
            return file
        except:
            print("Could not open your history file")
            sys.exit()
    else:
        print("Your history file should be a json file")
        sys.exit()

def parse_json(file, cursor):
    json_object = json.load(file)
    for obj in json_object:
        if (should_not_ignore(obj['title'], obj['time'], obj['header'], analyzeYear)):
            if ('subtitles' in obj):
                cursor.execute("""INSERT INTO songs(title, artist, year, url) VALUES(?, ?, ?, ?)""", (
                    obj['title'][8:], obj['subtitles'][0]['name'], obj['time'], obj['titleUrl'][32:]))
            elif (('titleUrl' in obj) and (duration)):
                cursor.execute("""INSERT INTO songs(title, artist, year, url) VALUES(?, ?, ?, ?)""", (
                    "parseme", "parseme", obj['time'], obj['titleUrl'][32:]))

def print_db(cursor):
    # Print results from DB
    print("####################Full List#####################", file=log)
    cursor.execute("""SELECT id, artist, title, url, year FROM songs""")
    rows = cursor.fetchall()
    for row in rows:
        datetime.datetime.now()
        print(
            '{0} : {1} - {2} - {4} - {3}'.format(row[0], row[1], row[2], row[3], row[4]), file=log)
    print("####################Non-Duplicate List#####################", file=log)
    cursor.execute("""SELECT id, artist, title, url, occurence FROM report""")
    rows = cursor.fetchall()
    for row in rows:
        datetime.datetime.now()
        print(
            '{0} : {1} - {2} - {3} - {4}'.format(row[0], row[1], row[2], row[3], row[4]), file=log)

def prepare_tops(cursor):
    # Artist top
    cursor.execute("""SELECT artist FROM report GROUP BY artist""")
    result = cursor.fetchall()
    for res in result:
        occurences = 0
        total_duration = 0
        cursor.execute(
            """SELECT occurence, duration FROM report WHERE artist = ?""", (res[0],))
        artocc = cursor.fetchall()
        for occ in artocc:
            occurences += occ[0]
            total_duration += occ[1]
        cursor.execute("""INSERT INTO artist_count(artist, occurence, duration) VALUES(?, ?, ?)""",
                       (res[0], occurences, total_duration))

        # Song Top
    cursor.execute(
        """SELECT title, artist, occurence FROM report GROUP BY url""")
    result_song = cursor.fetchall()
    for res_song in result_song:
        cursor.execute("""INSERT INTO songs_count(title, artist, occurence) VALUES(?, ?, ?)""",
                       (res_song[0], res_song[1], res_song[2]))

def delete_duplicate(cursor):
    # Doublon Deletor
    cursor.execute(
        """SELECT title, COUNT(*), artist, url FROM songs GROUP BY url""")
    result_doublon = cursor.fetchall()
    for res_doublon in result_doublon:
        cursor.execute("""INSERT INTO report(title, artist, occurence, url, duration) VALUES(?, ?, ?, ?, 0)""",
                       (res_doublon[0], res_doublon[2], res_doublon[1], res_doublon[3]))
    cursor.execute(
        """SELECT id, artist, title, url FROM report WHERE title = 'parseme'""")
    rows = cursor.fetchall()
    for row in rows:
        cursor.execute(
            """SELECT artist, title FROM songs WHERE url = ? AND title != ?""", (row[3], "parseme"))
        match = cursor.fetchone()
        if match:
            cursor.execute(
                """UPDATE report SET artist = ?, title = ? WHERE id = ?""", (match[0], match[1], row[0]))
    if not duration:
        cursor.execute("""DELETE FROM report WHERE title = 'parseme'""")

def print_full_tops(cursor):
    print("####################Top Artists#####################", file=log)
    cursor.execute(
        """SELECT artist, occurence FROM artist_count ORDER by occurence DESC""")
    rows = cursor.fetchall()
    for row in rows:
        datetime.datetime.now()
        print('{0} - {1}'.format(row[0], row[1]), file=log)

    print("####################Top Songs#####################", file=log)
    cursor.execute(
        """SELECT artist, title, occurence FROM songs_count ORDER by occurence DESC""")
    rows = cursor.fetchall()
    for row in rows:
        datetime.datetime.now()
        print('{0} - {1} - {2}'.format(row[0], row[1], row[2]), file=log)


def parse_duration(duration):
    timestr = duration
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

def call_api(idlist, cursor):
    print("api called", file=log)
    parameters = {"part": "contentDetails,snippet",
                  "id": ','.join(idlist), "key": ytAPIkey}
    response = requests.get(
        "https://www.googleapis.com/youtube/v3/videos", params=parameters)
    if (response.status_code == 200):
        json_parsed = response.json()
        for item in json_parsed['items']:
            duration = parse_duration(item['contentDetails']['duration'])
            artist = item['snippet']['channelTitle']
            title = item['snippet']['title']
            url = item['id']
            cursor.execute(
                """UPDATE report SET duration = ?, artist = ?, title = ? WHERE url = ?""", (duration, artist, title, url))

def get_duration(cursor):
    # Count duration
    cursor.execute("""SELECT id, artist, title, url FROM report""")
    rows = cursor.fetchall()
    print("\tNumber of videos: " + str(len(rows)))
    idlist = []
    calls = 0
    for row in rows:
        idlist.append(row[3])
        if len(idlist) == 50:
            print("\tGetting info on videos " +
                  str(1+50*calls) + " - " + str(50+50*calls))
            print(','.join(idlist), file=log)
            call_api(idlist, cursor)
            calls = calls + 1
            idlist = []
    print("\tGetting info on videos " +
          str(1+50*calls) + " - " + str(len(rows)))
    print(','.join(idlist), file=log)
    call_api(idlist, cursor)
    cursor.execute("""UPDATE report SET duration = ?, artist = ?, title = ? WHERE title = ?""",
                   (0, "Unknown Artist", "Unavailable Video", "parseme"))

    # Calculate total duration
    if verbose:
        print("####################Full List WITHOUT DOUBLON AND DURATION#####################", file=log)
    song_count = 0
    total_duration = 0
    error_rate = 0
    cursor.execute(
        """SELECT id, artist, title, duration, occurence, url FROM report""")
    rows = cursor.fetchall()
    for row in rows:
        datetime.datetime.now()
        song_count = row[0]
        if verbose:
            print('{0} : {1} - {2}- {3} - occurence : {4} - {5}'.format(
                row[0], row[1], row[2], row[3], row[4], row[5]), file=log)
        total_duration += row[3] * row[4]
        if row[3] == 0:
            error_rate = error_rate + 1
    return (total_duration, error_rate, song_count)

def gen_html_report(cursor, data, analyzeYear):
    htmlreport = open('report_{0}.html'.format(
        str(analyzeYear)), 'w', encoding=("utf8"))
    print("""<!DOCTYPE html><html><head><title>Wrapped</title><style type="text/css">body{background-color: #000000;}.center-div{position: absolute; margin: auto; top: 0; right: 0; bottom: 0; left: 0; width: 50%; height: 90%; background-color: #000000; border-radius: 3px; padding: 10px;}.ytm_logo{width: 15%;position: relative;top: 30px;left: 40px;}.title_logo{width: 30%;position: relative;top: 30px;left: 60px;}.right_title{position: absolute;font-family: "Product Sans";top: 55px;right: 10%;font-size: 2em;color: #ffffff;}.container{position: relative;top: 13%;left: 53px;}.minutes_title{font-family: "Product Sans";font-size: 2em;color: #ffffff;}.minutes{font-family: "Product Sans";font-size: 6em;color: #ffffff;}.row{display: flex;}.column{flex: 50%;}.list{font-family: "Roboto";font-size: 1.5em;line-height: 30px;color: #ffffff;}</style></head><body><div class="center-div"><img src="ytm_logo.png" class="ytm_logo"><img src="title.png" class="title_logo"/><span class="right_title">""", file=htmlreport)
    print(str(analyzeYear), file=htmlreport)
    print(""" Wrapped</span><div class="container"><div class="minutes_title">Minutes Listened</div><div class="minutes">""", file=htmlreport)
    if duration:
        print(str(data[0]//60), file=htmlreport)
    else:
        print("N/A", file=htmlreport)
    print("""</div><br><br><div class="row"><div class="column"><div class="minutes_title">Top Artists</div><div class="list">""", file=htmlreport)
    if duration:
        cursor.execute("""SELECT artist, occurence, duration FROM artist_count WHERE (occurence > 5) ORDER by duration DESC LIMIT 20""")
    else:
        cursor.execute("""SELECT artist, occurence, duration FROM artist_count WHERE (occurence > 5) ORDER by occurence DESC LIMIT 20""")
    rows = cursor.fetchall()
    for row in rows:
        print("<br>", file=htmlreport)
        if moreDetails:
            if duration:
                print('{0} - {1} songs ({2} mins)'.format(str(row[0]).replace(' - Topic', ''), row[1], str(row[2]//60)), file=htmlreport)
            else:
                print('{0} - {1} songs'.format(str(row[0]).replace(' - Topic', ''), row[1]), file=htmlreport)
        else:
            print('{0}'.format(str(row[0]).replace(
                ' - Topic', '')), file=htmlreport)
    print("""</div></div><div class="column"><div class="minutes_title">Top Songs</div><div class="list">""", file=htmlreport)
    cursor.execute(
        """SELECT artist, title, occurence FROM songs_count ORDER by occurence DESC LIMIT 20""")
    rows = cursor.fetchall()
    for row in rows:
        print("<br>", file=htmlreport)
        if moreDetails:
            print('{0} - {1} - {2} plays'.format(str(row[0]).replace(
                ' - Topic', ''), row[1], row[2]), file=htmlreport)
        else:
            print('{0}'.format(row[1]), file=htmlreport)
    print("""</div></div></div></div></div></body></html>""", file=htmlreport)
    htmlreport.close()

def gen_report(cursor, data, analyzeYear):
    # Top 10 Report
    report = open('report_{0}.dat'.format(
        str(analyzeYear)), 'w', encoding=("utf8"))
    print("#################### Top Artists #####################", file=report)
    cursor.execute(
        """SELECT artist, occurence FROM artist_count ORDER by occurence DESC""")
    rows = cursor.fetchall()
    for row in rows:
        datetime.datetime.now()
        print('{0} - {1}'.format(row[0], row[1]), file=report)

    print("#################### Top Songs #####################", file=report)
    cursor.execute(
        """SELECT artist, title, occurence FROM songs_count ORDER by occurence DESC""")
    rows = cursor.fetchall()
    for row in rows:
        datetime.datetime.now()
        print('{0} - {1} - {2}'.format(row[0], row[1], row[2]), file=report)

    if duration:
        print("\n#################### Duration #####################", file=report)
        print('Total duration : {0}'.format(data[0]), file=report)
        print('Total song count : {0}'.format(data[2]), file=report)
        print('Error count : {0}'.format(data[1]), file=report)
        print('Error rate : {0}%'.format(
            (float(data[1])/data[2])*100), file=report)
    report.close()
    gen_html_report(cursor, data, analyzeYear)

def main():
    flags()
    conn = sqlite3.connect('ytmusic.db')
    cursor = conn.cursor()
    with open('schema.sql') as fp:
        cursor.executescript(fp.read())
    data = ""

    file = open_file()

    print("Welcome to YouTube Music Year Wrapper.")
    print("We are now processing your file.")

    parse_json(file, cursor)
    print("Removing duplicates")
    delete_duplicate(cursor)

    if verbose:
        print_db(cursor)
    if duration:
        print("Getting durations. This may take a while.")
        data = get_duration(cursor)
    print("Getting top 20's")
    prepare_tops(cursor)
    if verbose:
        print_full_tops(cursor)
    log.close()
    print("Generating final report")
    gen_report(cursor, data, analyzeYear)
    conn.commit()
    conn.close()
    print("All done!")

if __name__ == "__main__":
    main()