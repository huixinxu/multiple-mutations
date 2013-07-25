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

DEBUG = True#do not use when site is public (allows for easier error catching during debugging)
UPLOAD_FOLDER = os.getcwd()
ALLOWED_EXTENSIONS = set(['txt'])#Currently not used allows for easy file limiting
app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER#configuring file to save data

@app.route('/')
def openPage():#calls initial html
	return render_template('UploadPage.html')

def allowedFile(filename):#checks if uploaded file is of the correct type
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
		
@app.route('/upload', methods=['POST'])
def uploadFile():
	userData = request.files['userData']#get file from browser request
	numSubjects = request.form['subjects']#get number of study subjects from browser request
	if userData and allowedFile(userData.filename):
		dataName = secure_filename(userData.filename)
		userData.save(os.path.join(app.config['UPLOAD_FOLDER'], dataName))#save user data
	else:
		return "Your file was of an incorrect type, please change file type to .txt and try again."
	repeatMutations = runMultipleMuts(dataName)
	argsForScript = [repeatMutations, 'fixed_mut_prob_fs_adjdepdiv.txt', float(numSubjects)]
	dout = overlap2mutprobs.main(argsForScript)
	#command = "python overlap2mutprobs_1.2.py " + repeatMutations +" fixed_mut_prob_fs_adjdepdiv.txt " + numSubjects#initial command line arguement
	#args = command.split()#splitting command line into individual args
	#output = subprocess.Popen(args, stdout=subprocess.PIPE, shell=False)#run the script
	#dout, derr = output.communicate()#getting the output of the script
	
	#print dout#printing to make sure it works
	noCommas = dout.replace(", ", "|")#replacing commas between types of mutations to avoid confusion in csv files
	addCommas = noCommas.replace("\t", ",")#adding commas between data fields for csv file
	#print addCommas
	addTabs = noCommas#holder string for splitting into individual rows
	addReturns = addTabs.split("\n")#splitting into individual rows to send to display html (ReturnData.html)
	numRows= len(addReturns)#the number of rows to determine html table formatting
	return render_template('ReturnData.html', results=addReturns, iterations=numRows, downloadString=addCommas)#render the ReturnData.html with required data atributes.  These are the results as an array of lines, the number of lines, and the results as a comma delimited string

def runMultipleMuts(initialFile):
	#theCommand = "python multiple_hits_onelist.py "+initialFile
	#arguments = theCommand.split()
	#multipleMutsOutput = subprocess.Popen(arguments, stdout=subprocess.PIPE, shell=False)
	#out, err = multipleMutsOutput.communicate()
	theFile = open(initialFile, 'r')
	out = multiple_hits_onelist_noprint.runFile(theFile)
	theFile.close()
	multiOutFile = tempfile.NamedTemporaryFile(delete=False)
	multiOutFile.write(out)
	multiOutFile.close()
	return multiOutFile.name

@app.route('/download/<dataToSend>')
def downloadFile(dataToSend):
	#print "About to Return File"
	sendableString = StringIO.StringIO()#make sendableString into an easily transferrable StringIO object.
	sendableString.write('#gene	mutations,#LoF,#mis,prob(LoF),prob(mis),prob(LoF+mis),2*prob,exp#[151.0],ppois,compared_to')
	sendableString.write(str(dataToSend))#write data to it
	sendableString.seek(0)#send marker to the first position
	return send_file(sendableString, attachment_filename="YourData.csv", as_attachment=True)#return sendableString as an attachment

@app.route('/exampleData')
def exampleDownload():
	exampleData = open('exampleData.txt', 'r')
	return send_file(exampleData, attachment_filename="ExampleInputData.txt", as_attachment=True)
	
if __name__ == '__main__':
	app.run()#initialization function