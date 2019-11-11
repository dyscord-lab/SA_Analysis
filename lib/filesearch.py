import os


def find_participants(dataroot):

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
def find_highest_export(exportsfolder):

    """Sort through the export directory to all exported subdirectories
        and find the most recent export"""
    
    # assume that the current folder is the highest folder
    highest = max([os.path.basename(next_dir) 
                   for next_dir in os.scandir(exportsfolder) 
                   if next_dir.is_dir()])

    # return the highest-numbered folder
    return os.path.join(exportsfolder,highest)


# search for .log file, but returns list if any duplicates found
def find_logfile(root):

    """Find all logfiles, including flagging duplicate logfiles"""

    logfile = ''
    duplicates = []

    # loop through the files in the directory to find all possible log files
    for file in os.listdir(root):
        if file.endswith('.log'):
            if not logfile:
                # a log file hasn't been found before
                logfile = os.path.join(root, file)
            else:
                dupilcate.append(file)

    # reutrn no duplicates found, so just the found logfile
    if not duplicates:
        return logfile

    # return duplicate logfiles
    return duplicates
