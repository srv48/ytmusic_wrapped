# YouTube Music Year Wrapper
A spotify year wrap like for YouTube Music

Note : This project is not endorsed by Google

![example of a report](https://raw.githubusercontent.com/cinfulsinamon/ytmusic_wrapped/master/example_report.png)

## To use YouTube Music Year Wrapper
<br>
You will need to install Python. I used 3.8.0 32bit, so use that version if you want to be super safe.
Be sure to select the "Add python to PATH" option in the installer.
<br>
Once python is installed, open up a console and run `pip install requests` to get the required module for this script.
<br>
Download this repo using git or by downloading the master.zip in browser.
<br>
Extract the zip file somewhere you can point a terminal to it.
<br>
Then download a history file from Google My Activity containing your YouTube Watch History.
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

You will need to extract the `watch-history.json` file from within the archive it generates. Place it in the same folder as the script to make things easier.
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
Your report will be available in report.html and report.dat. Note that it usually takes less than 1 minute to complete a report. However `-d` option can increase this.
An HTML file with a report formatted like the image above will be generated in the same folder as the script.
If you want the font to look correct, you'll have to download and install the Roboto and Product Sans fonts.
