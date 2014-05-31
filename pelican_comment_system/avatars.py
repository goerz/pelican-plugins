# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

import logging
import os

import hashlib
import urllib.parse
import urllib.request


logger = logging.getLogger(__name__)
_log = "pelican_comment_system: avatars: "
try:
	from . identicon import identicon
	_identiconImported = True
except ImportError as e:
	logger.warning(_log + "identicon deactivated: " + str(e))
	_identiconImported = False

# Global Variables
_identicon_save_path = None
_identicon_output_path = None
_identicon_data = None
_identicon_size = None
_initialized = False
_authors = None
_missingAvatars = []

def _ready():
	if not _initialized:
		logger.warning(_log + "Module not initialized. use init")
	if not _identicon_data:
		logger.debug(_log + "No identicon data set")
	return _identiconImported and _initialized and _identicon_data


def init(pelican_output_path, identicon_output_path, identicon_data, identicon_size, authors):
	global _identicon_save_path
	global _identicon_output_path
	global _identicon_data
	global _identicon_size
	global _initialized
	global _authors
	_identicon_save_path = os.path.join(pelican_output_path, identicon_output_path)
	_identicon_output_path = identicon_output_path
	_identicon_data = identicon_data
	_identicon_size = identicon_size
	_authors = authors
	_initialized = True

def _createIdenticonOutputFolder():
	if not _ready():
		return

	if not os.path.exists(_identicon_save_path):
		os.makedirs(_identicon_save_path)


def getAvatarPath(comment_id, metadata):
	if not _ready():
		return ''

	md5 = hashlib.md5()
	author = tuple()
	for data in _identicon_data:
		if data in metadata:
			string = str(metadata[data])
			md5.update(string.encode('utf-8'))
			author += tuple([string])
		else:
			logger.warning(_log + data + " is missing in comment: " + comment_id)

	if author in _authors:
		return _authors[author]

	global _missingAvatars

	code = md5.hexdigest()

	if not code in _missingAvatars:
		_missingAvatars.append(code)

	return os.path.join(_identicon_output_path, '%s.png' % code)


def get_gravatar_url(md5hex):
	gravatar_url = "http://www.gravatar.com/avatar.php?"
	gravatar_url += urllib.parse.urlencode({
		'gravatar_id':md5hex,
		'd':'identicon', 'size':str(_identicon_size*3)
	})
	# Note: _identicon_size is 1/3 of PELICAN_COMMENT_SYSTEM_IDENTICON_SIZE,
	# hence the factor of 3 to compensate
	return gravatar_url


def generateAndSaveMissingAvatars(use_gravatar=False):
	_createIdenticonOutputFolder()
	for code in _missingAvatars:
		avatar_path = '%s.png' % code
		avatar_save_path = os.path.join(_identicon_save_path, avatar_path)
		if use_gravatar:
			# Assume that code is an MD5-hash of the users email address
			gravatar_url = get_gravatar_url(code)
			if not os.path.isfile(avatar_save_path):
				urllib.request.urlretrieve(gravatar_url, avatar_save_path)
		else:
			avatar = identicon.render_identicon(int(code, 16), _identicon_size)
			avatar.save(avatar_save_path, 'PNG')
