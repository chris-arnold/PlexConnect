#!/usr/bin/env python

#Need to remove release update button
#Will only update to most recent dev commit
#Has two update types. git and tarball DL
#Need to send updates to UI from update script
#	* Probably via JS popup window
#	* Should have spinning wheel after click
#	* After update, popup telling Success/fail and to close/open app

import urllib2, json, ConfigParser, os, sys, tarfile, shutil
import subprocess

from Debug import *  # dprint()

import pprint

class updater():
	def __init__(self, UType):
		dprint('Updater', 0, "Initializing Updater")
		self.updateRequested = UType
		#dprint("Updater",0, "Update Type: %s" % self.updateRequested)
		#print "Need to open config file"
		self.owner = "iBaa"			#"chris-arnold" for my update version when working
		self.repo = "PlexConnect"
		self.version = ""
		self.updateType = ""
		self.published = "2014-12-14T18:36:19Z" #from config
		self.status = ""
		self.updateFile = "update.tar.gz"
		self.changes = ""
		self.gitInstalled = True
		self.baseInstall = os.getcwd()
		try:
			changeLog = open("CHANGELOG.txt", "r")
			log = changeLog.readlines()
			#print log
			self.updateType = log[0].strip()	#releases, or dev
			self.version = log[1].strip()		#release, or sha
			self.published = log[2].strip()
			#exit()
			changeLog.close()
		except:
			dprint ("Updater", 0, "No ChangeLog. Running Update Selected")

		self.baseDownloadURL = os.path.join("https://github.com/", self.owner, self.repo, "archive")
		self.baseURL = os.path.join("https://api.github.com/repos", self.owner, self.repo) #/releases/latest"
		dprint('Updater', 0, 'Checking for git installation')
		try:
			null = open(os.devnull, 'w')
			subprocess.Popen('git', stdout=null, stderr=null)
			null.close()
			dprint('Updater', 0, 'Git found. Will use Git Update')
		except OSError:
			self.gitInstalled = False
			dprint('Updater', 0, 'Git not found, fall back to zip updates')

		#self.upgrade()	#Allow Plexconnect to init this class and have it run the update

	def writeLog(self):
		ChangeLog = open("CHANGELOG.txt", "w")
		ChangeLog.write(self.updateType + "\n" + self.version + "\n" + self.published + '\n\n')
		ChangeLog.write(self.changes)
		ChangeLog.close()

	def getNewestRelease(self):
		'Get info for Newest Release'
		response = urllib2.urlopen(os.path.join(self.baseURL, "releases", "latest")).read()
		data = json.loads(response)
		#latest_repo = gh.repos.list('iBaa').latest()
		self.newestVersion = data["tag_name"]
		self.changes = data["body"].encode('utf-8')
		self.newestName = data["name"]
		self.newestPublished = data["published_at"]
		self.newestTarget_Commitish = data["target_commitish"]
		self.newestTarballURL = data["tarball_url"]

	def getLatestCommit(self):
		response = urllib2.urlopen(os.path.join(self.baseURL, "commits")).read()
		data = json.loads(response)
		c=0
		for x in data:
			if c == 0:
				self.newestVersion = x["sha"]
				self.newestPublished = x["commit"]["author"]["date"]

			self.changes += x["commit"]["message"].encode('utf-8')
			c += 1

		self.newestTarballURL = os.path.join(self.baseDownloadURL, self.newestVersion) + ".tar.gz"


	def isUpdateRequired(self):
		'Check if Newest release is newer than currently installed'
		if self.newestPublished == None:
			return False

		if self.newestPublished > self.published:
			return True

	def getUpdate(self):
		dprint('Updater', 0, "Downloading Update")
		try:
			response = urllib2.urlopen(self.newestTarballURL)
			data = response.read()
			with open(self.updateFile, "wb") as f:
				f.write(data)
			self.status="Success"
			
		except Exception, e:
			dprint('Updater', 0, "Update Failed", e)
			self.status="Failed"

	def extractTarball(self):
		'Extracts tarball. Returns list of files extracted'
		dprint('Updater', 0, "Extracting Update")
		tar = tarfile.open(self.updateFile)
		contents = tar.getnames()
		self.updateBase = os.path.join(os.getcwd(), contents[0])
		tar.extractall()
		tar.close()

	def copyTree(self, src, dst):
		'Built in copytree fails if dst exists. Workaround'
		for item in os.listdir(src):
			s = os.path.join(src, item)
			d = os.path.join(dst, item)
			if os.path.isdir(s):
				if not os.path.exists(d):
					os.makedirs(d)
				self.copyTree(s, d)
			else:
				shutil.copy2(s,d)

	def doUpdate(self):
		'Perform the update.'
		dprint('Updater', 0, "Starting Update")
		self.extractTarball()
		dprint('Updater', 0, "Installing Update")
		self.copyTree(self.updateBase, self.baseInstall) #copy all files
		dprint('Updater', 0, "Cleaning up Install")
		shutil.rmtree(self.updateBase)
		os.remove(self.updateFile)  #remove update file after extraction
		#Write new cfg file
		self.updateType = self.updateRequested
		self.version = self.newestVersion
		self.published = self.newestPublished
		#restart PlexConnect
		#print "Restart PlexConnect to enjoy the update"


	def printSelf(self):
		print "Newest Version: ", self.newestVersion
		print "Published: ", self.newestPublished
		print "Name: ", self.newestName
		print "Impovements: ", self.newestBody
		print "Update URL: ", self.newestTarballURL
		print "Type: ", self.newestTarget_Commitish

	def upgrade(self):
		'Main Updater Function. Call this to do upgrade'
		if self.gitInstalled:
			self.gitUpdate()
		else:
			if self.updateRequested == "dev":
				self.getLatestCommit()
			elif self.updateRequested == "release":
				self.getNewestRelease()
			else:
				self.newestPublished = None
				print "Invalid Update Type. Aborting"

			if self.isUpdateRequired() or self.updateRequested != self.updateType:
				#dprint('Updater', 0, "Update Required")
				self.getUpdate()
				if self.status is "Success":
					self.doUpdate()
					self.writeLog()
					dprint('Updater', 0, 'Update Complete')
			else:
				dprint('Updater', 0, "No Update Required")

	def gitUpdate(self):
		'This update uses git if installed'
		dprint('Updater', 0, 'Using git update')
		if os.path.isdir('.git'):
			process = subprocess.Popen(["git", "pull"])
			output = process.communicate()[0]
		else:
			dprint('Updater', 0, 'Updater has never been run. Setting things up..')
			process = subprocess.Popen(["git", "clone", "https://github.com/iBaa/PlexConnect.git"])
			output = process.communicate()[0]
			self.copyTree("./PlexConnect/.git", "./.git")
			shutil.rmtree("./PlexConnect")


		dprint('Updater', 0, 'Git Update Complete')



def update(UpdateType):
	update = updater(UpdateType)
	update.upgrade()

if __name__ == '__main__':
	#update = updater("dev")
	update("dev")
	#update.upgrade()


