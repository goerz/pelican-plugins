# -*- coding: utf-8 -*-
"""
Pelican Comment System
======================

A Pelican plugin, which allows you to add comments to your articles.

Author: Bernhard Scheirle
"""
from __future__ import unicode_literals
import logging
import os
import copy

logger = logging.getLogger(__name__)

from itertools import chain
from pelican import signals
from pelican.readers import MarkdownReader
from pelican.writers import Writer

from . comment import Comment
from . import avatars


def pelican_initialized(pelican):
	from pelican.settings import DEFAULT_CONFIG
	DEFAULT_CONFIG.setdefault('PELICAN_COMMENT_SYSTEM', False)
	DEFAULT_CONFIG.setdefault('PELICAN_COMMENT_SYSTEM_DIR' 'comments')
	DEFAULT_CONFIG.setdefault('PELICAN_COMMENT_SYSTEM_IDENTICON_OUTPUT_PATH' 'images/identicon')
	DEFAULT_CONFIG.setdefault('PELICAN_COMMENT_SYSTEM_IDENTICON_DATA', ())
	DEFAULT_CONFIG.setdefault('PELICAN_COMMENT_SYSTEM_IDENTICON_SIZE', 72)
	DEFAULT_CONFIG.setdefault('PELICAN_COMMENT_SYSTEM_AUTHORS', {})
	DEFAULT_CONFIG.setdefault('PELICAN_COMMENT_SYSTEM_FEED', os.path.join('feeds', 'comment.%s.atom.xml'))
	DEFAULT_CONFIG.setdefault('COMMENT_URL', '#comment-{path}')
	DEFAULT_CONFIG.setdefault('PELICAN_COMMENT_SYSTEM_USE_GRAVATAR', False)
	if pelican:
		pelican.settings.setdefault('PELICAN_COMMENT_SYSTEM', False)
		pelican.settings.setdefault('PELICAN_COMMENT_SYSTEM_DIR', 'comments')
		pelican.settings.setdefault('PELICAN_COMMENT_SYSTEM_IDENTICON_OUTPUT_PATH', 'images/identicon')
		pelican.settings.setdefault('PELICAN_COMMENT_SYSTEM_IDENTICON_DATA', ())
		pelican.settings.setdefault('PELICAN_COMMENT_SYSTEM_IDENTICON_SIZE', 72)
		pelican.settings.setdefault('PELICAN_COMMENT_SYSTEM_AUTHORS', {})
		pelican.settings.setdefault('PELICAN_COMMENT_SYSTEM_FEED', os.path.join('feeds', 'comment.%s.atom.xml'))
		pelican.settings.setdefault('COMMENT_URL', '#comment-{path}')
		pelican.settings.setdefault('PELICAN_COMMENT_SYSTEM_USE_GRAVATAR', False)


def initialize(article_generator):
	avatars.init(
		article_generator.settings['OUTPUT_PATH'],
		article_generator.settings['PELICAN_COMMENT_SYSTEM_IDENTICON_OUTPUT_PATH'],
		article_generator.settings['PELICAN_COMMENT_SYSTEM_IDENTICON_DATA'],
		article_generator.settings['PELICAN_COMMENT_SYSTEM_IDENTICON_SIZE']/3,
		article_generator.settings['PELICAN_COMMENT_SYSTEM_AUTHORS'],
		)

def add_static_comments(gen, content):
	if gen.settings['PELICAN_COMMENT_SYSTEM'] != True:
		return

	content.comments_count = 0
	content.comments = []

	#Modify the local context, so we get proper values for the feed
	context = copy.copy(gen.context)
	context['SITEURL'] += "/" + content.url
	context['SITENAME'] = "Comments for: " + content.title
	context['SITESUBTITLE'] = ""
	path = gen.settings['PELICAN_COMMENT_SYSTEM_FEED'] % content.slug
	writer = Writer(gen.output_path, settings=gen.settings)

	folder = os.path.join(gen.settings['PELICAN_COMMENT_SYSTEM_DIR'], content.slug)

	if not os.path.isdir(folder):
		logger.debug("No comments found for: " + content.slug)
		writer.write_feed( [], context, path)
		return

	reader = MarkdownReader(gen.settings)
	comments = []
	replies = []

	for file in os.listdir(folder):
		name, extension = os.path.splitext(file)
		if extension[1:].lower() in reader.file_extensions:
			com_content, meta = reader.read(os.path.join(folder, file))
			
			avatar_path = avatars.getAvatarPath(name, meta)

			com = Comment(file, avatar_path, com_content, meta, gen.settings, file, context)

			if 'replyto' in meta:
				replies.append( com )
			else:
				comments.append( com )

	writer.write_feed( comments + replies, context, path)

	#TODO: Fix this O(n²) loop
	for reply in replies:
		for comment in chain(comments, replies):
			if comment.id == reply.metadata['replyto']:
				comment.addReply(reply)

	count = 0
	for comment in comments:
		comment.sortReplies()
		count += comment.countReplies()

	comments = sorted(comments)

	content.comments_count = len(comments) + count
	content.comments = comments

def writeIdenticonsToDisk(gen, writer):
	use_gravatar = gen.settings['PELICAN_COMMENT_SYSTEM_USE_GRAVATAR']
	avatars.generateAndSaveMissingAvatars(use_gravatar)

def register():
	signals.initialized.connect(pelican_initialized)
	signals.article_generator_init.connect(initialize)
	signals.article_generator_write_article.connect(add_static_comments)
	signals.article_writer_finalized.connect(writeIdenticonsToDisk)
