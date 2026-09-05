# -*- coding: utf-8 -*-
# MattStream2014 https://github.com/Kodi-MattStream2014/MattRixx2014-Kodi-addons

import xbmcplugin
import xbmc

from resources.lib.comaddon import addon, dialog, isKrypton, VSlog, addonManager
from resources.lib.db import cDb
from resources.lib.gui.gui import cGui
from resources.lib.handler.inputParameterHandler import cInputParameterHandler
from resources.lib.handler.pluginHandler import cPluginHandler
from resources.lib.upnext import UpNext
from resources.lib.util import cUtil, Unquote, urlHostName

from os.path import splitext


class cPlayer(xbmc.Player):

    ADDON = addon()

    def __init__(self, *args):

        sPlayerType = self.__getPlayerType()
        xbmc.Player.__init__(self, sPlayerType)

        self.Subtitles_file = []
        self.SubtitleActive = False

        oInputParameterHandler = cInputParameterHandler()
        self.sHosterIdentifier = oInputParameterHandler.getValue('sHosterIdentifier')
        self.sTitle = oInputParameterHandler.getValue('sFileName')
        if self.sTitle:
            self.sTitle = Unquote(self.sTitle)
        self.sCat = oInputParameterHandler.getValue('sCat')
        self.sSaison = oInputParameterHandler.getValue('sSeason')
        self.sEpisode = oInputParameterHandler.getValue('sEpisode')
        self.tvShowTitle = oInputParameterHandler.getValue('tvShowTitle')

        self.sSite = oInputParameterHandler.getValue('siteUrl')
        self.sSource = oInputParameterHandler.getValue('sourceName')
        self.sFav = oInputParameterHandler.getValue('sourceFav')
        self.saisonUrl = oInputParameterHandler.getValue('saisonUrl')
        self.nextSaisonFunc = oInputParameterHandler.getValue('nextSaisonFunc')
        self.movieUrl = oInputParameterHandler.getValue('movieUrl')
        self.movieFunc = oInputParameterHandler.getValue('movieFunc')
        self.sTmdbId = oInputParameterHandler.getValue('sTmdbId')

        self.playBackEventReceived = False
        self.playBackStoppedEventReceived = False
        self.forcestop = False

        VSlog('player initialized')

    def clearPlayList(self):
        oPlaylist = self.__getPlayList()
        oPlaylist.clear()

    def __getPlayList(self):
        return xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

    def addItemToPlaylist(self, oGuiElement):
        oGui = cGui()
        oListItem = oGui.createListItem(oGuiElement)
        self.__addItemToPlaylist(oGuiElement, oListItem)

    def __addItemToPlaylist(self, oGuiElement, oListItem):
        oPlaylist = self.__getPlayList()
        oPlaylist.add(oGuiElement.getMediaUrl(), oListItem)

    def AddSubtitles(self, files):
        if type(files) is list or type(files) is tuple:
            self.Subtitles_file = files
        else:
            self.Subtitles_file.append(files)

    def run(self, oGuiElement, sUrl):

        if self.isPlaying():
            sEpisode = str(oGuiElement.getEpisode())
            if sEpisode:
                numEpisode = int(sEpisode)
                prevEpisode = numEpisode - 1
                sPrevEpisode = '%02d' % prevEpisode
                self._setWatched(sPrevEpisode)
            else:
                self._setWatched()
        self.totalTime = 0
        self.currentTime = 0

        sPluginHandle = cPluginHandler().getPluginHandle()

        oGui = cGui()
        item = oGui._createListItem(oGuiElement)
        item.setPath(oGuiElement.getMediaUrl())

        if self.Subtitles_file:
            try:
                item.setSubtitles(self.Subtitles_file)
                VSlog('Load SubTitle :' + str(self.Subtitles_file))
                self.SubtitleActive = True
            except:
                VSlog("Can't load subtitle:" + str(self.Subtitles_file))

        player_conf = self.ADDON.getSettingString('playerPlay')
        mpd = splitext(urlHostName(sUrl))[-1] in [".mpd", ".m3u8"]
        mpd |= '&ct=6&' in sUrl
        if mpd:
            if isKrypton() == True:
                addonManager().enableAddon('inputstream.adaptive')
                item.setProperty('inputstream', 'inputstream.adaptive')
                if '.m3u8' in sUrl:
                    item.setProperty('inputstream.adaptive.manifest_type', 'hls')
                else:
                    item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                xbmcplugin.setResolvedUrl(sPluginHandle, True, listitem=item)
                VSlog('Player use inputstream addon')
            else:
                dialog().VSerror('Nécessite kodi 17 minimum')
                return
        elif player_conf == '0':
            self.play(sUrl, item)
            VSlog('Player use Play() method')
        elif player_conf == 'neverused':
            xbmc.executebuiltin('PlayMedia(' + sUrl + ')')
            VSlog('Player use PlayMedia() method')
        else:
            xbmcplugin.setResolvedUrl(sPluginHandle, True, item)
            VSlog('Player use setResolvedUrl() method')

        for _ in range(20):
            if self.playBackEventReceived:
                break
            xbmc.sleep(1000)

        if self.getAvailableSubtitleStreams():
            if self.ADDON.getSettingString('srt-view') == 'true':
                self.showSubtitles(True)
            else:
                self.showSubtitles(False)
                dialog().VSinfo('Des sous-titres sont disponibles', 'Sous-titres', 4)

        waitingNext = 0

        while self.isPlaying() and not self.forcestop:
            try:
                self.currentTime = self.getTime()

                waitingNext += 1
                if waitingNext == 10:
                    self.totalTime = self.getTotalTime()
                    self.infotag = self.getVideoInfoTag()
                    UpNext().nextEpisode(oGuiElement)

            except Exception as err:
                VSlog("Exception run: {0}".format(err))

            xbmc.sleep(1000)

        if not self.playBackStoppedEventReceived:
            self.onPlayBackStopped()

        if player_conf == '0':
            r = xbmcplugin.addDirectoryItem(handle=sPluginHandle, url=sUrl, listitem=item, isFolder=False)
            return r

        VSlog('Closing player')
        return True

    def startPlayer(self, window=False):
        oPlayList = self.__getPlayList()
        self.play(oPlayList, windowed=window)

    def onPlayBackEnded(self):
        self.onPlayBackStopped()

    def onPlayBackStopped(self):
        VSlog('player stopped')

        if self.playBackStoppedEventReceived:
            return
        self.playBackStoppedEventReceived = True

        self._setWatched(self.sEpisode)

    def _setWatched(self, sEpisode=''):

        try:
            with cDb() as db:
                if self.isPlaying():
                    self.totalTime = self.getTotalTime()
                    self.currentTime = self.getTime()
                    self.infotag = self.getVideoInfoTag()

                if self.totalTime > 0:
                    pourcent = float('%.2f' % (self.currentTime / self.totalTime))

                    saisonViewing = False

                    if (pourcent > 0.90) or (pourcent == 0.0 and self.currentTime == self.totalTime):

                        sTitleWatched = self.infotag.getOriginalTitle()
                        if sTitleWatched:
                            if sEpisode:
                                sTitle = '%s S%sE%s' % (self.tvShowTitle, self.sSaison, sEpisode)
                            else:
                                sTitle = self.sTitle
                            meta = {}
                            meta['cat'] = self.sCat
                            meta['title'] = sTitle
                            meta['titleWatched'] = sTitleWatched
                            if self.movieUrl and self.movieFunc:
                                meta['siteurl'] = self.movieUrl
                                meta['fav'] = self.movieFunc
                            else:
                                meta['siteurl'] = self.sSite
                                meta['fav'] = self.sFav

                            meta['tmdbId'] = self.sTmdbId
                            meta['site'] = self.sSource

                            if self.sSaison:
                                meta['season'] = self.sSaison
                            meta['saisonUrl'] = self.saisonUrl
                            meta['seasonFunc'] = self.nextSaisonFunc

                            db.insert_watched(meta)
                            db.del_resume(meta)

                            if self.sCat == '1':
                                db.del_viewing(meta)
                            elif self.sCat == '8':
                                saisonViewing = True

                        self.__setWatchlist(sEpisode)

                    elif self.currentTime > 180.0:
                        sTitleWatched = self.infotag.getOriginalTitle()
                        if sTitleWatched:
                            meta = {}
                            meta['title'] = self.sTitle
                            meta['titleWatched'] = sTitleWatched
                            meta['site'] = self.sSite
                            meta['point'] = self.currentTime
                            meta['total'] = self.totalTime
                            matchedrow = db.insert_resume(meta)

                            meta['cat'] = self.sCat
                            meta['site'] = self.sSource
                            meta['sTmdbId'] = self.sTmdbId

                            if self.sCat == '8':
                                saisonViewing = True
                            else:
                                if self.sCat == '5' and self.totalTime < 2700:
                                    pass
                                else:
                                    if self.movieUrl and self.movieFunc:
                                        meta['siteurl'] = self.movieUrl
                                        meta['fav'] = self.movieFunc
                                    else:
                                        meta['siteurl'] = self.sSite
                                        meta['fav'] = self.sFav

                                    db.insert_viewing(meta)

                    if saisonViewing:
                        meta['cat'] = '4'
                        meta['sTmdbId'] = self.sTmdbId
                        tvShowTitleWatched = cUtil().titleWatched(self.tvShowTitle).replace(' ', '')
                        if self.sSaison:
                            meta['season'] = self.sSaison
                            meta['title'] = self.tvShowTitle + " S" + self.sSaison
                            meta['titleWatched'] = tvShowTitleWatched + "_S" + self.sSaison
                        else:
                            meta['title'] = self.tvShowTitle
                            meta['titleWatched'] = tvShowTitleWatched
                        meta['site'] = self.sSource
                        meta['siteurl'] = self.saisonUrl
                        meta['fav'] = self.nextSaisonFunc
                        db.insert_viewing(meta)

        except Exception as err:
            VSlog("ERROR Player_setWatched : {0}".format(err))

    def onAVStarted(self):
        VSlog('player started')

        if self.playBackEventReceived:
            self.forcestop = True
            return

        self.playBackEventReceived = True

        with cDb() as db:
            if self.isPlayingVideo() and self.getTime() < 180:
                self.infotag = self.getVideoInfoTag()
                sTitleWatched = self.infotag.getOriginalTitle()
                if sTitleWatched:
                    meta = {'titleWatched': sTitleWatched}
                    resumePoint, total = db.get_resume(meta)
                    if resumePoint:
                        h = resumePoint//3600
                        ms = resumePoint-h*3600
                        m = ms//60
                        s = ms-m*60
                        ret = dialog().VSselect(['Reprendre depuis %02d:%02d:%02d' %(h, m, s), 'Lire depuis le début'], 'Reprendre la lecture')
                        if ret == 0:
                            self.seekTime(resumePoint)
                        elif ret == 1:
                            self.seekTime(0.0)
                            db.del_resume(meta)

    def __setWatchlist(self, sEpisode=''):
        if self.ADDON.getSettingString('bstoken') == '':
            return
        plugins = __import__('resources.lib.trakt', fromlist=['trakt']).cTrakt()
        function = getattr(plugins, 'getAction')
        function(Action="SetWatched", sEpisode=sEpisode)

    def __getPlayerType(self):
        sPlayerType = self.ADDON.getSettingString('playerType')

        try:
            if sPlayerType == '0':
                VSlog('playertype from config: auto')
                return xbmc.PLAYER_CORE_AUTO

            if sPlayerType == '1':
                VSlog('playertype from config: mplayer')
                return xbmc.PLAYER_CORE_MPLAYER

            if sPlayerType == '2':
                VSlog('playertype from config: dvdplayer')
                return xbmc.PLAYER_CORE_DVDPLAYER
        except:
            return False
