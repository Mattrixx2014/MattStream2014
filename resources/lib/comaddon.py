# -*- coding: utf-8 -*-
# MattStream2014 https://github.com/Kodi-MattStream2014/MattRixx2014-Kodi-addons

import time
import json
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

"""System d'importation
from resources.lib.comaddon import addon, dialog, VSlog
"""

"""
from resources.lib.comaddon import addon

addons = addon() en haut de page.

utiliser une fonction comaddon ou xbmcaddon
https://codedocs.xyz/xbmc/xbmc/class_x_b_m_c_addon_1_1xbmcaddon_1_1_addon.html

addons.VSlang(30305)
addons.getLocalizedString(30305)
addons.openSettings()

utiliser la fonction avec un autre addon

addons2 = addon('plugin.video.youtube')
addons2.openSettings()
"""

"""
Ne pas utiliser :
class addon(xbmcaddon.Addon):

L'utilisation de subclass peut provoquer des fuites de mémoire, signalé par ce message :

the python script "\plugin.video.MattStream2014\default.py" has left several classes in memory that we couldn't clean up. The classes include: class XBMCAddon::xbmcaddon::Addon

# https://stackoverflow.com/questions/26588266/xbmc-addon-memory-leak
"""
ADDONVS = xbmcaddon.Addon('plugin.video.MattStream2014')  # singleton


# class addon(xbmcaddon.Addon):
class addon:
    def __init__(self, addonId=None):
        self.addonId = addonId

    def openSettings(self):
        return xbmcaddon.Addon(self.addonId).openSettings() if self.addonId else ADDONVS.openSettings()

    def getSetting(self, key):
        return xbmcaddon.Addon(self.addonId).getSetting(key) if self.addonId else ADDONVS.getSetting(key)

    def getSettingString(self, key):
        return xbmcaddon.Addon(self.addonId).getSettingString(key) if self.addonId else ADDONVS.getSettingString(key)

    def setSetting(self, key, value):
        return xbmcaddon.Addon(self.addonId).setSetting(key, value) if self.addonId else ADDONVS.setSetting(key, value)

    def getAddonInfo(self, info):
        return xbmcaddon.Addon(self.addonId).getAddonInfo(info) if self.addonId else ADDONVS.getAddonInfo(info)

    def VSlang(self, lang):
        return VSPath(xbmcaddon.Addon(self.addonId).getLocalizedString(lang)) if self.addonId else VSPath(ADDONVS.getLocalizedString(lang))


"""

from resources.lib.comaddon import dialog

Utilisation :
dialogs = dialog()
dialogs.VSinfo('test')
https://codedocs.xyz/xbmc/xbmc/group__python___dialog.html
"""


class dialog:
    def __init__(self):
        self.DIALOG = xbmcgui.Dialog()

    def VSok(self, desc, title='MattStream2014'):
        return self.DIALOG.ok(title, desc)

    def VSyesno(self, desc, title='MattStream2014'):
        return self.DIALOG.yesno(title, desc)

    def VSselect(self, desc, title='MattStream2014'):
        return self.DIALOG.select(title, desc)

    def numeric(self, dialogType, heading, defaultt):
        return self.DIALOG.numeric(dialogType, heading, defaultt)

    def VSbrowse(self, type, heading, shares):
        return self.DIALOG.browse(type, heading, shares)

    def VSselectqual(self, list_qual, list_url):

        if len(list_url) == 0:
            return ''
        if len(list_url) == 1:
            return list_url[0]

        ret = self.DIALOG.select(addon().VSlang(30448), list_qual)
        if ret > -1:
            return list_url[ret]
        return ''

    def VSinfo(self, desc, title='MattStream2014', iseconds=0, sound=False):
        if (iseconds == 0):
            iseconds = 1000
        else:
            iseconds = iseconds * 1000

        if (addon().getSettingString('Block_Noti_sound') == 'true'):
            sound = True

        return self.DIALOG.notification(str(title), str(desc), xbmcgui.NOTIFICATION_INFO, iseconds, sound)

    def VSerror(self, e):
        return self.DIALOG.notification('MattStream2014', 'Erreur: ' + str(e), xbmcgui.NOTIFICATION_ERROR, 2000), VSlog('Erreur: ' + str(e))

    def VStextView(self, desc, title='MattStream2014'):
        return self.DIALOG.textviewer(title, desc)
