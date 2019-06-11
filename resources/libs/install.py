import xbmc

import glob
import os
import re
import shutil

from resources.libs.config import CONFIG

###########################
#      Fresh Install      #
###########################


def fresh_start(install=None, over=False):
    from resources.libs import db
    from resources.libs import gui
    from resources.libs import logging
    from resources.libs import tools

    if CONFIG.KEEPTRAKT == 'true':
        from resources.libs import traktit

        traktit.auto_update('all')
        CONFIG.set_setting('traktlastsave', str(tools.get_date(days=3)))
    if CONFIG.KEEPDEBRID == 'true':
        from resources.libs import debridit

        debridit.auto_update('all')
        CONFIG.set_setting('debridlastsave', str(tools.get_date(days=3)))
    if CONFIG.KEEPLOGIN == 'true':
        from resources.libs import loginit

        loginit.auto_update('all')
        CONFIG.set_setting('loginlastsave', str(tools.get_date(days=3)))

    if over:
        yes_pressed = 1

    elif install == 'restore':
        yes_pressed = gui.DIALOG.yesno(CONFIG.ADDONTITLE,
                                       "[COLOR {0}]Do you wish to restore your".format(CONFIG.COLOR2),
                                       "Kodi configuration to default settings",
                                       "Before installing the local backup?[/COLOR]",
                                       nolabel='[B][COLOR red]No, Cancel[/COLOR][/B]',
                                       yeslabel='[B][COLOR springgreen]Continue[/COLOR][/B]')
    elif install:
        yes_pressed = gui.DIALOG.yesno(CONFIG.ADDONTITLE, "[COLOR %s]Do you wish to restore your".format(CONFIG.COLOR2),
                                       "Kodi configuration to default settings",
                                       "Before installing [COLOR {0}]{1}[/COLOR]?".format(CONFIG.COLOR1, install),
                                       nolabel='[B][COLOR red]No, Cancel[/COLOR][/B]',
                                       yeslabel='[B][COLOR springgreen]Continue[/COLOR][/B]')
    else:
        yes_pressed = gui.DIALOG.yesno(CONFIG.ADDONTITLE,
                                       "[COLOR {0}]Do you wish to restore your".format(CONFIG.COLOR2),
                                       "Kodi configuration to default settings?[/COLOR]",
                                       nolabel='[B][COLOR red]No, Cancel[/COLOR][/B]',
                                       yeslabel='[B][COLOR springgreen]Continue[/COLOR][/B]')
    if yes_pressed:
        if CONFIG.SKIN not in ['skin.confluence', 'skin.estuary']:
            from resources.libs import skin

            swap = skin.skin_to_default('Fresh Install')
            if not swap:
                logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                                   '[COLOR {0}]Fresh Install: Skin Swap Failed![/COLOR]'.format(CONFIG.COLOR2))
                return False
            xbmc.sleep(1000)

        from resources.libs import update
        update.addon_updates('set')
        xbmcPath = os.path.abspath(CONFIG.HOME)
        gui.DP.create(CONFIG.ADDONTITLE,
                      "[COLOR {0}]Calculating files and folders".format(CONFIG.COLOR2), '', 'Please Wait![/COLOR]')
        total_files = sum([len(files) for r, d, files in os.walk(xbmcPath)])
        del_file = 0
        gui.DP.update(0, "[COLOR {0}]Gathering Excludes list.[/COLOR]".format(CONFIG.COLOR2))
        if CONFIG.KEEPREPOS == 'true':
            repos = glob.glob(os.path.join(CONFIG.ADDONS, 'repo*/'))
            for item in repos:
                repofolder = os.path.split(item[:-1])[1]
                if not repofolder == CONFIG.EXCLUDES:
                    CONFIG.EXCLUDES.append(repofolder)
        if CONFIG.KEEPSUPER == 'true':
            CONFIG.EXCLUDES.append('plugin.program.super.favourites')
        if CONFIG.KEEPWHITELIST == 'true':
            pvr = ''

            from resources.libs import whitelist
            whitelist = whitelist.whitelist('read')
            if len(whitelist) > 0:
                for item in whitelist:
                    try:
                        name, id, fold = item
                    except:
                        pass
                    if fold.startswith('pvr'):
                        pvr = id

                    depends = db.depends_list(fold)
                    for plug in depends:
                        if not plug in CONFIG.EXCLUDES:
                            CONFIG.EXCLUDES.append(plug)
                        depends2 = db.depends_list(plug)
                        for plug2 in depends2:
                            if not plug2 in CONFIG.EXCLUDES:
                                CONFIG.EXCLUDES.append(plug2)
                    if not fold in CONFIG.EXCLUDES:
                        CONFIG.EXCLUDES.append(fold)
                if not pvr == '':
                    CONFIG.set_setting('pvrclient', fold)
        if CONFIG.get_setting('pvrclient') == '':
            for item in CONFIG.EXCLUDES:
                if item.startswith('pvr'):
                    CONFIG.set_setting('pvrclient', item)
        gui.DP.update(0, "[COLOR {0}]Clearing out files and folders:".format(CONFIG.COLOR2))
        latestAddonDB = db.latest_db('Addons')
        for root, dirs, files in os.walk(xbmcPath, topdown=True):
            dirs[:] = [d for d in dirs if d not in CONFIG.EXCLUDES]
            for name in files:
                del_file += 1
                fold = root.replace('/', '\\').split('\\')
                x = len(fold)-1
                if name == 'sources.xml' and fold[-1] == 'userdata' and CONFIG.KEEPSOURCES == 'true':
                    logging.log("Keep sources.xml: {0}".format(os.path.join(root, name)), level=xbmc.LOGNOTICE)
                elif name == 'favourites.xml' and fold[-1] == 'userdata' and CONFIG.KEEPFAVS == 'true':
                    logging.log("Keep favourites.xml: {0}".format(os.path.join(root, name)), level=xbmc.LOGNOTICE)
                elif name == 'profiles.xml' and fold[-1] == 'userdata' and CONFIG.KEEPPROFILES == 'true':
                    logging.log("Keep profiles.xml: {0}".format(os.path.join(root, name)), level=xbmc.LOGNOTICE)
                elif name == 'playercorefactory.xml' and fold[-1] == 'userdata' and CONFIG.KEEPPLAYERCORE == 'true':
                    logging.log("Keep playercorefactory.xml: {0}".format(os.path.join(root, name)), level=xbmc.LOGNOTICE)
                elif name == 'advancedsettings.xml' and fold[-1] == 'userdata' and CONFIG.KEEPADVANCED == 'true':
                    logging.log("Keep advancedsettings.xml: {0}".format(os.path.join(root, name)), level=xbmc.LOGNOTICE)
                elif name in CONFIG.LOGFILES:
                    logging.log("Keep Log File: {0}".format(name), level=xbmc.LOGNOTICE)
                elif name.endswith('.db'):
                    try:
                        if name == latestAddonDB:
                            logging.log("Ignoring {0} on Kodi {1}".format(name, tools.kodi_version()), level=xbmc.LOGNOTICE)
                        else:
                            os.remove(os.path.join(root, name))
                    except Exception as e:
                        if not name.startswith('Textures13'):
                            logging.log('Failed to delete, Purging DB', level=xbmc.LOGNOTICE)
                            logging.log("-> {0}".format(str(e)), level=xbmc.LOGNOTICE)
                            db.purge_db_file(os.path.join(root, name))
                else:
                    gui.DP.update(int(tools.percentage(del_file, total_files)), '',
                                  '[COLOR {0}]File: [/COLOR][COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, name), '')
                    try:
                        os.remove(os.path.join(root,name))
                    except Exception as e:
                        logging.log("Error removing {0}".format(os.path.join(root, name)), level=xbmc.LOGNOTICE)
                        logging.log("-> / {0}".format(str(e)), level=xbmc.LOGNOTICE)
            if gui.DP.iscanceled():
                gui.DP.close()
                logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                                   "[COLOR {0}]Fresh Start Cancelled[/COLOR]".format(CONFIG.COLOR2))
                return False
        for root, dirs, files in os.walk(xbmcPath, topdown=True):
            dirs[:] = [d for d in dirs if d not in CONFIG.EXCLUDES]
            for name in dirs:
                gui.DP.update(100, '',
                              'Cleaning Up Empty Folder: [COLOR {0}]{1}[/COLOR]'.format(CONFIG.COLOR1, name), '')
                if name not in ["Database", "userdata", "temp", "addons", "addon_data"]:
                    shutil.rmtree(os.path.join(root, name), ignore_errors=True, onerror=None)
            if gui.DP.iscanceled():
                gui.DP.close()
                logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                                   "[COLOR {0}]Fresh Start Cancelled[/COLOR]".format(CONFIG.COLOR2))
                return False
        gui.DP.close()
        CONFIG.clear_setting('build')
        if over:
            return True
        elif install == 'restore':
            return True
        elif install:
            from resources.libs import menu

            menu.build_wizard(install, 'normal', over=True)
        else:
            if CONFIG.INSTALLMETHOD == 1:
                todo = 1
            elif CONFIG.INSTALLMETHOD == 2:
                todo = 0
            else:
                todo = gui.DIALOG.yesno(CONFIG.ADDONTITLE,
                                        "[COLOR {0}]Would you like to [COLOR {1}]Force close[/COLOR] Kodi or [COLOR {2}]Reload Profile[/COLOR]?[/COLOR]".format(CONFIG.COLOR2, CONFIG.COLOR1, CONFIG.COLOR1),
                                        yeslabel="[B][COLOR red]Reload Profile[/COLOR][/B]",
                                        nolabel="[B][COLOR springgreen]Force Close[/COLOR][/B]")
            if todo == 1:
                tools.reload_fix('fresh')
            else:
                update.addon_updates('reset');
                tools.kill_kodi(True)
    else:
        if not install == 'restore':
            logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                               '[COLOR {0}]Fresh Install: Cancelled![/COLOR]'.format(CONFIG.COLOR2))
            xbmc.executebuiltin('Container.Refresh()')


def install_addon_pack(name, url):
    from resources.libs import check
    from resources.libs import downloader
    from resources.libs import db
    from resources.libs import extract
    from resources.libs import gui
    from resources.libs import logging

    if not check.check_url(url):
        logging.log_notify("[COLOR {0}]Addon Installer[/COLOR]".format(CONFIG.COLOR1),
                           '[COLOR {0}]{1}:[/COLOR] [COLOR {2}]Invalid Zip Url![/COLOR]'.format(CONFIG.COLOR1, name, CONFIG.COLOR2))
        return
    if not os.path.exists(CONFIG.PACKAGES):
        os.makedirs(CONFIG.PACKAGES)
    gui.DP.create(CONFIG.ADDONTITLE,
                  '[COLOR {0}][B]Downloading:[/B][/COLOR] [COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, name),
                  '', '[COLOR {0}]Please Wait[/COLOR]'.format(CONFIG.COLOR2))
    urlsplits = url.split('/')
    lib = xbmc.makeLegalFilename(os.path.join(CONFIG.PACKAGES, urlsplits[-1]))
    try:
        os.remove(lib)
    except:
        pass
    downloader.download(url, lib, gui.DP)
    title = '[COLOR {0}][B]Installing:[/B][/COLOR] [COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, name)
    gui.DP.update(0, title, '', '[COLOR {0}]Please Wait[/COLOR]'.format(CONFIG.COLOR2))
    percent, errors, error = extract.all(lib, CONFIG.ADDONS, gui.DP, title=title)
    installed = db.grab_addons(lib)
    db.addon_database(installed, 1, True)
    gui.DP.close()
    logging.log_notify("[COLOR {0}]Addon Installer[/COLOR]".format(CONFIG.COLOR1),
                       '[COLOR {0}]{1}: Installed![/COLOR]'.format(CONFIG.COLOR2, name))
    xbmc.executebuiltin('UpdateAddonRepos()')
    xbmc.executebuiltin('UpdateLocalAddons()')
    xbmc.executebuiltin('Container.Refresh()')


def install_skin(name, url):
    from resources.libs import check
    from resources.libs import downloader
    from resources.libs import db
    from resources.libs import extract
    from resources.libs import gui
    from resources.libs import logging
    from resources.libs import skin

    if not check.check_url(url):
        logging.log_notify("[COLOR {0}]Addon Installer[/COLOR]".format(CONFIG.COLOR1),
                           '[COLOR {0}]{1}:[/COLOR] [COLOR {2}]Invalid Zip Url![/COLOR]'.format(CONFIG.COLOR1, name, CONFIG.COLOR2))
        return
    if not os.path.exists(CONFIG.PACKAGES):
        os.makedirs(CONFIG.PACKAGES)
    gui.DP.create(CONFIG.ADDONTITLE,
                  '[COLOR {0}][B]Downloading:[/B][/COLOR] [COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, name),
                  '', '[COLOR {0}]Please Wait[/COLOR]'.format(CONFIG.COLOR2))
    urlsplits = url.split('/')
    lib = xbmc.makeLegalFilename(os.path.join(CONFIG.PACKAGES, urlsplits[-1]))
    try:
        os.remove(lib)
    except:
        pass
    downloader.download(url, lib, gui.DP)
    title = '[COLOR {0}][B]Installing:[/B][/COLOR] [COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, name)
    gui.DP.update(0, title, '', '[COLOR {0}]Please Wait[/COLOR]'.format(CONFIG.COLOR2))
    percent, errors, error = extract.all(lib, CONFIG.HOME, gui.DP, title=title)
    installed = db.grab_addons(lib)
    db.addon_database(installed, 1, True)
    gui.DP.close()
    logging.log_notify("[COLOR {0}]Addon Installer[/COLOR]".format(CONFIG.COLOR1),
                       '[COLOR {0}]{1}: Installed![/COLOR]'.format(CONFIG.COLOR2, name))
    xbmc.executebuiltin('UpdateAddonRepos()')
    xbmc.executebuiltin('UpdateLocalAddons()')
    for item in installed:
        if item.startswith('skin.') and not item == 'skin.shortcuts':
            if not CONFIG.BUILDNAME == '' and CONFIG.DEFAULTIGNORE == 'true':
                CONFIG.set_setting('defaultskinignore', 'true')
            skin.swap_skins(item, 'Skin Installer')
    xbmc.executebuiltin('Container.Refresh()')


def install_addon_from_url(name, url):
    from resources.libs import check
    from resources.libs import downloader
    from resources.libs import db
    from resources.libs import extract
    from resources.libs import gui
    from resources.libs import logging
    from resources.libs import skin

    if not check.check_url(url):
        logging.log_notify("[COLOR {0}]Addon Installer[/COLOR]".format(CONFIG.COLOR1),
                           '[COLOR {0}]{1}:[/COLOR] [COLOR {2}]Invalid Zip Url![/COLOR]'.format(CONFIG.COLOR1, name, CONFIG.COLOR2))
        return
    if not os.path.exists(CONFIG.PACKAGES):
        os.makedirs(CONFIG.PACKAGES)
    gui.DP.create(CONFIG.ADDONTITLE,
                  '[COLOR {0}][B]Downloading:[/B][/COLOR] [COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, name),
                  '', '[COLOR {0}]Please Wait[/COLOR]'.format(CONFIG.COLOR2))
    urlsplits = url.split('/')
    lib = os.path.join(CONFIG.PACKAGES, urlsplits[-1])
    try:
        os.remove(lib)
    except:
        pass
    downloader.download(url, lib, gui.DP)
    title = '[COLOR {0}][B]Installing:[/B][/COLOR] [COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, name)
    gui.DP.update(0, title, '', '[COLOR {0}]Please Wait[/COLOR]'.format(CONFIG.COLOR2))
    percent, errors, error = extract.all(lib, CONFIG.ADDONS, gui.DP, title=title)
    gui.DP.update(0, title, '', '[COLOR {0}]Installing Dependencies[/COLOR]'.format(CONFIG.COLOR2))
    installed(name)
    installlist = db.grab_addons(lib)
    logging.log(str(installlist))
    db.addon_database(installlist, 1, True)
    install_dependency(name, gui.DP)
    gui.DP.close()

    xbmc.executebuiltin('UpdateAddonRepos()')
    xbmc.executebuiltin('UpdateLocalAddons()')
    xbmc.executebuiltin('Container.Refresh()')

    for item in installlist:
        if item.startswith('skin.') and not item == 'skin.shortcuts':
            if not CONFIG.BUILDNAME == '' and CONFIG.DEFAULTIGNORE == 'true':
                CONFIG.set_setting('defaultskinignore', 'true')
            skin.swap_skins(item, 'Skin Installer')


def install_addon(plugin, url):
    from resources.libs import logging

    if not CONFIG.ADDONFILE == 'http://':
        from resources.libs import check
        from resources.libs import clear
        from resources.libs import downloader
        from resources.libs import db
        from resources.libs import extract
        from resources.libs import gui
        from resources.libs import skin
        from resources.libs import tools

        if url is None:
            url = CONFIG.ADDONFILE
        if check.check_url(url):
            link = clear.text_cache(url).replace('\n', '').replace('\r', '').replace('\t', '').replace('repository=""', 'repository="none"').replace('repositoryurl=""', 'repositoryurl="http://"').replace('repositoryxml=""', 'repositoryxml="http://"')
            match = re.compile('name="(.+?)".+?lugin="%s".+?rl="(.+?)".+?epository="(.+?)".+?epositoryxml="(.+?)".+?epositoryurl="(.+?)".+?con="(.+?)".+?anart="(.+?)".+?dult="(.+?)".+?escription="(.+?)"' % plugin).findall(link)
            if len(match) > 0:
                for name, url, repository, repositoryxml, repositoryurl, icon, fanart, adult, description in match:
                    if os.path.exists(os.path.join(CONFIG.ADDONS, plugin)):
                        do = ['Launch Addon', 'Remove Addon']
                        selected = gui.DIALOG.select("[COLOR {0}]Addon already installed what would you like to do?[/COLOR]".format(CONFIG.COLOR2), do)
                        if selected == 0:
                            xbmc.executebuiltin('RunAddon({0})'.format(plugin))
                            xbmc.sleep(500)
                            return True
                        elif selected == 1:
                            tools.clean_house(os.path.join(CONFIG.ADDONS, plugin))
                            try:
                                tools.remove_folder(os.path.join(CONFIG.ADDONS, plugin))
                            except:
                                pass
                            if gui.DIALOG.yesno(CONFIG.ADDONTITLE,
                                                "[COLOR {0}]Would you like to remove the addon_data for:".format(CONFIG.COLOR2),
                                                "[COLOR {0}]{1}[/COLOR]?[/COLOR]".format(CONFIG.COLOR1, plugin),
                                                yeslabel="[B][COLOR springgreen]Yes Remove[/COLOR][/B]",
                                                nolabel="[B][COLOR red]No Skip[/COLOR][/B]"):
                                clear.remove_addon_data(plugin)
                            xbmc.executebuiltin('Container.Refresh()')
                            return True
                        else:
                            return False
                    repo = os.path.join(CONFIG.ADDONS, repository)
                    if repository.lower() != 'none' and not os.path.exists(repo):
                        logging.log("Repository not installed, installing it")
                        if gui.DIALOG.yesno(CONFIG.ADDONTITLE,
                                            "[COLOR {0}]Would you like to install the repository for [COLOR {1}]{2}[/COLOR]: ".format(CONFIG.COLOR2, CONFIG.COLOR1, plugin),
                                            "[COLOR {0}]{1}[/COLOR]?[/COLOR]".format(CONFIG.COLOR1, repository),
                                            yeslabel="[B][COLOR springgreen]Yes Install[/COLOR][/B]",
                                            nolabel="[B][COLOR red]No Skip[/COLOR][/B]"):
                            ver = tools.parse_dom(tools.open_url(repositoryxml), 'addon', ret='version', attrs={'id': repository})
                            if len(ver) > 0:
                                repozip = '{0}{1}-{2}.zip'.format(repositoryurl, repository, ver[0])
                                logging.log(repozip)
                                db.addon_database(repository, 1)
                                install_addon(repository, repozip)
                                xbmc.executebuiltin('UpdateAddonRepos()')
                                logging.log("Installing Addon from Kodi")
                                install = install_from_kodi(plugin)
                                logging.log("Install from Kodi: {0}".format(install))
                                if install:
                                    xbmc.executebuiltin('Container.Refresh()')
                                    return True
                            else:
                                logging.log("[Addon Installer] Repository not installed: Unable to grab url! ({0})".format(repository))
                        else:
                            logging.log("[Addon Installer] Repository for {0} not installed: {1}".format(plugin, repository))
                    elif repository.lower() == 'none':
                        logging.log("No repository, installing addon")
                        pluginid = plugin
                        zipurl = url
                        install_addon_from_url(plugin, url)
                        xbmc.executebuiltin('Container.Refresh()')
                        return True
                    else:
                        logging.log("Repository installed, installing addon")
                        install = install_from_kodi(plugin, False)
                        if install:
                            xbmc.executebuiltin('Container.Refresh()')
                            return True
                    if os.path.exists(os.path.join(CONFIG.ADDONS, plugin)):
                        return True
                    ver2 = tools.parse_dom(tools.open_url(repositoryxml), 'addon', ret='version', attrs={'id': plugin})
                    if len(ver2) > 0:
                        url = "{0}{1}-{2}.zip".format(url, plugin, ver2[0])
                        logging.log(str(url))
                        db.addon_database(plugin, 1)
                        install_addon_from_url(plugin, url)
                        xbmc.executebuiltin('Container.Refresh()')
                    else:
                        logging.log("no match")
                        return False
            else:
                logging.log("[Addon Installer] Invalid Format")
        else:
            logging.log("[Addon Installer] Text File: {0}".format(CONFIG.ADDONFILE))
    else:
        logging.log("[Addon Installer] Not Enabled.")


def install_from_kodi(plugin, over=True):
    from resources.libs import gui

    if over:
        xbmc.sleep(2000)

    xbmc.executebuiltin('RunPlugin(plugin://{0})'.format(plugin))
    if not gui.while_window('yesnodialog'):
        return False
    xbmc.sleep(500)
    if gui.while_window('okdialog'):
        return False
    gui.while_window('progressdialog')
    if os.path.exists(os.path.join(CONFIG.ADDONS, plugin)):
        return True
    else:
        return False


def install_dependency(name, DP=None):
    from resources.libs import db
    from resources.libs import tools

    dep = os.path.join(CONFIG.ADDONS, name, 'addon.xml')
    if os.path.exists(dep):
        match = tools.parse_dom(tools.read_from_file(dep), 'import', ret='addon')
        for depends in match:
            if 'xbmc.python' not in depends:
                if DP is not None:
                    DP.update(0, '', '[COLOR {0}]{1}[/COLOR]'.format(CONFIG.COLOR1, depends))
                try:
                    add = tools.get_addon_by_id(id=depends)
                    name2 = tools.get_addon_info(add, 'name')
                except:
                    db.create_temp(depends)
                    db.addon_database(depends, 1)


def installed(addon):
    url = os.path.join(CONFIG.ADDONS, addon, 'addon.xml')
    if os.path.exists(url):
        try:
            from resources.libs import logging
            from resources.libs import tools

            name = tools.parse_dom(tools.read_from_file(url), 'addon', ret='name', attrs={'id': addon})
            icon = os.path.join(CONFIG.ADDONS, addon, 'icon.png')  # read from infolabel?
            logging.log_notify('[COLOR {0}]{1}[/COLOR]'.format(CONFIG.COLOR1, name[0]),
                               '[COLOR {0}]Add-on Enabled[/COLOR]'.format(CONFIG.COLOR2), '2000', icon)
        except:
            pass


def install_apk(apk, url):
    from resources.libs import check
    from resources.libs import downloader
    from resources.libs import gui
    from resources.libs import logging
    from resources.libs import tools

    logging.log(apk)
    logging.log(url)
    if tools.platform() == 'android':
        yes = gui.DIALOG.yesno(CONFIG.ADDONTITLE,
                               "[COLOR {0}]Would you like to download and install: ".format(CONFIG.COLOR2),
                               "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, apk),
                               yeslabel="[B][COLOR springgreen]Download[/COLOR][/B]",
                               nolabel="[B][COLOR red]Cancel[/COLOR][/B]")
        if not yes:
            logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                               '[COLOR {0}]ERROR: Install Cancelled[/COLOR]'.format(CONFIG.COLOR2))
            return
        display = apk
        if not os.path.exists(CONFIG.PACKAGES):
            os.makedirs(CONFIG.PACKAGES)
        if not check.check_url(url):
            logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                               '[COLOR {0}]APK Installer: Invalid Apk Url![/COLOR]'.format(CONFIG.COLOR2))
            return
        gui.DP.create(CONFIG.ADDONTITLE,
                      '[COLOR {0}][B]Downloading:[/B][/COLOR] [COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, display),
                      '', 'Please Wait')
        lib = os.path.join(CONFIG.PACKAGES, "{0}.apk".format(apk.replace('\\', '').replace('/', '').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')))
        try:
            os.remove(lib)
        except:
            pass
        downloader.download(url, lib, gui.DP)
        xbmc.sleep(100)
        gui.DP.close()
        gui.show_apk_warning(apk)
        xbmc.executebuiltin('StartAndroidActivity("","android.intent.action.VIEW","application/vnd.android.package-archive","file:{0}")'.format(lib))
    else:
        logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                           '[COLOR {0}]ERROR: None Android Device[/COLOR]'.format(CONFIG.COLOR2))