#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Gitlog script
"""

# ########################## Copyrights and license ############################
#                                                                              #
# Copyright 2017-2022 Erik Brozek <erik@brozek.name>                           #
#                                                                              #
# This file is part of CaptainCI.                                              #
# http://www.captainci.com                                                     #
#                                                                              #
# CaptainCI is free software: you can redistribute it and/or modify it under   #
# the terms of the GNU Lesser General Public License as published by the Free  #
# Software Foundation, either version 3 of the License, or (at your option)    #
# any later version.                                                           #
#                                                                              #
# CaptainCI is distributed in the hope that it will be useful, but WITHOUT ANY #
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS    #
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more #
# details.                                                                     #
#                                                                              #
# You should have received a copy of the GNU Lesser General Public License     #
# along with CaptainCI. If not, see <http://www.gnu.org/licenses/>.            #
#                                                                              #
# ##############################################################################

import os
import subprocess

DEBIAN_CHANGELOG = 'debian/changelog'
GIT_CONFIG = '.git/config'

class GitLog:
	"""Gitlog object."""

	def __init__(self):
		"""Init object."""

		# debug
		self.debug_mode = 1

		# commit log format
		self.file_types = ('md', 'jira', 'html', 'txt')

		# package name + version
		self.package = {'name':'unknown', 'version':0, 'fullname':'unknown 0'}
		if os.path.isfile(DEBIAN_CHANGELOG):
			pckgs = self.command(\
				'head -n1 %s | cut -d" " -f1,2 | cut -d")" -f1' % DEBIAN_CHANGELOG).replace('\n', '')
			self.debug('pckgs="%s"' % pckgs)
			self.package = {'name':pckgs.split()[0], 'version':pckgs.split()[1], 'fullname':pckgs}

			if self.package['name'][:2] == "b'":
				self.package['name'] = self.package['name'][2:]

		# version + 1
		try:
			_vers = self.package.get('version', '0.0.0')[1:-1].split('.')
			self.package['version'] = '(%s.%s.%s)' % \
				(int(_vers[0]), int(_vers[1]), int(_vers[2].split('+')[0])+1)
		except BaseException as base_err:
			self.debug('version err="%s"' % base_err)

		self.debug('version="%s"' % self.package['version'])
		self.url = ''



	def command(self, cmd):
		"""Shell command."""

		self.debug('cmd shell: %s' % cmd)
		out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)

		if out:
			out = str(out).replace('\\n', '\n')

		self.debug('cmd out: %s' % out)
		return out


	def debug(self, msg):
		"""Debug message."""

		if self.debug_mode:
			print('[debug] %s' % msg)
			return True

		return False


	def __read(self):
		"""Read config."""
		# pylint: disable=unreachable

		# git config
		if os.path.isfile(GIT_CONFIG):
			return False

		config = open(GIT_CONFIG).read().split('\n')
		sections = {}
		section_name = ''
		for line in config:

			if not line:
				continue

			if line[0] == '[':
				section_name = line.replace(' ', '-').lower()
				sections[section_name] = {}
			continue

			lines = line.replace('\t', '').split('=')
			if len(lines) != 2:
				continue

			sections[section_name][lines[0].strip()] = lines[1].strip()

		self.url = sections['remote-origin']['url']
		urls = self.url.split('@')
		if len(urls) == 2:
			self.url = 'https://%s' % urls[1]
			self.url = self.url.replace('https://github.com:', 'https://github.com/')

		if self.url.endswith('.git'):
			self.url = self.url[:-4]

		return True


	def __history(self):
		"""GIT history."""
		# pylint: disable=too-many-branches
		# pylint: disable=too-many-statements

		# git history
		fwrite = {}
		for file_type in self.file_types:
			fwrite[file_type] = open('.captainci-deb-gitlog.%s' % file_type, 'w')

		send_lines = []
		line_break = 0
		write_no = 0

		outs = self.command('git log --no-decorate --source').split('\ncommit ')
		self.debug('git log len=%s, output=%s' % (len(outs), outs))
		for lines in outs:

			if not lines:
				continue

			if line_break:
				break

			__lines = {\
				'git_commit_hash': '',\
				'arr': lines.split('\n'),\
				'cnt': 0,\
			}
			__lines['cnt'] = len(__lines['arr'])

			if __lines['cnt'] > 0:
				__lines['git_commit_hash'] = __lines['arr'][0].split('\t')[0]

				if __lines['git_commit_hash'].startswith('commit '):
					__lines['git_commit_hash'] = __lines['git_commit_hash'][7:]

			line_no = 0
			for line in __lines['arr']:
				if not line:
					continue

				if line[0] != ' ':
					continue

				line = line.strip()
				if not line:
					continue

				if line.startswith("* commit '"):
					self.debug('commit line=%s' % line)
					continue

				for name_break in (self.package['fullname'],\
					'%s (' % self.package['name'], '%s ' % self.package['name']):

					if line.startswith(name_break):
						line_break = 1
						break

				if line[0] != '*':
					line = '* %s' % line

				if line in send_lines:
					continue

				send_lines.append(line)
				line_no = line_no + 1

				if line_no == 1:
					commit_url = {}
					for file_type in self.file_types:
						commit_url[file_type] = ''

					if self.url != '':
						commit_url['md'] = ' [#%s](%s/commit/%s)' % (\
							__lines['git_commit_hash'], self.url,\
							__lines['git_commit_hash'])
						commit_url['jira'] = ' [#%s|%s/commit/%s]' % (\
							__lines['git_commit_hash'], self.url,\
							__lines['git_commit_hash'])
						commit_url['html'] = ' <a href="%s/commit/%s">#%s</a>' % (\
							self.url, __lines['git_commit_hash'],\
							__lines['git_commit_hash'])
						commit_url['txt'] = ' %s/commit/%s' % (\
							self.url, __lines['git_commit_hash'])


					self.debug('changelog:  %s%s' % (line, commit_url['md']))
					for file_type in self.file_types:
						fwrite[file_type].write('  %s%s\n' % (line, commit_url[file_type]))

				else:
					self.debug('changelog:  %s' % line)
					for file_type in self.file_types:
						fwrite[file_type].write('  %s\n' % line)

			write_no = write_no + 1
			#fwrite.write('  %s\n' % line )

		for file_type in self.file_types:
			fwrite[file_type].close()

		return write_no


	def __write(self, write_no):
		"""Write for all types."""

		for file_type in self.file_types:
			self.__write_type(file_type, write_no)

		return True


	def __write_type(self, file_type, write_no):
		"""Write by type."""

		fwrite = open('.captainci-deb-gitlog-commit.%s' % file_type, 'w')
		#fwrite.write('%s %s\n' % (self.package['name'], self.package['version']))

		if write_no == 0:
			content = '* without changes'
		else:
			content = open('.captainci-deb-gitlog.%s' % file_type, 'r').read()

		if file_type == 'html':
			content = content.replace('*', '<li>').replace('\n', '.')

		fwrite.write('%s' % content)

		fwrite.close()

		return True


	def run(self):
		"""Run script."""

		self.__read()
		write_no = self.__history()
		self.__write(write_no)

		return True


if __name__ == '__main__':

	LOG = GitLog()
	LOG.run()
