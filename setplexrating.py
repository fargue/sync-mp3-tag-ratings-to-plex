
class Track:
    'Common base class for all tracks'

    trackCount = 0

    def __init__(self, mediaItemId):
        self.rating = -1
        self.mediaItemId = mediaItemId
        self.dbConn = self.dbConnect()
        self.populateTrackFromDb()
        self.readTagData()

        if self.plexRating is None:
            print ("no plex rating, setting to 2")
            self.rating = 2
        else:
            print ("rating is ", self.rating)

        if self.metaDataItemsId is None:
            # if they have no row in metadata_item_settings, insert one
            self.insertMetaDataItemsSettings()

#        if self.plexRating is None:
            # no rating so update value
        self.updateMetaDataItemSettingsRating()

        Track.trackCount += 1
        self.dbConn.commit()
        self.dbConn.close()

    def displayCount(self):
        print ("Total tracks %d" % Track.trackCount)

    def displayTrack(self):
        print ("Track Id : ", self.mediaItemId, ", Rating : ", self.rating, " MetaDataItemsId : ", self.metaDataItemsId, ", filename : ", self.fileName)

    def dbConnect(self):
        import sqlite3
        dbFileName='/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db'
        conn = sqlite3.connect(dbFileName)
        return conn

    def insertMetaDataItemsSettings(self):
        print ("inserting row for guid : ", self.metaDataGuid)
        i1 = '''\
            INSERT INTO metadata_item_settings
                ( account_id, guid, rating )
                VALUES
                ( 1, ?, ? )\
            '''

        c = self.dbConn.cursor()
        c.execute(i1, (self.metaDataGuid,self.rating))

    def readTagData(self):
        import os
        file_extension = os.path.splitext(self.fileName)[1][1:]
        print ("File Extension of ", self.fileName, " is ", file_extension)

        if file_extension == 'ogg':
            self.handleOGG()
        elif file_extension == 'flac':
            self.handleFlac()
        elif file_extension == 'mp3':
            self.handleMP3()
        elif file_extension == 'wma':
            print ("Can't handle wma....yet")
            self.rating = 0
        elif file_extension == 'm4a':
            print ("Can't handle m4a....yet")
            self.rating = 0
        else:
            print ("Invalid file type ", file_extension, " on file ", self.fileName)
            raise SystemExit
        print ("Setting Plex Rating to ", self.rating)
        if self.rating < 0 or self.rating > 10:
            print ("Invalid rating ", self.rating)
            raise SystemExit


    def handleMP3(self):
        from mutagen.mp3 import MP3

        f = MP3(self.fileName)
        self.rating = 0
        for frame in f.tags.getall("TXXX"):
            if frame.HashKey == 'TXXX:FMPS_Rating':
                if frame == '0.1':
                    self.rating = 1
                elif frame == '0.2':
                    self.rating = 2
                elif frame == '0.3':
                    self.rating = 3
                elif frame == '0.4':
                    self.rating = 4
                elif frame == '0.5':
                    self.rating = 5
                elif frame == '0.6':
                    self.rating = 6
                elif frame == '0.7':
                    self.rating = 7
                elif frame == '0.8':
                    self.rating = 8
                elif frame == '0.9':
                    self.rating = 9
                elif frame == '1':
                    self.rating = 10
                return
#        print f.pprint()

    def handleFlac(self):
        from mutagen.flac import FLAC
        f = FLAC(self.fileName)
        for tag in f.tags:
            if tag[0].upper() == 'FMPS_RATING':
                frame = tag[1]
                print ("flac rating is", frame)
                self.rating = float(frame) * 10
                return

    def handleOGG(self):
        from mutagen.oggvorbis import OggVorbis
        f = OggVorbis(self.fileName)
        for tag in f.tags:   # pylint: disable=not-an-iterable
            if tag[0].upper() == 'FMPS_RATING':
                frame = tag[1]
                print ("flac rating is", frame)
                self.rating = float(frame) * 10
                return

    def updateMetaDataItemSettingsRating(self):
        print ("Setting id ", self.metaDataItemsId, " rating to ", self.rating)
        i1 = "UPDATE metadata_item_settings set rating = ? where id = ?"
        c = self.dbConn.cursor()
        c.execute(i1, (self.rating, self.metaDataItemsId))


    def populateTrackFromDb(self):
        q1 = '''\
            SELECT mi.id, mi.library_section_id, mi.section_location_id, mi.metadata_item_id,
                   ls.name,
                   sl.root_path,
                   mp.file,
                   mdi.id, mdi.guid,
                   mis.id, mis.account_id, mis.rating
            FROM media_items mi
            JOIN library_sections ls on mi.library_section_id = ls.id
            JOIN section_locations sl on mi.section_location_id = sl.id
            JOIN media_parts mp on mi.id = mp.media_item_id
            join metadata_items mdi on mi.metadata_item_id = mdi.id
            LEFT OUTER JOIN metadata_item_settings mis on mdi.guid = mis.guid
            where mi.id = ?\
            '''
        c = self.dbConn.cursor()
        c.execute(q1, (self.mediaItemId,))
        r = c.fetchone()
#        print r
        self.librarySectionId = r[1]
        self.sectionLocationId = r[2]
        self.metadataItemId = r[3]
        self.librarySectionName = r[4]
        self.rootPath = r[5]
        self.fileName = r[6]
        self.metaDataId = r[7]
        self.metaDataGuid = r[8]
        self.metaDataItemsId = r[9]
        self.accountId = r[10]
        self.plexRating = r[11]



#t = Track(201734)
import sqlite3
dbFileName='/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db'
conn = sqlite3.connect(dbFileName)
q1 = '''\
    SELECT mi.id
    FROM media_items mi
    WHERE mi.library_section_id = 16
    ORDER BY mi.id desc
    '''
arr = []
c = conn.cursor()
for row in c.execute(q1):
    arr.append(row[0])
c.close()

for plexid in arr:
    t = Track(plexid)
    t.displayTrack()

t.displayCount()
print ("Done....")
