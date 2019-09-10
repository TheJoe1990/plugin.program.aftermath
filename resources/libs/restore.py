################################################################################
#      Copyright (C) 2015 Surfacingx                                           #
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
import xbmcvfs

import os

try:  # Python 3
    from urllib.parse import quote_plus
    import zipfile
except ImportError:  # Python 2
    from urllib import quote_plus
    from resources.libs import zipfile

from resources.libs.config import CONFIG


def _make_backup_locations():
    try:
        if not os.path.exists(CONFIG.BACKUPLOCATION):
            xbmcvfs.mkdirs(CONFIG.BACKUPLOCATION)
        if not os.path.exists(CONFIG.MYBUILDS):
            xbmcvfs.mkdirs(CONFIG.MYBUILDS)
        if not os.path.exists(CONFIG.USERDATA):
            xbmcvfs.mkdirs(CONFIG.USERDATA)
        if not os.path.exists(CONFIG.ADDON_DATA):
            xbmcvfs.mkdirs(CONFIG.ADDON_DATA)
        if not os.path.exists(CONFIG.PACKAGES):
            xbmcvfs.mkdirs(CONFIG.PACKAGES)
    except Exception as e:
        from resources.libs import gui

        gui.DIALOG.ok(CONFIG.ADDONTITLE,
                      "[COLOR {0}]Error making Back Up directories:[/COLOR]".format(CONFIG.COLOR2),
                      "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, str(e)))
        return


def _local(file, loc):
    display = os.path.split(file)
    filename = display[1]

    try:
        zipfile.ZipFile(file, 'r')
    except:
        from resources.libs import gui

        gui.DP.update(0, '[COLOR {0}]Unable to read zipfile from current location.'.format(CONFIG.COLOR2),
                      'Copying file to packages')
        pack = os.path.join(CONFIG.PACKAGES, filename)
        xbmcvfs.copy(file, pack)
        file = xbmc.translatePath(pack)
        gui.DP.update(0, '', 'Copying file to packages: Complete')
        zipfile.ZipFile(file, 'r')

    _finish(file, loc, filename)


def _external(source, loc):
    from resources.libs import downloader
    from resources.libs import gui

    display = os.path.split(source)
    filename = display[1]

    file = os.path.join(CONFIG.PACKAGES, filename)
    downloader.download(source, file, gui.DP)
    gui.DP.update(0, 'Installing External Backup', '', 'Please Wait')

    _finish(file, loc, filename)


def _finish(file, loc, zname):
    from resources.libs import db
    from resources.libs import extract
    from resources.libs import gui
    from resources.libs import tools

    percent, errors, error = extract.all(file, loc, gui.DP)
    db.fix_metas()
    CONFIG.clear_setting('build')
    gui.DP.close()

    if int(errors) >= 1:
        if gui.DIALOG.yesno(CONFIG.ADDONTITLE,
                            '[COLOR {0}][COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, zname),
                            'Completed: [COLOR {0}]{1}{2}[/COLOR] [Errors:[COLOR {3}]{4}[/COLOR]]'.format(CONFIG.COLOR1,
                                                                                                          percent, '%',
                                                                                                          CONFIG.COLOR1,
                                                                                                          errors),
                            'Would you like to view the errors?[/COLOR]',
                            nolabel='[B][COLOR red]No Thanks[/COLOR][/B]',
                            yeslabel='[B][COLOR springgreen]View Errors[/COLOR][/B]'):
            gui.show_text_box("Viewing Errors", error.replace('\t', ''))
    CONFIG.set_setting('installed', 'true')
    CONFIG.set_setting('extract', str(percent))
    CONFIG.set_setting('errors', str(errors))
    try:
        os.remove(file)
    except:
        pass

    gui.DIALOG.ok(CONFIG.ADDONTITLE,
                  "[COLOR {0}]To save changes you now need to force close Kodi, Press OK to force close Kodi[/COLOR]".format(
                      CONFIG.COLOR2))
    tools.kill_kodi(True)


class Restore:
    def __init__(self):
        _make_backup_locations()

        self.external = False
        self.location = 'Local'

    def _choose(self, loc):
        from resources.libs import gui
        from resources.libs import logging
        from resources.libs import skin

        skin.look_and_feel_data()

        if not self.external:
            file = gui.DIALOG.browse(1,
                                     '[COLOR {0}]Select the backup file you want to restore[/COLOR]'.format(
                                         CONFIG.COLOR2),
                                     'files', '.zip', False, False, CONFIG.MYBUILDS)
            if file == "" or not file.endswith('.zip'):
                logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                                   "[COLOR {0}]Local Restore: Cancelled[/COLOR]".format(CONFIG.COLOR2))
                return

            skin.skin_to_default("Restore")

            gui.DP.create(CONFIG.ADDONTITLE, '[COLOR {0}]Installing Local Backup'.format(CONFIG.COLOR2), '',
                          'Please Wait[/COLOR]')

            _local(file, loc)
        elif self.external:
            from resources.libs import tools

            source = gui.DIALOG.browse(1,
                                       '[COLOR {0}]Select the backup file you want to restore[/COLOR]'.format(
                                           CONFIG.COLOR2),
                                       'files', '.zip', False, False)
            if source == "" or not source.endswith('.zip'):
                logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                                   "[COLOR {0}]External Restore: Cancelled[/COLOR]".format(CONFIG.COLOR2))
                return
            if not source.startswith('http'):
                logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                                   "[COLOR {0}]External Restore: Invalid URL[/COLOR]".format(CONFIG.COLOR2))
                return
            try:
                work = tools.check_url(source)
            except:
                logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                                   "[COLOR {0}]External Restore: Error Valid URL[/COLOR]".format(CONFIG.COLOR2))
                logging.log("Not a working url, if source was local then use local restore option",
                            level=xbmc.LOGNOTICE)
                logging.log("External Source: {0}".format(source), level=xbmc.LOGNOTICE)
                return

            skin.skin_to_default("Restore")

            _external(source, loc)

    def _build(self):
        from resources.libs import gui

        # Should we wipe first?
        wipe = gui.DIALOG.yesno(CONFIG.ADDONTITLE,
                                           "[COLOR {0}]Do you wish to restore your".format(CONFIG.COLOR2),
                                           "Kodi configuration to default settings",
                                           "Before installing the {0} backup?[/COLOR]".format(self.location),
                                           nolabel='[B][COLOR red]No[/COLOR][/B]',
                                           yeslabel='[B][COLOR springgreen]Yes[/COLOR][/B]')
        if wipe:
            from resources.libs import install
            install.wipe()

        self._choose(CONFIG.HOME)

    def _guifix(self):
        self._choose(CONFIG.USERDATA)

    def _theme(self):
        self._choose(CONFIG.USERDATA)

    def _addonpack(self):
        self._choose(CONFIG.USERDATA)

    def _addondata(self):
        self._choose(CONFIG.ADDON_DATA)

    def restore(self, param, external=False):
        self.external = external
        self.location = 'Local' if not external else 'External'

        if param == 'build':
            self._build()
        elif param == 'guifix':
            self._guifix()
        elif param == 'theme':
            self._theme()
        elif param == 'addonpack':
            self._addonpack()
        elif param == 'addondata':
            self._addondata()