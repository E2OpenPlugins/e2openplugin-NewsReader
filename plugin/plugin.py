# -*- coding: utf-8 -*-
# based on the work from Rico Schulte
# (c) 2006 Rico Schulte
# This Software is Free, use it where you want, when you want for whatever you want and modify it if you want but don't remove my copyright!
#
# Added enigma(1) rssreader compatible feed.xml support
# Overworked for Python3 in 2023 (by Mr.Servo @ OpenA.TV)

from __future__ import print_function

# PYTHON IMPORTS
from html import unescape
from urllib.request import Request, urlopen
from xml.dom.minidom import parse, getDOMImplementation

# ENIGMA IMPORTS
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from Components.MenuList import MenuList
from Components.Input import Input
from Plugins.Plugin import PluginDescriptor

# for localized messages
from . import _

myname = "NewsReader"


def main(session, **kwargs):
	session.open(FeedScreenList)


def autostart(reason, **kwargs):
	pass


def Plugins(**kwargs):
	return PluginDescriptor(name=myname, description="Read RSS feeds", where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main)


class FeedScreenList(Screen):
	skin = """
		<screen position="120,120" size="e-240,e-240" title="%s" >
			<widget name="menu" position="15,15" size="e-30,e-30" font="Regular;33" itemHeight="45" scrollbarMode="showOnDemand" />
		</screen>""" % myname

	def __init__(self, session, args=0):
		self.skin = FeedScreenList.skin
		self.session = session
		Screen.__init__(self, session)
		self.menu = args
		self.config = FeedreaderConfig()
		self["menu"] = MenuList([])
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "MenuActions"],
			{
			"ok": self.go,
			"back": self.close,
			"menu": self.openMainMenu,
			}, -1)
		self.onShown.append(self.getFeedfeedlist)
		self.onClose.append(self.cleanup)

	def cleanup(self):
		if self.config:
			self.config.cleanup()

	def go(self):
		feed = self["menu"].getCurrent()[1]
		if feed:
			self.showFeed(feed)
		else:
			print("[" + myname + "] section in config not found")

	def showFeed(self, feed):
		try:
			self.session.open(FeedScreenContent, feed)
		except IOError as error:  # no messagebox allowed till we've opened our screen
			self.session.open(MessageBox, _("loading feeddata failed!\n\n%s" % error), MessageBox.TYPE_WARNING)
		except Exception:  # no messagebox allowed till we've opened our screen
			print("no feed data")
			self.session.open(MessageBox, _("Beim Anzeigen des Feeds %s ist ein Fehler aufgetreten" % feed.getName()), MessageBox.TYPE_INFO)

	def openMainMenu(self):
		self.session.open(FeedreaderMenuMain, self.config, self["menu"].getCurrent()[1])

	def getFeedfeedlist(self):
		feedlist = []
		for feed in self.config.getFeeds():
			feedlist.append((feed.getName(), feed))
		self["menu"].l.setList(feedlist)


class FeedreaderConfig:

	def __init__(self):
		self.configfile = "/etc/feeds.xml"
		self.node = None
		self.feeds = []
		self.readConfig()

	def cleanup(self):
		if self.node:
			self.node.unlink()
			self.node = None
			self.feeds = []

	def readConfig(self):
		self.cleanup()
		try:
			self.node = parse(self.configfile)
		except Exception:
			print("Illegal xml file")
			print(self.configfile)
			return
		if self.node is not None:
			self.node = self.node.documentElement
			self.getFeeds()

	def writeConfig(self):
		impl = getDOMImplementation()
		if impl is not None:
			newdoc = impl.createDocument(None, "feeds", None)
			for feed in self.feeds:
				node = newdoc.createElement("feed")
				name = newdoc.createElement("name")
				name.appendChild(newdoc.createTextNode(feed.getName()))
				node.appendChild(name)
				url = newdoc.createElement("url")
				url.appendChild(newdoc.createTextNode(feed.getURL()))
				node.appendChild(url)
				if feed.getDescription():
					description = newdoc.createElement("description")
					description.appendChild(newdoc.createTextNode(feed.getDescription()))
					node.appendChild(description)
				newdoc.documentElement.appendChild(node)
			newdoc.writexml(open(self.configfile, "w"))

	def getFeeds(self):
		if self.feeds:
			return self.feeds
		if self.node is not None:
			for node in self.node.getElementsByTagName("feed"):
				name = ''
				description = ''
				url = ''
				nodes = node.getElementsByTagName("name")
				if nodes and nodes[0].childNodes:
					name = str(nodes[0].childNodes[0].data)
				nodes = node.getElementsByTagName("description")
				if nodes and nodes[0].childNodes:
					description = str(nodes[0].childNodes[0].data)
				nodes = node.getElementsByTagName("url")
				if nodes and nodes[0].childNodes:
					url = str(nodes[0].childNodes[0].data)
				self.feeds.append(Feed(name, description, url, True))
		return self.feeds

	def isFeed(self, feedname):
		for feed in self.feeds:
			if feed.getName() == feedname:
				return True
		return False

	def getFeedByName(self, feedname):
		for feed in self.feeds:
			if feed.getName() == feedname:
				return feed
		return None

	def getProxysettings(self):
		if self.node is not None:
			proxynodes = self.node.getElementsByTagName("proxy")
			for node in proxynodes:
				if self.node.getElementsByTagName("useproxy"):
					proxysettings = {}
					httpnodes = node.getElementsByTagName("http")
					if httpnodes and httpnodes[0].childNodes:
						proxysettings['http'] = str(httpnodes[0].childNodes[0].data)
					ftpnodes = node.getElementsByTagName("ftp")
					if ftpnodes and ftpnodes[0].childNodes:
						proxysettings['ftp'] = str(ftpnodes[0].childNodes[0].data)
					return proxysettings
		return None

	def addFeed(self, feed):
		if self.isFeed(feed.getName()):
			return False, _("Feed already exists!")
		feed.setFavorite()
		self.feeds.append(feed)
		self.writeConfig()
		return True, _("Feed added")

	def changeFeed(self, feedold, feednew):
		for index in range(0, len(self.feeds)):
			if self.feeds[index].getName() == feedold.getName():
				self.feeds[index] = feednew
				self.writeConfig()
				return True, _("Feed updated")
		return False, _("Feed not found in config")

	def deleteFeedWithName(self, feedname):
		for index in range(0, len(self.feeds)):
			if self.feeds[index].getName() == feedname:
				self.feeds.pop(index)
				self.writeConfig()
				break


class Feed:
	isfavorite = False

	def __init__(self, name, description, url, isfavorite=False):
		self.name = name
		self.description = description
		self.url = url
		self.isfavorite = isfavorite

	def getName(self):
		return self.name

	def getDescription(self):
		return self.description

	def getURL(self):
		return self.url

	def setName(self, name):
		self.name = name

	def setDescription(self, description):
		self.description = description

	def setURL(self, url):
		self.url = url

	def setFavorite(self):
		self.isfavorite = True

	def getFavorite(self):
		return self.isfavorite


class FeedreaderMenuMain(Screen):
	def __init__(self, session, config, selectedfeed):
		self.config = config
		self.selectedfeed = selectedfeed
		self.skin = """
				<screen position="120,120" size="e-240,e-240" title="Main Menu" >
					<widget name="menu" position="15,15" size="e-30,e-30" font="Regular;33" itemHeight="45" scrollbarMode="showOnDemand" />
				</screen>"""
		self.session = session
		Screen.__init__(self, session)
		feedlist = []
		feedlist.append((_("change feed"), "feed_change"))
		feedlist.append((_("add new feed"), "feed_add"))
		feedlist.append((_("delete feed"), "feed_delete"))
		self["menu"] = MenuList(feedlist)
		self["actions"] = ActionMap(["WizardActions", "DirectionActions"],
										{
										"ok": self.go,
										"back": self.close,
										}, -1)

	def go(self):
		selection = self["menu"].getCurrent()
		if selection is not None:
			cmd = selection[1]
			if cmd == "feed_delete":
				if self.selectedfeed:
					WizzardDeleteFeed(self.session, self, self.config, self.selectedfeed.getName())
			elif cmd == "feed_add":
				WizzardAddFeed(self.session, self.config)
			elif cmd == "feed_change" and self.selectedfeed:
				WizzardAddFeed(self.session, self.config, [self.selectedfeed.getName(), self.selectedfeed.getDescription(), self.selectedfeed.getURL(), True])


class WizzardAddFeed(Screen):
	name = ""
	description = ""
	url = "http://"
	changefeed = False

	def __init__(self, session, config, args=[0, 0, 0, 0]):
		if args != 0:
			self.name = args[0].rstrip()
			self.description = args[1]
			self.url = args[2]
			self.changefeed = args[3]
			self.feedold = Feed(self.name, self.description, self.url)
		self.session = session
		self.config = config
		self.session.openWithCallback(self.name_entered, InputBox, title=_("Please enter a name for the new feed"), text=self.name, maxSize=False, type=Input.TEXT)

	def name_entered(self, feedname):
		if feedname is None:
			self.cancelWizzard()
		else:
			self.name = feedname
			self.session.openWithCallback(self.url_entered, InputBox, title=_("Please enter a url for the new feed"), text=self.url, maxSize=False, type=Input.TEXT)

	def url_entered(self, feedurl):
		if feedurl is None:
			self.cancelWizzard()
		else:
			self.url = feedurl
			self.session.openWithCallback(self.description_entered, InputBox, title=_("Please enter a description for the new feed"), text=self.description, maxSize=False, type=Input.TEXT)

	def description_entered(self, feeddescription):
		if feeddescription is None:
			self.cancelWizzard()
		else:
			self.description = feeddescription
			feednew = Feed(self.name.rstrip(), self.description, self.url)
			if self.changefeed is True:
				result, text = self.config.changeFeed(self.feedold, feednew)
				if result is False:
					self.session.open(MessageBox, _("changing feed failed!\n\n%s" % text), MessageBox.TYPE_WARNING)
			else:
				result, text = self.config.addFeed(feednew)
				if result is False:
					self.session.open(MessageBox, _("adding feed failed!\n\n%s" % text), MessageBox.TYPE_WARNING)

	def cancelWizzard(self):
		self.session.open(MessageBox, _("adding was canceled"), MessageBox.TYPE_WARNING)


class WizzardDeleteFeed(Screen):
	def __init__(self, session, menu, config, feedname):
		self.session = session
		self.config = config
		self.menu = menu
		self.feedname2delete = feedname
		self.session.openWithCallback(self.userIsSure, MessageBox, _("are you sure to delete this feed?\n\n%s" % self.feedname2delete), MessageBox.TYPE_YESNO)

	def userIsSure(self, answer):
		if answer is not None or answer is True:
			self.config.deleteFeedWithName(self.feedname2delete)
			self.menu.close()


class FeedScreenContent(Screen):
	def __init__(self, session, args=None):
		self.feed = args
		if self.feed is None:
			return
		self.skin = """
				<screen position="120,120" size="e-240,e-240" title="%s" >
					<widget name="menu" position="15,15" size="e-30,e-30" font="Regular;33" itemHeight="45" scrollbarMode="showOnDemand" />
				</screen>""" % (self.feed.getName())
		self.session = session
		Screen.__init__(self, session)
		feedlist = []
		self.itemfeedlist = []
		itemnr = 0
		for item in self.getFeedContent(self.feed):
			feedlist.append((item["title"], itemnr))
			self.itemfeedlist.append(item)
			itemnr = itemnr + 1
		self.menu = args
		self["menu"] = MenuList(feedlist)
		self["actions"] = ActionMap(["WizardActions", "DirectionActions"],
										{
										"ok": self.go,
										"back": self.close,
										}, -1)

	def getFeedContent(self, feed):
		print("[" + myname + "] reading feedurl '%s' ..." % (feed.getURL()))
		try:
			self.rss = RSS()
			self.feedc = self.rss.getfeedlist(feed.getURL())
			print("[" + myname + "] have got %i items in newsfeed " % len(self.feedc))
			return self.feedc
		except IOError:
			print("[" + myname + "] IOError by loading the feed! feed adress correct?")
			return []
		except Exception:  # no messagebox allowed till we've opened our screen
			self.session.open(MessageBox, _("loading feeddata failed!"), MessageBox.TYPE_WARNING)
			return []

	def go(self):
		selection = self["menu"].l.getCurrentSelection()
		if selection is not None:
			cmd = selection[1]
			item = self.itemfeedlist[cmd]
			if item["type"].startswith("folder") is True or item["type"].startswith("pubfeed") is True:
				newitem = Feed(item["title"], item["desc"], item["link"])
				self.session.open(FeedScreenContent, newitem)
			else:
				try:
					self.session.open(FeedScreenItemviewer, [self.feed, item])
				except AssertionError:
					self.session.open(MessageBox, _("Error processing feeds"), MessageBox.TYPE_ERROR)


class FeedScreenItemviewer(Screen):
	skin = ""

	def __init__(self, session, args=[0, 0]):
		self.feed = args[0]
		self.item = args[1]
		self.skin = """
				<screen position="120,120" size="e-240,e-240" title="%s" >
					<widget name="text" position="15,15" size="e-30,e-30" font="Regular;33" />
				</screen>""" % self.feed.getName()
		Screen.__init__(self, session)

		self["text"] = ScrollLabel(self.item['title'] + "\n\n" + self.item['desc'] + "\n\n" + self.item['date'] + "\n" + self.item['link'])
		self["actions"] = ActionMap(["WizardActions"],
									{
									"ok": self.close,
									"back": self.close,
									"up": self["text"].pageUp,
									"down": self["text"].pageDown
									}, -1)


class RSS:
	DEFAULT_NAMESPACES = (
						None,  # RSS 0.91, 0.92, 0.93, 0.94, 2.0
						'http://purl.org/rss/1.0/',  # RSS 1.0
						'http://my.netscape.com/rdf/simple/0.9/'  # RSS 0.90
						)
	DUBLIN_CORE = ('http://purl.org/dc/elements/1.1/',)

	def getElementsByTagName(self, node, tagName, possibleNamespaces=DEFAULT_NAMESPACES):
		for namespace in possibleNamespaces:
			children = node.getElementsByTagNameNS(namespace, tagName)
			if len(children):
				return children
		return []

	def node_data(self, node, tagName, possibleNamespaces=DEFAULT_NAMESPACES):
		children = self.getElementsByTagName(node, tagName, possibleNamespaces)
		node = len(children) and children[0] or None
		return node and "".join([child.data for child in node.childNodes]) or None

	def get_txt(self, node, tagName, default_txt=""):
		# Liefert den Inhalt >tagName< des >node< zurueck, ist dieser nicht vorhanden, wird >default_txt< zurueck gegeben.
		return self.node_data(node, tagName) or self.node_data(node, tagName, self.DUBLIN_CORE) or default_txt

	def print_txt(self, node, tagName, print_string):
		# Formatierte Ausgabe
		item_data = self.get_txt(node, tagName)
		if item_data != "":
			print(print_string % {"tag": tagName, "data": item_data})

	def print_rss(self, url):
		configproxies = FeedreaderConfig().getProxysettings()
		req = Request(url)
		req.set_proxy(str(configproxies), 'http')
		rssDocument = parse(urlopen(req)) if configproxies else parse(urlopen(url))
		for node in self.getElementsByTagName(rssDocument, 'item'):
			print('<ul class="RSS">')
			print('<li><h1><a href="%s">' % self.get_txt(node, "link", "#"))
			print(self.get_txt(node, "title", "<no title>"))
			print("</a></h1></li>")
			self.print_txt(node, "date", '<li><small>%(data)s</li>')
			self.print_txt(node, "description", '<li>%(data)s</li>')
			print("</ul>")

	def getfeedlist(self, url):
		# returns the content of the given URL as array
		header = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36", 'referer': 'https://www.google.com/'}
		configproxies = FeedreaderConfig().getProxysettings()
		if configproxies is not None:
			req = Request(url)
			req.set_proxy(str(configproxies), 'http')
			rssDocument = parse(urlopen(req))
		else:
			req = Request(url, headers=header)
			rssDocument = parse(urlopen(req))
		channelname = self.get_txt(rssDocument, "title", "no channelname")
		data = []
		for node in self.getElementsByTagName(rssDocument, 'item'):
			nodex = {}
			nodex['channel'] = channelname
			nodex['type'] = self.get_txt(node, "type", "feed")
			nodex['link'] = self.get_txt(node, "link", "")
			nodex['title'] = unescape(self.get_txt(node, "title", "<no title>"))
			nodex['date'] = self.get_txt(node, "pubDate", self.get_txt(node, "date", ""))
			nodex['desc'] = unescape(self.get_txt(node, "description", ""))
			data.append(nodex)
		return data
