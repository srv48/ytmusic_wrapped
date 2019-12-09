# YouTube Music Year Wrapper
## NOTE: while this works, Google has an API quota set for these requests and each operation is costly. Running on my own history of 2016 unique songs (by url) cost me 7.5k out of the 10k quota. Getting duration costs 3 units, 5 if the title needs to be grabbed due to the anomalies in the watch history JSON. Gonna look into using plain HTML requests to get titles at least, but I don't think anything can be done for duration calc.
A spotify year wrap like for YouTube Music

Note : This project is not endorsed by Google

![alt text](https://raw.githubusercontent.com/cinfulsinamon/gmusic_wrapped/master/example_report.png)

## To use YouTube Music Year Wrapper
`git clone https://github.com/cinfulsinamon/gmusic_wrapped.git`
<br>
`sudo pip install requests`
<br>
<br>
Then download a history file from Google My Activity containing your Play Music History.
<br>
To download a history file: 
1) <a href="https://takeout.google.com/"> Go here</a>. 
2) Click `Deselect All` above the first checkbox.
3) Scroll all the way down to YouTube, and only check that box. 
4) Click the button that says `Multiple Formats`.
5) Next to `History`, select the `JSON` option from the dropdown box and Click OK.
6) Click on the `All YouTube data included` button. 
7) Click `Deselect All`, and then only check `History`. Click OK. 
8) Scroll down and hit next step to finish your takeout. 

You will need to extract the `watch-history.json` file from within the archive it generates.
<br><br>
You can now launch the script with the following options :
<br>
`python main.py [path/to/your/json/history_file]`
<br>
`-v` to enable a full detailed log in log.dat
<br>
`-d [YouTube API key]` to enable duration calculation
<br>
<br>
Your report will be available in report.html and report.dat. Note that it usually takes less than 1 minute to complete a report. However `-d` option can add several hours to the process.
