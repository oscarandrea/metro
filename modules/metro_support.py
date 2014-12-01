#!/usr/bin/python3

import os, sys, subprocess, time, pw, grp

def ismount(path):
	"enhanced to handle bind mounts"
	if os.path.ismount(path):
		return 1
	a=os.popen("mount")
	mylines=a.readlines()
	a.close()
	for line in mylines:
		mysplit=line.split()
		if os.path.normpath(path) == os.path.normpath(mysplit[2]):
			return 1
	return 0

class MetroError(Exception):
	def __init__(self, *args):
		self.args = args
	def __str__(self):
		if len(self.args) == 1:
			return str(self.args[0])
		else:
			return "(no message)"

class CommandRunner(object):

	"CommandRunner is a class that allows commands to run, and messages to be displayed. By default, output will go to a log file. Messages will appear on stdout and in the logs."

	def __init__(self, settings, logging=True):
		self.settings = settings
		self.logging = logging
		if self.logging:
			self.fname = self.settings["path/mirror/target"] + "/log" + self.settings["target"] + ".txt"
			if not os.path.exists(os.path.dirname(self.fname)):
				# create output directory for logs
				self.cmdout = sys.stdout
				self.run(["install", "-o", self.settings["path/mirror/owner"], "-g", self.settings["path/mirror/group"], "-m", self.settings["path/mirror/dirmode"], "-d", os.path.dirname(self.fname)], {})
			self.cmdout = open(self.fname,"rb")
			# set logfile ownership:
			os.chown(self.fname, pwd.getpwuid(self.settings["path/mirror/owner"]), pwd.getgrgid(self.settings["path/mirror/group"]))
			sys.stdout.write("Logging output to %s.\n" % self.fname)

	def mesg(self, msg):
		if self.logging:
			self.cmdout.write(msg + "\n")
		sys.stdout.write(msg + "\n")

	def run(self, cmdargs, env):
		self.mesg("Running command: %s (env %s) " % ( cmdargs,env ))
		try:
			if self.logging:
				cmd = subprocess.Popen(cmdargs, env=env, stdout=self.cmdout, stderr=subprocess.STDOUT)
			else:
				cmd = subprocess.Popen(cmdargs, env=env)
			exitcode = cmd.wait()
		except KeyboardInterrupt:
			cmd.terminate()
			self.mesg("Interrupted via keyboard!")
			return 1
		else:
			if exitcode != 0:
				self.mesg("Command exited with return code %s" % exitcode)
				return exitcode
			return 0

class stampFile(object):

	def __init__(self,path):
		self.path = path

	def getFileContents(self):
		return "replaceme"

	def exists(self):
		return os.path.exists(self.path)

	def get(self):
		if not os.path.exists(self.path):
			return False
		try:
			inf = open(self.path,"r")
		except IOError:
			return False
		data = inf.read()
		inf.close()
		try:
			return int(data) 
		except ValueError:
			return False

	def unlink(self):
		if os.path.exists(self.path):
			os.unlink(self.path)

	def wait(self,seconds):
		elapsed = 0
		while os.path.exists(self.path) and elapsed < seconds:
			sys.stderr.write(".")
			sys.stderr.flush()
			time.sleep(5)
			elapsed += 5
		if os.path.exists(self.path):
			return False
		return True

class lockFile(stampFile):

	"Class to create lock files; used for tracking in-progress metro builds."

	def __init__(self,path):
		stampFile.__init__(self,path)
		self.created = False

	def unlink(self):
		"only unlink if *we* created the file. Otherwise leave alone."
		if self.created and os.path.exists(self.path):
			os.unlink(self.path)

	def create(self):
		if self.exists():
			return False
		try:
			out = open(self.path,"w")
		except IOError:
			return False
		out.write(self.getFileContents())
		out.close()
		self.created = True
		return True

	def exists(self):
		exists = False
		if os.path.exists(self.path):
			exists = True
			mypid = self.get()
			if mypid == False:
				try:
					os.unlink(self.path)
				except FileNotFoundError:
					pass
				return False
			try:
				os.kill(mypid, 0)
			except OSError:
				exists = False
				# stale pid, remove:
				sys.stderr.write("# Removing stale lock file: %s\n" % self.path)
				try:
					os.unlink(self.path)
				except FileNotFoundError:
					pass
		return exists

	def unlink(self):
		if self.created and os.path.exists(self.path):
			os.unlink(self.path)

	def getFileContents(self):
		return(str(os.getpid()))

class countFile(stampFile):

	"Class to record fail count for builds."

	@property
	def count(self):
		try:
			f = open(self.path,"r")
			d = f.readlines()
			return int(d[0])
		except (IOError, ValueError):
			return None

	def increment(self):
		try:
			count = self.count
			if count == None:
				count = 0
			count += 1
			f = open(self.path,"w")
			f.write(str(count))
			f.close()
		except (IOError, ValueError):
			return None

if __name__ == "__main__":
	pass
# vim: ts=4 sw=4 noet
