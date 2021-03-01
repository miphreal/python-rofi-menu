import re, configparser, os, sys
from rofi_menu.menu import Menu, NestedMenu, BackItem
from .shell import ShellItem

class DesktopEntry (ShellItem):
	def __init__(self, path, term_exec='rofi-sensible-terminal -e', verbosity=0, use_keywords=True, **kwargs):
		cfgparser = configparser.ConfigParser( interpolation=None)
		cfgparser.read( path)
		if "Desktop Entry" in cfgparser.sections():
			self._path = path
			cf_app = cfgparser['Desktop Entry']
			try:
				self._genname = cf_app.get( 'GenericName', None)
				self._comment = cf_app.get( 'Comment', None)
				self._name = cf_app['Name']
				self._execraw = cf_app['Exec']
				self._exec = re.sub( r'\s+%[a-zA-Z]', "", self._execraw)
				self._terminal =  cf_app.getboolean( "Terminal", False)
				if self._terminal:
					self._exec = f'{term_exec} \'{self._exec}\''
				self._icon = cf_app.get( "Icon", None)
				if self._icon:
					kwargs.update( icon=self._icon)
				self._type = cf_app.get('Type', None)
				if self._type is None or self._type != 'Application':
					raise SyntaxWarning(f'DesktopEntry is not of type Application ({self._type})')
				if "Categories" in cf_app:
					self._categories = [c for c in cf_app["Categories"].split(';') if c and len( c) > 0]
				else:
					self._categories = None
				if "Keywords" in cf_app:
					self._keywords = [c for c in cf_app["Keywords"].split(';') if c and len( c) > 0]
				else:
					self._keywords = None
				title_tmp = [ self._name ]
				if verbosity > 0 and self._genname:
					title_tmp.append( f' <span size=\'smaller\'>({self._genname})</span>')
				if verbosity > 1 and self._comment:
					title_tmp.append( f' <span size=\'smaller\'>[{self._comment}]</span>')
				self._title = "".join( title_tmp)
				self._searchable_text = f'{self._name} {" ".join( self._keywords) if use_keywords and self._keywords else ""}'
				kwargs.update( searchable_text=self._searchable_text)
			except KeyError as ke:
				raise SyntaxWarning( "missing keyword: {}".format( ke))
			super().__init__( text=self._title, command=self._exec, **kwargs)
		else:
			raise SyntaxWarning( "no [Desktop Entry] section in file")
	
	def __repr__( self):
		return f'name: {self._name} genname: {self._genname} execraw: [{self._execraw}] exec: [{self._exec}] icon: {self._icon} categories: {"|".join( self._categories)}'
	
	def __str__( self):
		return self._title

	def clone( self):
		obj = self.__class__( self._path)
		obj.__dict__.update( self.__dict__)
		return obj

def _get_files_dir( paths):
	fpatt = re.compile( r'.*\.desktop$')
	allfiles = []
	for fpath in paths:
		for root, dirs, filenames in os.walk( fpath, followlinks=True):
			for f in filenames:
				if fpatt.match( f):
					allfiles.append( os.path.join(root, f))
	return allfiles

def create_appmenu_flat( paths, prompt=None, verbosity=1, sort=True, **kwargs):
#	sys.stderr.write( f'AppMenu: {len( dfiles)} files\n')
	_items = []
	for f in _get_files_dir( paths):
		_items.append( DesktopEntry( f, verbosity=verbosity, **kwargs))
	items = sorted( _items, key=lambda it: it._name.casefold()) if sort else _items
	return Menu( prompt=prompt, items=items)


def create_appmenu_categories( paths, prompt=None, verbosity=1, sort=True, cat_whitelist = None, include_uncategorized = True, **kwargs):
	_items = []
	for f in _get_files_dir( paths):
		_items.append( DesktopEntry( f, verbosity=verbosity, **kwargs))
	items = sorted( _items, key=lambda it: it._name.casefold()) if sort else _items
	allcats = [ (i, i._categories) for i in items if i._categories]
	allcats_sort = sorted( { item for sublist in allcats if sublist[1] for item in sublist[1]})
	catdict = { cat: [] for cat in allcats_sort if not cat_whitelist or cat in cat_whitelist}
	for k,v in catdict.items():
		for i in allcats:
			if k in i[1]:
				v.append( i[0])
	if include_uncategorized:
		uitems = [ i for i in items if not i._categories]
		if len( uitems) > 0:
			catdict['(Uncategorized)'] = uitems
	menuitems = []
	for k, v in catdict.items():
		menuitems.append( Menu( prompt=k, items=[ BackItem()] + v))
	nested = [ NestedMenu( text=f'{mi.prompt} >', menu=mi) for mi in menuitems]
	return Menu( prompt=prompt, items=nested)
