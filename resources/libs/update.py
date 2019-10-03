################################################################################
#      Copyright (C) 2019 drinfernoo                                           #
#                                                                              #
#  This Program is free software; you can redistribute it and/or modify        #
#  it under the terms of the GNU General Public License as published by        #
#  the Free Software Foundation; either version 2, or (at your option)         #
#  any later version.                                                          #
#                                                                              #
#  This Program is distributed in the hope that it will be useful,             #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of              #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the                #
#  GNU General Public License for more details.                                #
#                                                                              #
#  You should have received a copy of the GNU General Public License           #
#  along with XBMC; see the file COPYING.  If not, write to                    #
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.       #
#  http://www.gnu.org/copyleft/gpl.html                                        #
################################################################################

import xbmc
import xbmcgui

import os
import re

from resources.libs.config import CONFIG


def force_update(silent=False):
    xbmc.executebuiltin('UpdateAddonRepos()')
    xbmc.executebuiltin('UpdateLocalAddons()')
    if not silent:
        from resources.libs import logging

        logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                           '[COLOR {0}]Forcing Addon Updates[/COLOR]'.format(CONFIG.COLOR2))


def wizard_update(startup=None):
    from resources.libs import check
    from resources.libs import logging
    from resources.libs import tools

    dialog = xbmcgui.Dialog()
    progress_dialog = xbmcgui.DialogProgress()
    
    if tools.check_url(CONFIG.BUILDFILE):
        try:
            wid, ver, zip = check.check_wizard('all')
        except:
            return
        if ver > CONFIG.ADDON_VERSION:
            yes = dialog.yesno(CONFIG.ADDONTITLE,
                                   '[COLOR {0}]There is a new version of the [COLOR {1}]{2}[/COLOR]!'.format(CONFIG.COLOR2, CONFIG.COLOR1, CONFIG.ADDONTITLE),
                                   'Would you like to download [COLOR {0}]v{1}[/COLOR]?[/COLOR]'.format(CONFIG.COLOR1, ver),
                                   nolabel='[B][COLOR red]Remind Me Later[/COLOR][/B]',
                                   yeslabel="[B][COLOR springgreen]Update Wizard[/COLOR][/B]")
            if yes:
                from resources.libs import tools

                logging.log("[Auto Update Wizard] Installing wizard v{0}".format(ver), level=xbmc.LOGNOTICE)
                progress_dialog.create(CONFIG.ADDONTITLE, '[COLOR {0}]Downloading Update...'.format(CONFIG.COLOR2), '',
                              'Please Wait[/COLOR]')
                lib = os.path.join(CONFIG.PACKAGES, '{0}-{1}.zip'.format(CONFIG.ADDON_ID, ver))
                try:
                    os.remove(lib)
                except:
                    pass
                from resources.libs import downloader
                from resources.libs import extract
                downloader.download(zip, lib)
                xbmc.sleep(2000)
                progress_dialog.update(0, "", "Installing {0} update".format(CONFIG.ADDONTITLE))
                percent, errors, error = extract.all(lib, CONFIG.ADDONS, True)
                progress_dialog.close()
                xbmc.sleep(1000)
                force_update()
                xbmc.sleep(1000)
                logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                                   '[COLOR {0}]Add-on updated[/COLOR]'.format(CONFIG.COLOR2))
                logging.log("[Auto Update Wizard] Wizard updated to v{0}".format(ver), level=xbmc.LOGNOTICE)
                tools.remove_file(os.path.join(CONFIG.ADDONDATA, 'settings.xml'))
                gui.show_save_data_settings()
                if startup:
                    xbmc.executebuiltin('RunScript({0}/startup.py)'.format(CONFIG.PLUGIN))
                return
            else:
                logging.log("[Auto Update Wizard] Install New Wizard Ignored: {0}".format(ver), level=xbmc.LOGNOTICE)
        else:
            if not startup:
                logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                                   "[COLOR {0}]No New Version of Wizard[/COLOR]".format(CONFIG.COLOR2))
            logging.log("[Auto Update Wizard] No New Version v{0}".format(ver), level=xbmc.LOGNOTICE)
    else:
        logging.log("[Auto Update Wizard] Url for wizard file not valid: {0}".format(CONFIG.BUILDFILE), level=xbmc.LOGNOTICE)


def addon_updates(do=None):
    setting = '"general.addonupdates"'
    if do == 'set':
        query = '{{"jsonrpc":"2.0", "method":"Settings.GetSettingValue","params":{{"setting":{0}}}, "id":1}}'.format(setting)
        response = xbmc.executeJSONRPC(query)
        match = re.compile('{"value":(.+?)}').findall(response)
        if len(match) > 0:
            default = match[0]
        else:
            default = 0
        CONFIG.set_setting('default.addonupdate', str(default))
        query = '{{"jsonrpc":"2.0", "method":"Settings.SetSettingValue","params":{{"setting":{0},"value":{1}}}, "id":1}}'.format(setting, '2')
        response = xbmc.executeJSONRPC(query)
    elif do == 'reset':
        try:
            value = int(float(CONFIG.get_setting('default.addonupdate')))
        except:
            value = 0
        if value not in [0, 1, 2]:
            value = 0
        query = '{{"jsonrpc":"2.0", "method":"Settings.SetSettingValue","params":{{"setting":{0},"value":{1}}}, "id":1}}'.format(setting, value)
        response = xbmc.executeJSONRPC(query)
