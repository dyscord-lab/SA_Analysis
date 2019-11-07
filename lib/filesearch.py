import os


def findparticipants(dataroot):

    """Find all participants in the current dataset"""

    # create a container for participants
    included_participants = []

    days = [day for day in os.listdir(dataroot)
            if os.path.isdir(os.path.join(dataroot, day))]

    for day in days:
        dayfolder = os.path.join(dataroot, day)
        participants = [participant for participant in os.listdir(dayfolder)
                        if os.path.isdir(os.path.join(dayfolder, participant))]
        for p in participants:
            participant_root = os.path.join(dayfolder, p)
            included_participants.append(participant_root)

    return included_participants


# uses the export folder with highest number
def findhighest(exportsfolder):

    """Sort through the export directory to all exported subdirectories"""

    # assume that the current folder is the highest folder
    highest = ''

    # goes through the list of all files in path
    for export in os.listdir(exportsfolder):

        # loop through the next folder in the export folder
        export_subfolder = os.path.join(exportsfolder, export)

        # check if the file found is an actual folder
        if os.path.isdir(export_subfolder):
            if not highest:
                # first export folder found
                highest = export_subfolder
            else:

                # check if the current folder is a higher num than current highest
                try:
                    if int(export_subfolder) > int(highest):
                        highest = export_subfolder

                # the folder found isn't all numbers, so skip
                except ValueError:
                    continue

    # return the highest-numbered folder
    return os.path.join(highest)


# search for .log file, but returns list if any duplicates found
def findlogfile(root):

    """Find all logfiles, including flagging duplicate logfiles"""

    logfile = ''
    duplicates = []

    # loop through the files in the directory to find all possible log files
    for file in os.listdir(root):
        if file.endswith('.log'):
            if not logfile:
                # a log file hasn't been found before
                logfile = os.path.join(root, file)
            # if file.endswith('.DS_Store'): # ??
            #     x = file
            else:
                dupilcate.append(file)

    # reutrn no duplicates found, so just the found logfile
    if not duplicates:
        return logfile

    # return duplicate logfiles
    return duplicates


# accounts for future ver where it uses 'info.xslx' + 'info.old_style.csv'
def findinfofile(root):

    """Identify the location of the info file"""

    # in future will include 'info.xlsx'
    possiblenames = ('info.csv', 'info.old_style.csv')

    # generate path to info file
    for file in os.listdir(root):
        if file in possiblenames:
            return os.path.join(root, file)
