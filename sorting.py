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
        # read in the file as a dataframe
        fullinfo = (pd.read_csv(path, sep='\t', header=None)

                      # rename columns
                      .rename(columns={0:"start_time",
                                       1:"type",
                                       2:"event"})

                      # drop any participant responses
                      .dropna())

        # get the end time for each screen
        fullinfo['end_time'] = fullinfo['start_time'].shift(-1)

        # get duration for each screen
        fullinfo['duration'] = (pd.to_numeric(fullinfo['end_time']) -
                                pd.to_numeric(fullinfo['start_time']))


        # identify only the events where images occurred
        only_pics = (fullinfo[fullinfo['event'].str.contains("PICTURE")]
                                .reset_index(drop=True)
                                .drop(columns='type')
                                .rename(columns={'event': 'picture'}))

        # leave only picture numbers for picture identification
        only_pics['picture'] = (only_pics['picture'].str.replace('PICTURE: ','')
                                                    .str.replace('.png',''))

        # write the picture dataframe to file
        pic_fileroot = savelogs
        pic_file = savelogs + '/img_times.csv'
        i = 1
        while True:
            if os.path.exists(pic_file):
                pic_file = pic_fileroot + '/img_times_copy_' + str(i) + '.csv'
                i += 1
            else:
                break
        only_pics.to_csv(pic_file, sep=",", index=None, header=True)

        # save image order
        self.imgsorder = [int(x) for x in only_pics.picture.unique() if x != "reset_image"]

        # return the picture dataframe
        return only_pics

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

    filename = simplefilechecker('Gazes_Position_Sectioned', '.csv')
    #writer = pd.ExcelWriter(filename)
    df.to_csv(filename)
    return df


def chunks(l, n):
    
    """Convert a list l into chunks of n size.
    Credit to Ned Batchelder: https://stackoverflow.com/a/312464"""
    
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        
        # Create an index range for l of n items:
        yield l[i:i+n]

def process_surfaces(surface_events_path):
    """Process surface events file from Pupil Player."""

    # read surface events file to dataframe
    surface_info = (pd.read_csv(surface_events_path)
                     .drop(columns='surface_name'))

    # sequence surface names and events
    surface_info['surface_num'] = surface_info.groupby('event_type').cumcount()+1

    # concatenate variables
    surface_info['surface_and_event'] = (surface_info['event_type'] 
                                        + '_' 
                                        + surface_info['surface_num'].map(str))
    
    # get the start time, end time, and duration for each surface event
    surface_info = surface_info.rename(columns={'world_timestamp': 'start_time'})
    surface_info['end_time'] = surface_info['start_time'].shift(-1)
    surface_info['duration'] = (pd.to_numeric(surface_info['end_time']) - 
                                pd.to_numeric(surface_info['start_time']))
    
    # if a frame took less than the appropriate amount of time, try to pair it
    interrupted_frames = surface_info[(surface_info['event_type']=='enter') & 
                                      (surface_info['duration'] < 1.95)]

    # if there aren't any interrupted frames, continue on
    if len(interrupted_frames)==0:
        del interrupted_frames

    # if there are an odd number of interrupted frames, stop
    elif len(interrupted_frames)%2!=0: 
        raise ValueError('An odd number of interrupted frames have been flagged.')

    # if there are an even number of interrupted frames, pair them
    else:
        
        # TODO: Implement check to make sure the 2 observed times add up to ~2 sec
        
        # identify the surface numbers of partial frames and pair them
        partial_frames = interrupted_frames.surface_num.unique()
        identified_pairs = list(chunks(partial_frames, 2))

        # rename pairs in the original df
        for pair in identified_pairs:

            # identify what the value of the first one is
            first_appearance = pair[0]

            # identify what one needs to be replaced
            second_appearance = pair[1]

            # replace the second one
            surface_info['surface_num'][surface_info['surface_num']==second_appearance] = first_appearance

    # return processed dataframe
    return surface_info

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


def pair_logs(processed_surface_df, processed_log_df):
    """Combine the processed surface dataframe from Pupil with the processed 
        log dataframe from PsychoPy to figure out which stimulus was shown 
        at what time."""
    
    # only retain the stimulus logs
    stim_logs_only = (processed_log_df[processed_log_df['picture']!='reset_image']
                      .reset_index(drop=True))
    
    # associate the stimulus and surface numbers
    paired_logs = pd.DataFrame({'surface_num': processed_surface_df['surface_num'].unique(),
                                'stimulus_pic': stim_logs_only['picture'].unique()})
    
    # merge with the surface dataframe
    processed_surface_df = processed_surface_df.merge(paired_logs, on='surface_num')
    
    # return the merged dataframe
    return processed_surface_df
    
    
def associate_gaze_stimulus(gaze_surface_path, paired_log_df):
    """Add the stimulus ID and event (enter/exit) to each line of the gaze activity dataframe."""
    
    # read in the file with gaze surface information
    gaze_surface_df = pd.read_csv(gazesurface_file)
    
    # take only a few columns from the paired_log_df
    limited_paired_logs = paired_log_df[['world_index', 'stimulus_pic', 'surface_and_event']]
    
    # merge the gaze logs and stimulus logs
    gaze_surface_df = (gaze_surface_df
                       
                       # retain all gaze rows
                       .merge(limited_paired_logs,
                             on='world_index', 
                             how='outer')
                                       
                       # fill all NAs with the previous value
                       .fillna(method='ffill'))
    
    # return the newly merged df
    return gaze_surface_df
    
# sort the info file
sort = Sorting(infofile)

# process the surface file
processed_surfaces = process_surfaces(surfaceevents)

# process the logfile
processed_logs = sort.logsort(logfile)

# associate the surface and log stimulus information
paired_logs = pair_logs(processed_surfaces, processed_logs)

# imggaze_chunks = { chunk# : { colname : value } }
# ie { 000 : { 'world_timestamp' : 123123, ....,.. 'y_scaled': 0.99453 }
imggaze_chunks = sort.gazesort(gazesurface_file)  # type: dict
fullinfo = sort.logsort(logfile)  # type:list

gazes = nesteddicts_inlist(imggaze_chunks)
