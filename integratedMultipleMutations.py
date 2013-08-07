'''
overlap2mutprobsInterface.py is a web interface for the python script to calculate
the statistical significance of multiple de novo events found in any specific gene.
The interface uses two html templates (ReturnData.html and UploadPage.html) to allow
a public user to use the overlap2mutprobs.py script on their own data.

Required local software:
	See requirements.txt

Required local files:
	1) Per gene mutation probability file (fixed_mut_prob_fs_adjdepdiv.txt)
	2) The actual script (overlap2mutprobs_1.2.py)
	3) The multiple hits one gene script (multiple_hits_onelist.py)
	4) The user data example (exampleData.txt)
	5) A templates directory containing ReturnData.html and UploadPage.html
	6) A static directory

Required user inputs (through HTML):
	1) Genes with multiple mutations list
	2) The number of study participants
	
'''
import os
import subprocess
import tempfile
from flask import Flask, request, Response, session, g, redirect, url_for, \
	abort, render_template, flash, send_from_directory, send_file
from werkzeug import secure_filename
import StringIO
import multiple_hits_onelist_noprint
import overlap2mutprobs
from datetime import datetime

DEBUG = True#do not use when site is public (allows for easier error catching during debugging)
UPLOAD_FOLDER = os.getcwd()
ALLOWED_EXTENSIONS = set(['txt'])
app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER#configuring file to save data

SERVER_NAME = '127.0.0.1'
SERVER_PORT = 5002

@app.route('/')
def openPage():
	#calls initial html
	if 'username' in session:
		return render_template('UploadPage.html')
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
    	if request.form['username'] == 'ATGUuser':
        	session['username'] = request.form['username']
        	return redirect(url_for('openPage'))
        else:
        	return '''
    			<p>Incorrect Username
        		<form action="" method="post">
        		    <p><input type=text name=username>
        		    <p><input type=submit value=Login>
        		</form>
        		'''
    return '''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=submit value=Login>
        </form>
        '''

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('openPage'))

def allowedFile(filename):
	#checks if uploaded file is of the correct type
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
		
@app.route('/upload', methods=['POST'])
def uploadFile():
	#handles data from the form in UploadPage.html
	#gets the file and the number of subjects
	if request.method == 'POST':
		numSubjects = request.form['subjects']
		if request.form['inputType'] == '1':
			userData = request.files['userData']
			if userData and allowedFile(userData.filename):
				dataName = secure_filename(userData.filename)
				userData.save(os.path.join(app.config['UPLOAD_FOLDER'], dataName))
			else:
				return "Your file was of an incorrect type, please change file type to .txt and try again."
		else:
			dataFile = open('userData.txt', 'r+')
			dataFile.write(request.form['userInput'])
			dataName = 'userData.txt'
		repeatMutations = runMultipleMuts(dataName)
		argsForScript = [repeatMutations, 'fixed_mut_prob_fs_adjdepdiv.txt', float(numSubjects)]
		dout = overlap2mutprobs.main(argsForScript)
		noCommas = dout.replace(", ", "|")
		addCommas = noCommas.replace("\t", ",")
		addTabs = noCommas
		addReturns = addTabs.split('\n')
		roundReturns = []
		finalReturns = []
		for row in addReturns:
			row = row.split('\t')
			returnRow = []
			for piece in row:
				try:
					returnRow.append(round_to_n(float(piece), 3))
				except ValueError:
					returnRow.append(piece)
			if len(returnRow) >3:
				returnRow[2] = int(returnRow[2])
				returnRow[3] = int(returnRow[3])
			finalReturns.append(returnRow)
		numRows= len(addReturns)
		return render_template('ReturnData.html', results=finalReturns, iterations=numRows, downloadString=addCommas, numSubjects=numSubjects)

def round_to_n(x, n):
    if n < 1:
        raise ValueError("number of significant digits must be >= 1")
    # Use %e format to get the n most significant digits, as a string.
    format = "%." + str(n-1) + "e"
    as_string = format % x
    return float(as_string)

def runMultipleMuts(initialFile):
	#takes a file name and runs multiple_hits_onelist_noprint.py on it
	#multiple_hits... finds all of the genes with multiple mutations
	theFile = open(initialFile, 'r')
	out = multiple_hits_onelist_noprint.runFile(theFile)
	theFile.close()
	multiOutFile = tempfile.NamedTemporaryFile(delete=False)
	multiOutFile.write(out)
	multiOutFile.close()
	return multiOutFile.name

@app.route('/download/<dataToSend>')
def downloadFile(dataToSend):
	#takes dataToSend and returns it as a download
	sendableString = StringIO.StringIO()
	sendableString.write('#gene	mutations, mutations, #LoF,#mis,prob(LoF),prob(mis),prob(LoF+mis),2*prob,exp#[151.0],ppois,compared_to\n')
	sendableString.write(str(dataToSend))
	sendableString.seek(0)
	time = datetime.now()
	splitTime = str(time).rsplit('.', 1)[0]
	return send_file(sendableString, attachment_filename="SOME Results "+splitTime+".csv", as_attachment=True)

@app.route('/exampleData')
def exampleDownload():
	#allows the download of an example file
	exampleData = open('exampleData.txt', 'r')
	time = datetime.now()
	splitTime = str(time).rsplit('.', 1)[0]
	return send_file(exampleData, attachment_filename="Example SOME Input "+splitTime+".txt", as_attachment=True)

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__ == '__main__':
	app.run(SERVER_NAME, SERVER_PORT)#initialization function