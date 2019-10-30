import csv
import gc
import os
from datetime import datetime
import pandas as pd



#-------- FILE PATHS SETUP --------#

# NOTE!! This script should be ideally be placed at the top level of a participant's directory
# That is what tdetermines the "root" filepath!

# After my 2 exams i'll make sure to implement a thing that is more interactive
# or potentially a batch mode? if that's desired.
#-=================================#

root = os.path.dirname(__file__)

savelogs = os.path.join(root, 'savelogs')
if not os.path.exists(savelogs):
    os.makedirs(savelogs)

testdata = os.path.join(root, 'test data', '2019_10_19', '000').replace('\\', '/')
exportfolder = os.path.join(testdata, 'exports', '004').replace('\\', '/')
logfile = os.path.join(root, 'test data', 'sa1_2019-10-19_000-1.log').replace('\\', '/')

exportinfo = os.path.join(exportfolder, 'export_info.csv').replace('\\', '/')
infofile = os.path.join(testdata, 'info.old_style.csv').replace('\\', '/')
# gaze/position file paths
gazesurface_file = os.path.join(exportfolder, 'surfaces', 'gaze_positions_on_surface_Surface 1.csv').replace('\\', '/')
surfaceevents = os.path.join(exportfolder, 'surfaces', 'surface_events.csv').replace('\\', '/')


# Handles the general sorting
class Sorting:
    def __init__(self, expInfo):
        self.offset = self.generateoffset(expInfo)
        self.imgsorder = []
        self.surfaces = []

    # generic file parser
    def sortfiles(self, filepath):
        if not os.path.exists(filepath):
            return None

        info = []
        with open(filepath, "r+") as f:
            reader = csv.reader(f)

            for chunk in reader:
                info.append(chunk)

        return info

    # sorts through surface_events.csv to determine when it enters + exists the video.
    def sortsurfaces(self, surfaceinput):
        # ['world_index', 'world_timestamp', 'surface_name', 'event_type']
        surfaceinfo = self.sortfiles(surfaceinput)  # type:list

        enter = None
        exits = None
        segment = []

        for line in surfaceinfo:
            if "enter" in line:
                enter = line[0:2]  # exclude 'Surface 1' 'enter/exit', we dont need it
            elif "exit" in line[3]:
                exits = line[0:2]

            if enter and exits:
                # record and then reset
                worldtimes = (enter[1], exits[1])
                frames = (enter[0], exits[0])

                segment.append([frames, worldtimes])
                enter = None
                exits = None

        self.surfaces = segment

    # generic sorting through logfile
    def logsort(self, path):
        fullinfo = []

        imgs = []
        pauses = []
        start = 10000000000

        with open(path, "r+") as f:
            for line in f:
                if "PICTURE" in line:
                    split = line.split(' 	DATA 	PICTURE: ')
                    t = float(split[0])
                    pic = split[1][:-1]
                    if 'reset_image' in line:
                        pauses.append(t)
                    else:
                        imgs.append((t, pic))
                elif 'START' in line:
                    start = float(line.split(' ', 1)[0])  # b/c not always @ 0

        if start < imgs[0][0]:
            duration = round(imgs[0][0] - start, 18)
            start = start + self.offset
            end = imgs[0][0] + self.offset
            fullinfo.append([start, end, duration, 'START'])

        for img, pause in zip(imgs, pauses):
            t1 = img[0] + self.offset
            t2 = pause + self.offset
            if pause < t1:
                t2 = t1 + self.offset
                t1 = pause + self.offset
            duration = round(t2 - t1, 12)
            pic = os.path.splitext(img[1])[0]
            info = [t1, t2, duration, pic]
            fullinfo.append(info)

        self.savedata(fullinfo, 'fullinfo', ['Start Time', 'End Time', 'Duration', 'Image Shown'])
        self.imgsorder = imgs

        return fullinfo

    # saves any sort of collection, ie list or array, to a file
    def savedata(self, data, savename, header=None):
        file = self.checkexisting(savename, header)

        with open(file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)

    # to check if file already exists, to prevent overwriting
    # otherwise generates desired file
    def checkexisting(self, filename, header=None, makeCopy=True, extension='.csv'):
        fileroot = os.path.join(savelogs, filename).replace('\\', '/')
        file = fileroot + extension
        if makeCopy:
            i = 1
            while True:
                if os.path.exists(file):
                    file = fileroot + '_copy_' + str(i) + extension
                    i += 1
                else:
                    break

        if not os.path.exists(file):
            if not header:
                # aka no header was actually given
                header = ['']
            with open(file, 'w+', newline='') as f:
                if extension == '.csv':
                    writer = csv.writer(f)
                    writer.writerow(header)
                else:
                    try:
                        f.writelines(header)
                    except:
                        print(Exception)

        return file

    # takes input timestamp in unix format + possibly filepath of info.csv
    # returns time in %H:%M:%S.%f format
    def converttime(self, initaltimestamp):
        timestamp = float(initaltimestamp)
        wall_time = datetime.fromtimestamp(timestamp + self.offset).strftime("%H:%M:%S.%f")

        return wall_time

    # returns calculated offset time as a float
    def generateoffset(self, timesfile):
        if len(timesfile) < 4:
            print("Missing filepath!")
            return None

        systemStart = None
        syncedStart = None

        with open(timesfile, "r+") as f:
            reader = csv.reader(f)

            for row in reader:
                try:
                    if "System" in row[0]:
                        systemStart = float(row[1])
                    elif "Synced" in row[0]:
                        syncedStart = float(row[1])
                except ValueError:
                    return None

                if systemStart and syncedStart:
                    return systemStart - syncedStart

        return None

    # Loads in the gaze positions file and segments them out based on the frame# + times
    # returns dict-like object {index -> {column -> value}}
    #
    def gazesort(self, file):
        if not self.surfaces:
            return None

        # self.sortfiles(file) returns a list of lists, which is then parsed into dataframe
        df = pd.DataFrame.from_records(
            self.sortfiles(file),
            columns=[
                'world_timestamp', 'world_index', 'gaze_timestamp',
                'x_norm', 'y_norm', 'x_scaled', 'y_scaled', 'on_surf', 'confidence'
            ]
        )  # type: pd.DataFrame()
        df = df[1:]  # removes the header (read in above as actual row)

        # collection of each img segment and all its associated details
        chunks = []

        # temp variables
        previous = tuple()
        previous_frames = tuple()

        for surface in self.surfaces:
            enters = surface[0][0]
            exits = surface[0][1]  # search by frames

            index1 = df['world_index'].values.searchsorted(enters, side='left')  # first time it appears
            index2 = df['world_index'].values.searchsorted(exits, side='right')  # last time it appears

            # through obersvations, when it is a new surface, the frame # has a significant jump
            # aka the index is GOOD if index = index + 1 ---> this is only issue for index1/start
            if previous and (index1 == previous[1]) and (int(enters) - previous_frames[0]) > 2:
                index1 = index1 + 1

            chunk = df[index1:index2].to_dict(orient='index')
            chunks.append(chunk)
            previous = (index1, index2)
            previous_frames = (int(enters), int(exits))

        self.savedata(chunks, 'gazes split into sections')

        return chunks


# Consolidates a List of a dict of other dicts, into one dict
# returns a Dataframe from that dict
def nesteddicts_inlist(imggazes):
    data = {  # template for sorting
        'world_timestamp': [],
        'world_index': [],
        'gaze_timestamp': [],
        'x_norm': [],
        'y_norm': [],
        'x_scaled': [],
        'y_scaled': [],
        'on_surf': [],
        'confidence': [],
        'section #': []
    }

    i = 1
    for section in imggazes:  # type: dict
        sect = str(i)
        for row in section:  # type: dict
            rowinfo = section[row]
            for label, val in zip(data, rowinfo):
                data[label].append(rowinfo[val])
            data['section #'].append(str(sect))
        i += 1
    gc.collect()  # just for good measure
    df = pd.DataFrame.from_dict(data)
    df.columns = list(data.keys())

    df["img shown"] = ""

    filename = simplefilechecker('Gazes_Position_Sectioned', '.xlsx')
    writer = pd.ExcelWriter(filename)
    df.to_excel(writer)
    return df


def simplefilechecker(filename, extension):
    fileroot = os.path.join(savelogs, filename).replace('\\', '/')
    file = fileroot + extension

    i = 1
    while True:
        if os.path.exists(file):
            file = fileroot + '_copy_' + str(i) + extension
            i += 1
        else:
            return file


# Need to work on this
def loggaze_matchup(imggazes, infolog):
    gazes = nesteddicts_inlist(imggazes)  # type: pd.DataFrame
    print(len(gazes))
    print(gazes['section #'].nunique())
    gc.collect()  # just for good measure
    gazes["img shown"] = ""


sort = Sorting(infofile)
sort.sortsurfaces(surfaceevents)

# imggaze_chunks = { chunk# : { colname : value } }
# ie { 000 : { 'world_timestamp' : 123123, ....,.. 'y_scaled': 0.99453 }
imggaze_chunks = sort.gazesort(gazesurface_file)  # type: dict
fullinfo = sort.logsort(logfile)  # type:list

gazes = nesteddicts_inlist(imggaze_chunks)
