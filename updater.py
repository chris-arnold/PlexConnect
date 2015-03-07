#!/usr/bin/env python

#Integrated with PlexConnect
#needs to be linked to a button in UI
#Currently a 'lazy' implementation. All we do is DL the new tarball and overwrite
#Ideally, would use a github library and use git clone to update (git clone needs to be run before this will work)

#update to use a pygithub library

import urllib2, json, ConfigParser, os, sys, tarfile, shutil

from Debug import *  # dprint()

import pprint

#sys.path.append( os.path.abspath(os.path.join(".", "PyGithub")))

#from github import Github

class updater():
	def __init__(self, UType):
		dprint('Updater', 0, "Initializing Updater")
		self.updateRequested = UType
		dprint("Updater",0, "Update Type: %s" % self.updateRequested)
		#print "Need to open config file"
		self.owner = "chris-arnold"
		self.repo = "PlexConnect"
		self.version = ""
		self.updateType = ""
		self.published = "" #from changelog/settings
		self.status = ""
		self.updateFile = "update.tar.gz"
		self.changes = ""
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
			dprint ("Updater: ", 0, "No ChangeLog. Running Update Selected")

		self.baseDownloadURL = os.path.join("https://github.com/", self.owner, self.repo, "archive")
		self.baseURL = os.path.join("https://api.github.com/repos", self.owner, self.repo) #/releases/latest"

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
		if self.updateRequested == "dev":
			self.getLatestCommit()
		elif self.updateRequested == "release":
			self.getNewestRelease()
		else:
			self.newestPublished = None
			print "Invalid Update Type. Aborting"

		if self.isUpdateRequired() or self.updateRequested != self.updateType:
			dprint('Updater', 0, "Update Required")
			self.getUpdate()
			if self.status is "Success":
				self.doUpdate()
				self.writeLog()
				dprint('Updater', 0, 'Update Complete')
		else:
			dprint('Updater', 0, "No Update Required")

def update(UpdateType):
	update = updater(UpdateType)
	update.upgrade()

if __name__ == '__main__':
	#update = updater("dev")
	update("dev")
	#update.upgrade()


