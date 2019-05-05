import re

import uservar
from resources.libs import tools


def check_build(name, ret):
    if not tools.working_url(uservar.BUILDFILE): return False
    link = tools.open_url(uservar.BUILDFILE).replace('\n', '').replace('\r', '').replace('\t', '')\
        .replace('gui=""', 'gui="http://"').replace('theme=""', 'theme="http://"')
    match = re.compile('name="%s".+?ersion="(.+?)".+?rl="(.+?)".+?inor="(.+?)".+?ui="(.+?)".+?odi="(.+?)".+?heme="(.+?)".+?con="(.+?)".+?anart="(.+?)".+?review="(.+?)".+?dult="(.+?)".+?nfo="(.+?)".+?escription="(.+?)"' % name).findall(link)
    if len(match) > 0:
        for version, url, minor, gui, kodi, theme, icon, fanart, preview, adult, info, description in match:
            if ret == 'version':
                return version
            elif ret == 'url':
                return url
            elif ret == 'minor':
                return minor
            elif ret == 'gui':
                return gui
            elif ret == 'kodi':
                return kodi
            elif ret == 'theme':
                return theme
            elif ret == 'icon':
                return icon
            elif ret == 'fanart':
                return fanart
            elif ret == 'preview':
                return preview
            elif ret == 'adult':
                return adult
            elif ret == 'description':
                return description
            elif ret == 'info':
                return info
            elif ret == 'all':
                return name, version, url, minor, gui, kodi, theme, icon, fanart, preview, adult, info, description
    else:
        return False


def check_info(name):
    if not tools.working_url(name):
        return False
    link = tools.open_url(name).replace('\n', '').replace('\r', '').replace('\t', '')
    match = re.compile('.+?ame="(.+?)".+?xtracted="(.+?)".+?ipsize="(.+?)".+?kin="(.+?)".+?reated="(.+?)".+?rograms="(.+?)".+?ideo="(.+?)".+?usic="(.+?)".+?icture="(.+?)".+?epos="(.+?)".+?cripts="(.+?)"').findall(link)
    if len(match) > 0:
        for name, extracted, zipsize, skin, created, programs, video, music, picture, repos, scripts in match:
            return name, extracted, zipsize, skin, created, programs, video, music, picture, repos, scripts
    else:
        return False


def check_theme(name, theme, ret):
    themeurl = check_build(name, 'theme')
    if not tools.working_url(themeurl):
        return False
    link = tools.open_url(themeurl).replace('\n', '').replace('\r', '').replace('\t', '')
    match = re.compile('name="%s".+?rl="(.+?)".+?con="(.+?)".+?anart="(.+?)".+?dult=(.+?).+?escription="(.+?)"' % theme).findall(link)
    if len(match) > 0:
        for url, icon, fanart, adult, description in match:
            if ret == 'url':
                return url
            elif ret == 'icon':
                return icon
            elif ret == 'fanart':
                return fanart
            elif ret == 'adult':
                return adult
            elif ret == 'description':
                return description
            elif ret == 'all':
                return name, theme, url, icon, fanart, adult, description


def check_wizard(ret):
    if not tools.working_url(uservar.WIZARDFILE):
        return False
    link = tools.open_url(uservar.WIZARDFILE).replace('\n', '').replace('\r', '').replace('\t', '')
    match = re.compile('id="{0}".+?ersion="(.+?)".+?ip="(.+?)"'.format(uservar.ADDON_ID)).findall(link)
    if len(match) > 0:
        for version, zip in match:
            if ret == 'version':
                return version
            elif ret == 'zip':
                return zip
            elif ret == 'all':
                return uservar.ADDON_ID, version, zip
    else:
        return False