#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  dropgp.py, simple crypting&uploading tool for Dropbox
#  
#  Copyright 2013 Francesco Guarneri <Black_Ram>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#
	
from getpass import getpass
import os
import time
import dropbox
import webbrowser
import pwd
import sys
import gnupg

class dropgp:

	def login(self):
		print 'Welcome to DroPGP.'
		self.app_key = 'g91qfdix2ixp9z6'
		self.app_secret = '4137szk36i2nrhx'
		self.initialize()
		
	def initialize(self):
		self.flow = dropbox.client.DropboxOAuth2FlowNoRedirect(self.app_key, self.app_secret)
		self.authorize_url = self.flow.start()
		
		print '1. Go to: ' + self.authorize_url
		webbrowser.open_new_tab(self.authorize_url)
		print '2. Click "Allow" (you might have to log in first)'
		print '3. Copy the authorization code.'
		code = raw_input("Enter the authorization code here: ").strip()
		
		try:
			self.access_token, self.user_id = self.flow.finish(code)
		except dbrest.ErrorResponse, e:
			print('Error: %s'%(e,))
			time.sleep(0.75)
			self.initialize()
		finally:
			self.client = dropbox.client.DropboxClient(self.access_token)
			self.gpg()


	def gpg(self):
		self.user = pwd.getpwuid(os.getuid())[0]
		choice = raw_input("Generate a new GPG-key before crypting? [Y/N] ")
		self.name_email = raw_input("Insert email: ")
		self.passphrase = getpass("Insert passphrase: ")

		if choice == 'y' or choice == 'Y':
			action = 'rm -rf /home/' + self.user + '/gpghome'
			os.system(action)
			gpg = gnupg.GPG(gnupghome='/home/' + self.user + '/gpghome')
			input_data = gpg.gen_key_input(self.name_email, self.passphrase)
			key = gpg.gen_key(input_data)
			print "\033[31mKEY\033[0m: " + str(key)
			time.sleep(0.75)
			self.path()
		
		elif choice == 'n' or choice == 'N':
			self.path()
	
	
	def path(self):
		self.filepath = os.path.dirname(os.path.abspath(__file__))
		self.filename = raw_input("Insert the name of the file do you want to crypt or decrypt (including extension): ")
		self.crypto_extension = '.gpg'
		self.final_path = self.filepath + '/' + self.filename

		choice = input("Press 1 to crypt files or 2 to decrypt. ")
		if choice == 1:
			self.crypting()
		elif choice == 2:
			self.decrypting()
		else:
			print 'Please insert a correct answer.'
			self.path()

	
	def crypting(self):
		gpg = gnupg.GPG(gnupghome='/home/' + self.user + '/gpghome')
		with open(self.final_path, 'rb') as f:
			status = gpg.encrypt_file(f, recipients=[self.name_email], output=self.filename+self.crypto_extension)

		print '\033[31mOk: \033[0m', status.ok
		print '\033[31mStatus: \033[0m', status.status
		print '\033[31mStderr: \033[0m] ', status.stderr
		self.current_working = os.getcwd()
		self.uploading()

	
	def decrypting(self):
		downloading_path = self.filepath + '/' + self.filename + '.gpg'


		choice = input("Press 1 to decrypt a file from Dropbox. ")
		if choice == 1:
			
			folder = raw_input("Insert the Dropbox account's folder not including the file: ")
			selected_path = folder + '/' + self.filename

			try:
				download, metadata = self.client.get_file_and_metadata(selected_path)
			except dropbox.rest.ErrorResponse:
				print '\033[31mFile has been deleted.\033[0m'
				print ''
				print ''
				time.sleep(2)
				self.path()
			except dropbox.rest.RESTSocketError:
				print '\033[31mSocket error was got while contacting Dropbox.\033[0m'

			current_working = os.getcwd()
			out = open(os.getcwd()+'/'+self.filename,'w')
			out.write(download.read())
			out.close()

			#print metadata


		gpg = gnupg.GPG(gnupghome='/home/' +self.user+ '/gpghome')
		
		with open(os.getcwd()+'/'+self.filename, 'rb') as f:
			string = f.read()
			str_formatted = str(string)
			decrypted_data = gpg.decrypt(str_formatted, passphrase=self.passphrase)
			print 'ok: ', decrypted_data.ok
			print 'status: ', decrypted_data.status
			print 'stderr: ', decrypted_data.stderr

			strd_formatted = str(decrypted_data)
			f.close()
		try:
			f = open(os.getcwd()+'/'+self.filename,'w')
		except IOError:
			print 'Error to open the file. Try again.'
			self.decrypting()
		finally:
			f.write(strd_formatted)
			f.close()
			newfilename = self.filename.replace('.gpg','')
			os.rename(self.filename,newfilename)
			print 'File successfully decrypted.'


	def uploading(self):
		select_path = raw_input("Insert the folder where do you want to upload the file (ex.root): ")
		uploading_path = self.current_working + '/' + self.filename + '.gpg'
		dropbox_path_root = '/' + self.filename + '.gpg'
		selected_path = '/' + select_path + '/' + self.filename + '.gpg'

		f = open(uploading_path)
		if select_path == 'root' or select_path == 'Root' or select_path == 'ROOT':
			try:
				response = self.client.put_file(dropbox_path_root, f)
			except dropbox.rest.ErrorResponse:
				print '\033[31mResponse error.\033[0m'
				print ''
				print ''
				time.sleep(2)
				self.path()
			except dropbox.rest.RESTSocketError:
				print 'Socket error was got while contacting Dropbox.'
		else:
			try:
				response = self.client.put_file(selected_path, f)
			except dropbox.rest.ErrorResponse:
				print '\033[31mError Response.\033[0m'
				print ''
				print ''
				time.sleep(2)
				self.path()
			except dropbox.rest.RESTSocketError:
				print 'Socket error was got while contacting Dropbox.'
		print 'Uploaded!'
		choice = raw_input('Other crypting actions? [Y/N]')
		if choice == 'y' or choice == 'Y':
			self.path()
		elif choice == 'n' or choice == 'N':
			print 'Ok. Bye bye!'
			time.sleep(0.75)
			sys.exit()		 



if __name__ == '__main__':   
	print 'Welcome to DroPGP!'   
	time.sleep(1)
	self = dropgp()
	self.login()
