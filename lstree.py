import os

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

class LsTree(object):
	def __init__(self):
		# hold the parsed content
		self._str = ''

		# HTML mode(default is turn on)
		self._HTMLMode = True
		self._nl = '<br/>'
		self._space = '&nbsp;'

		# tree component
		self._branch = '|'
		self._linkChar = '-'
		self._linkNum = 4
		self._ramification = None  # generated by _generateComponent(), default is '|----'
		self._fillSpaces = None  # generated by _generateComponent(), default is '&nbsp;'*4
		self._dirMark = 'd'
		self._fileMark = 'f'
		self._markLeftDelimiter = '('
		self._markRightDelimiter = ')'
		self._fileSuffix = None  # file mark, generated by _generateComponent(), default is '(f)'
		self._dirSuffix = None  # directory mark, generated by _generateComponent(), default is '(d)'
		# generate tree component
		self._generateComponent()

		# utils
		self._allowedDelimiter = '''&<[({"''"})]>&'''
		self._entitiesMap = {
			'<': '&lt;',
			'>': '&gt;',
			'&': '&amp;',
			'"': '&quot;',
			"'": '&#039;'
		}

	# generate tree component
	def _generateComponent(self):
		self._ramification = ''.join([self._branch, self._linkNum * self._linkChar])
		self._fillSpaces = self._linkNum * self._space
		self._fileSuffix = ''.join([
			self._markLeftDelimiter,
			self._fileMark,
			self._markRightDelimiter
		])
		self._dirSuffix = ''.join([
			self._markLeftDelimiter,
			self._dirMark,
			self._markRightDelimiter
		])

	# recursively walk through directory
	def _digDirInfo(self, dir):
		info = []
		for item in os.listdir(dir):
			if item == '.' or item == '..':
				continue
			itemPath = os.path.join(dir, item)
			if os.path.isfile(itemPath):
				info.append({
					'name': item
				})
			else:  # is directory
				info.append({
					'name': item,
					'children': self._digDirInfo(itemPath)
				})
		return info

	# parse directory info into tree string
	def _generateTree(self, info, prefix=''):
		content = ''
		for item in info:
			subInfo = item.get('children', None)
			if subInfo is None:
				# file line: prefix + ramification + filename + filesuffix + newline
				#			 |---test.py(f)
				content += ''.join([
					prefix,
					self._ramification,
					item['name'],
					self._fileSuffix,
					self._nl
				])
			else:
				# directory line: prefix + ramification + dirname + dirsuffix + newline
				#			 |---test(d)
				content += ''.join([
					prefix,
					self._ramification,
					item['name'],
					self._dirSuffix,
					self._nl
				])
				if subInfo:
					if item == info[-1]:  # current item no sibling
						new_prefix = ''.join([prefix, self._space, self._fillSpaces])
					else:  # have sibling
						new_prefix = ''.join([prefix, self._branch, self._fillSpaces])
					content += self._generateTree(subInfo, new_prefix)
			if item == info[-1]:
				content += ''.join([prefix, self._nl])
		return content

	# Set tree string as HTML or Text format
	# mode can be 'html', 'HTML', 'text', 'TEXT' and so on
	def setMode(self, mode):
		if not mode:
			return
		mode = mode[0].lower()
		if mode == 'h':
			self._HTMLMode = True
			self._space = '&nbsp;';
			self._nl = '<br/>'
			return True
		if mode == 't':
			self._HTMLMode = False
			self._space = ' '
			self._nl = '\n'
			return True

	# Set tree's component
	def setLinkNum(self, linknum):
		if not linknum:
			return
		linknum = abs(int(linknum))
		if linknum > 1:
			self._linkNum = linknum
			return True

	def setLinkChar(self, linkchar):
		if not linkchar:
			return
		self._linkChar = linkchar[0]
		return True

	def setDirMark(self, mark):
		if not mark:
			return
		self._dirMark = mark
		return True

	def setFileMark(self, mark):
		if not mark:
			return
		self._fileMark = mark

	# just specify left or right delimiter can set all of them
	# the allowed delimiter in self._allowedDelimiter
	def setDelimiterMark(self, delimiter):
		if not delimiter:
			return
		delimiter = delimiter[0]
		allowed = self._allowedDelimiter
		idx = allowed.find(delimiter)
		if idx != -1:
			if self._HTMLMode and delimiter in self._entitiesMap:
				if delimiter == '<' or delimiter == '>':
					self._markLeftDelimiter = '&lt;'
					self._markRightDelimiter = '&gt;'
				else:
					# ' or " or &
					self._markLeftDelimiter = self._entitiesMap[allowed[idx]]
					self._markRightDelimiter = self._markLeftDelimiter
			else:
				self._markLeftDelimiter = allowed[min(idx, len(allowed)-idx-1)]
				self._markRightDelimiter = allowed[max(idx, len(allowed)-idx-1)]
			return True

	def ls(self, dir):
		if not os.path.isdir(dir):
			raise Exception("%s is not a directory" % dir)
		# generate tree's component
		self._generateComponent()
		# the listed root item
		self._str = ''.join([os.path.abspath(dir), self._nl])
		# recursive directory
		info = self._digDirInfo(dir)
		# generate tree string
		self._str += self._generateTree(info)

	def render(self, filename=''):
		if filename and os.path.isfile(filename):
			with open(filename, 'a+') as f:
				f.write(self._str)
		else:
			if self._HTMLMode:
				response_body = '\n'.join([
					'<meta charset="utf-8"/>',
					'<pre class="prettyprint">',
					self._str,
					'</pre>'
				])
			else:
				response_body = self._str

			class MyRequestHandler(BaseHTTPRequestHandler):
				def do_GET(self):
					self.send_response(200)
					self.end_headers()
					self.wfile.write(response_body)
					return
			
			print("Server Listening On localhost:5000")
			server = HTTPServer(('localhost', 5000), MyRequestHandler)
			server.serve_forever()
			


if __name__ == '__main__':
	lt = LsTree()
	lt.ls('.')
	lt.render()