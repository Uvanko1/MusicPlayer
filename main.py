import sys
import os
import time
import mutagen
import sqlite3

from PyQt5 import QtMultimedia, QtGui
from PyQt5.QtCore import QUrl, Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlaylist
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QStyle, QLineEdit, QMenu, QAction, \
    QAbstractItemView, QPushButton, QDialog
from qt_material import apply_stylesheet

from MusicalPlayer import Ui_MainWindow


class MyWidget(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # Открытие базы данных
        self.con = sqlite3.connect('save_data.db')
        self.cur = self.con.cursor()
        # Сигналы
        self.Na = NewArtist()
        self.Na.login_data[str].connect(self.handle_input)
        # Альбомы, артисты и песни
        self.songs_url = {}
        self.songsUrl = []
        self.albums = []
        self.album = {}
        self.artists = {}
        self.artistsLst = []
        # Плеер и плейлист
        self.player = QtMultimedia.QMediaPlayer()
        self.player.positionChanged.connect(self.time)
        self.player.positionChanged.connect(self.positionChanged)
        self.player.durationChanged.connect(self.durationChanged)
        self.playlist = QtMultimedia.QMediaPlaylist(self.player)
        # Список песен
        self.listSongs.itemClicked.connect(self.selected_song)
        # Проигрыватель
        self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.prev.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.next.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.next.clicked.connect(self.next_song)
        self.prev.clicked.connect(self.prev_song)
        self.play.clicked.connect(self.playing)
        # Удаление альбомов
        self.listAlbums.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listAlbums.customContextMenuRequested.connect(self.AlbumsContext)
        # Время
        self.progress.sliderMoved.connect(self.setPosition)
        self.progress.setFocusPolicy(Qt.NoFocus)
        self.currentTime.setText("0:00")
        self.allTime.setText(time.strftime("%M:%S", time.gmtime(self.player.duration() // 1000)))
        # Громкость
        self.volumeShow.setText("50%")
        self.volume.valueChanged.connect(self.volume_change)
        self.volumeShow.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.volumeShow.setMinimumWidth(30)
        # Исполнители
        self.listArtists.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.listArtists.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listArtists.customContextMenuRequested.connect(self.myListWidgetContext)
        self.artistButton.clicked.connect(self.show_choose)
        artists = self.cur.execute('''SELECT DISTINCT artist FROM artists''').fetchall()
        Artists = []
        for artist in artists:
            Artists.append(artist[0])
        self.listArtists.addItems(Artists)
        self.listAlbums.itemDoubleClicked.connect(self.open_album)
        # Картинки
        pixmap = QPixmap('music1.jpg')
        self.imageLabel.setPixmap(pixmap)
        # Поиск
        self.lineEdit.textChanged.connect(self.search)
        # Загрузка песни
        self.action_2.triggered.connect(self.load_song)
        self.flag = False
        self.row = -1

    def load_song(self):
        self.flag = False
        song = QFileDialog.getOpenFileName(self, 'Выберите песню', '', '*.mp3')[0]
        if self.flag:
            self.listSongs.clear()
        self.listSongs.addItem(song.split('/')[-1])
        self.playlist.addMedia(QMediaContent(QUrl(song)))
        self.player.setPlaylist(self.playlist)
        self.player.playlist().setPlaybackMode(QMediaPlaylist.Loop)
        self.player.setVolume(50)
        self.tabWidget.setCurrentWidget(self.tab_3)
        self.songsUrl.append(song)

    # Выбранный трек в альбоме
    def selected_song(self, item):
        print(item.text())
        self.allTime.setText(time.strftime("%M:%S", time.gmtime(self.player.duration() // 1000)))
        self.playlist.setCurrentIndex(self.listSongs.currentRow())
        self.player.setPosition(0)
        self.player.pause()
        self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        pixmap = QtGui.QPixmap()
        metadata = mutagen.File(self.songsUrl[self.listSongs.currentRow()])
        try:
            for tag in metadata.tags.values():
                if tag.FrameID == 'APIC':
                    pixmap.loadFromData(tag.data)
                    break
            else:
                pixmap = QPixmap('music1.jpg')
                self.imageLabel.setPixmap(pixmap)
            self.imageLabel.setPixmap(pixmap)
        except Exception:
            pass

    # Функция паузы и воспроизведения трека
    def playing(self):
        if self.listSongs:
            if self.player.state() in (0, 2):
                if self.row == 0:
                    self.listSongs.setCurrentRow(0)
                else:
                    self.listSongs.setCurrentRow(self.listSongs.currentRow())
                pixmap = QtGui.QPixmap()
                metadata = mutagen.File(self.songsUrl[self.listSongs.currentRow()])
                try:
                    for tag in metadata.tags.values():
                        if tag.FrameID == 'APIC':
                            pixmap.loadFromData(tag.data)
                            break
                    else:
                        pixmap = QPixmap('music1.jpg')
                        self.imageLabel.setPixmap(pixmap)
                    self.imageLabel.setPixmap(pixmap)
                except Exception:
                    pass
                self.player.play()
                self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            else:
                self.player.pause()
                self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        pass

    # Отображение времени трека
    def time(self):
        for i in range((self.player.duration()) // 1000):
            self.currentTime.setText(time.strftime("%M:%S", time.gmtime(self.player.position() // 1000)))
        if self.player.position() == self.player.duration() - 1:
            self.player.playlist().next()
            if self.row == len(self.listSongs) - 1:
                self.row = 0
            else:
                self.row += 1
            self.listSongs.setCurrentRow(self.row)
            self.listSongs.update()
            pixmap = QtGui.QPixmap()
            metadata = mutagen.File(self.songsUrl[self.listSongs.currentRow()])
            for tag in metadata.tags.values():
                if tag.FrameID == 'APIC':
                    pixmap.loadFromData(tag.data)
                    break
            else:
                pixmap = QPixmap('music1.jpg')
                self.imageLabel.setPixmap(pixmap)
            self.imageLabel.setPixmap(pixmap)
        self.allTime.setText(time.strftime("%M:%S", time.gmtime(self.player.duration() // 1000)))

    # Включение следующего трека
    def next_song(self):
        try:
            if self.listSongs.currentRow() > -1:
                self.player.playlist().next()
            print(self.player.playlist().currentIndex())
            print(len(self.listSongs))
            if self.row == len(self.listSongs) - 1:
                self.row = 0
            else:
                self.row += 1
            print(self.row)
            self.listSongs.setCurrentRow(self.row)
            self.listSongs.update()
            pixmap = QtGui.QPixmap()
            print(self.songsUrl[self.listSongs.currentRow()])
            metadata = mutagen.File(self.songsUrl[self.listSongs.currentRow()])
            for tag in metadata.tags.values():
                if tag.FrameID == 'APIC':
                    pixmap.loadFromData(tag.data)
                    break
            else:
                pixmap = QPixmap('music1.jpg')
                self.imageLabel.setPixmap(pixmap)
            self.imageLabel.setPixmap(pixmap)
        except Exception:
            pass

    # Включение предыдущего трека
    def prev_song(self):
        try:
            self.row = self.listSongs.currentRow()
            self.player.playlist().previous()
            if self.row == 0:
                self.row = len(self.listSongs) - 1
            else:
                self.row -= 1
            self.listSongs.setCurrentRow(self.row)
            self.listSongs.update()
            pixmap = QtGui.QPixmap()
            metadata = mutagen.File(self.songsUrl[self.listSongs.currentRow()])
            for tag in metadata.tags.values():
                if tag.FrameID == 'APIC':
                    pixmap.loadFromData(tag.data)
                    break
            else:
                pixmap = QPixmap('music1.jpg')
                self.imageLabel.setPixmap(pixmap)
            self.imageLabel.setPixmap(pixmap)
        except Exception:
            pass

    # Изменение громкости
    def volume_change(self):
        self.player.setVolume(self.volume.value())
        self.volumeShow.setText(str(self.volume.value()) + '%')

    # Поле для ввода имени исполнителя
    def show_choose(self):
        self.Na.show()

    def handle_input(self, name):
        if name:
            self.listArtists.addItem(name)
            self.artistsLst.append(name)
        else:
            self.statusbar.showMessage('Вы не ввели имя исполнителя')

    # Контекстное меню
    def myListWidgetContext(self, position):
        try:
            self.position = position
            self.artist = self.listArtists.currentItem().text()
            if self.listArtists.itemAt(position):
                popMenu = QMenu()
                creAct = QAction("Добавить альбом", self)
                delAct = QAction("Удалить исполнителя", self)
                renameAct = QAction('Альбомы', self)
                popMenu.addAction(delAct)
                popMenu.addAction(renameAct)
                popMenu.addAction(creAct)
                creAct.triggered.connect(self.CreateNewAlbum)
                renameAct.triggered.connect(self.AllAlbums)
                delAct.triggered.connect(self.DeleteArtist)
                popMenu.exec_(self.listArtists.mapToGlobal(position))
            else:
                pass
        except AttributeError:
            pass

    def AlbumsContext(self, position):
        try:
            self.position = position
            self.album_1 = self.listAlbums.currentItem().text()
            if self.listAlbums.itemAt(position):
                popMenu = QMenu()
                delAct = QAction("Удалить альбом", self)
                popMenu.addAction(delAct)
                delAct.triggered.connect(self.DeleteAlbum)
                popMenu.exec_(self.listAlbums.mapToGlobal(position))
            else:
                pass
        except AttributeError:
            pass

    def DeleteAlbum(self):
        self.cur.execute('''DELETE FROM artists WHERE (artist, album) = (?, ?)''',
                         [self.listArtists.currentItem().text(), self.listAlbums.currentItem().text()])
        self.con.commit()
        self.listAlbums.takeItem(self.listAlbums.currentRow())
        print(self.cur.execute('''SELECT DISTINCT artist FROM artists WHERE artist != ""''').fetchall())

    # Все альбомы исполнителя
    def AllAlbums(self):
        self.listAlbums.clear()
        artist = self.listArtists.currentItem().text()
        albums = self.cur.execute('''SELECT album FROM artists WHERE artist = ?''',
                                  [artist]).fetchall()
        Albums = []
        for name in albums:
            if name[0] not in Albums:
                Albums.append(name[0])
        self.listAlbums.addItems(Albums)
        self.tabWidget.setCurrentWidget(self.tab)

    # Открытие альбома
    def open_album(self):
        self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.flag = True
        songs = []
        self.listSongs.clear()
        pixmap = QPixmap('music1.jpg')
        self.imageLabel.setPixmap(pixmap)
        self.playlist.clear()
        self.songsUrl = []
        filelist = []
        album_path = self.cur.execute('''SELECT album_path FROM artists WHERE album = ?''',
                                      [self.listAlbums.currentItem().text()]).fetchall()[0][0]
        for root, dirs, files in os.walk(album_path):
            for file in files:
                filelist.append(os.path.abspath(os.path.join(root, file)))
        for name in filelist:
            name = os.path.abspath(name)
            print(name.split('\\')[-1])
            self.songsUrl.append(name)
            songs.append(name.split('\\')[-1])
        if self.artist not in self.artists:
            self.albums = []
        self.album[os.path.abspath(filelist[0]).split('\\')[0]] = songs
        self.songs_url[os.path.abspath(filelist[0]).split('\\')[-2]] = self.songsUrl
        self.albums.append(os.path.abspath(filelist[0]).split('\\')[0])
        self.artists[self.artist] = self.albums
        print(self.songs_url)
        for song in self.songs_url[self.listAlbums.currentItem().text()]:
            print(os.path.splitext(song))
            if os.path.splitext(song)[-1] == '.mp3':
                print(song)
                song = song.replace('\\', '/')
                self.playlist.addMedia(QMediaContent(QUrl(song)))
                self.listSongs.addItem(song.split('/')[-1])
        if not len(self.listSongs):
            self.statusbar.showMessage('В папке нет песен')
        self.player.setPlaylist(self.playlist)
        self.player.playlist().setPlaybackMode(QMediaPlaylist.Loop)
        self.player.setVolume(self.volume.value())
        self.tabWidget.setCurrentWidget(self.tab_3)

    # Добавление нового альбома
    def CreateNewAlbum(self):
        try:
            songs = []
            self.songsUrl = []
            self.album1 = QFileDialog.getExistingDirectory(self,
                                                           'Выберите альбом', '.')
            filelist = []
            print(self.album1)
            for root, dirs, files in os.walk(self.album1):
                for file in files:
                    filelist.append(os.path.join(root, file))
            for name in filelist:
                name = os.path.abspath(name)
                print(name.split('\\')[-1])
                self.songsUrl.append(name)
                songs.append(name.split('\\')[-1])
            if self.artist not in self.artists:
                self.albums = []
            self.album[os.path.abspath(filelist[0]).split('\\')[-2]] = songs
            self.songs_url[os.path.abspath(filelist[0]).split('\\')[-2]] = self.songsUrl
            if os.path.abspath(filelist[0]).split('\\')[-2] not in self.albums:
                self.albums.append(os.path.abspath(filelist[0]).split('\\')[-2])
            self.artists[self.artist] = self.albums
            print(self.artists)
            print(self.artist)
            self.cur.execute('''INSERT INTO artists (artist, album, album_path)
                VALUES (?, ?, ?)''', [self.artist, os.path.abspath(filelist[0]).split('\\')[-2], self.album1])
            self.con.commit()
        except IndexError:
            self.statusbar.showMessage('Вы не выбрали папку')

    # Удаление исполнителя
    def DeleteArtist(self):
        self.cur.execute('''DELETE FROM artists WHERE artist = ?''',
                         [self.listArtists.currentItem().text()])
        self.con.commit()
        self.listArtists.takeItem(self.listArtists.currentRow())

    # Изменение текущего времени трека
    def setPosition(self, position):
        self.player.setPosition(position)

    # Изменение положения слайдера времени
    def positionChanged(self, position):
        self.progress.setValue(position)

    # Изменение длительности разных треков
    def durationChanged(self, duration):
        self.progress.setRange(0, duration)

    # Неготовая функция поиска исполнителя
    def search(self):
        self.ok = []
        query = str('{}%'.format(self.lineEdit.text()))
        for i in self.cur.execute('SELECT DISTINCT artist FROM artists WHERE artist LIKE ?', [query]).fetchall():
            self.ok.append(i[0])
        self.listArtists.clear()
        self.listArtists.addItems(self.ok)
        print(self.artistsLst)
        # artists_names = self.cur.execute('''SELECT artist FROM artists WHERE artist LIKE ?''',
        #                                  [self.lineEdit.text()]).fetchall()[0]
        # print(artists_names)
        # self.listArtists.addItems(artists_names)


# Окно ввода исполнителя
class NewArtist(QDialog):
    login_data = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setGeometry(200, 200, 200, 200)
        self.lineEdit_1 = QLineEdit(self)
        self.lineEdit_1.resize(100, 30)
        self.lineEdit_1.move(10, 10)
        self.lineEdit_1.show()
        self.artists = []
        self.button = QPushButton(self)
        self.button.setText('Ok')
        self.button.move(10, 50)
        self.button.show()
        self.button.clicked.connect(self.send_data)

    def send_data(self):
        self.login_data.emit(self.lineEdit_1.text())
        self.artists.append(self.lineEdit_1.text())
        self.lineEdit_1.setText('')
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_stylesheet(app, 'dark_red.xml')
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())
