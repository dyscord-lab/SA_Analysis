import os


def findparticipants(dataroot):
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
    highest = ''  # full path to the

    # goes through the list of all files in path
    for export in os.listdir(exportsfolder):

        export_subfolder = os.path.join(path, export)
        # check if the file found is an actual folder
        if os.path.isdir(export_subfolder):
            if not highest:
                # first export folder found
                highest = highest_export
            else:
                try:
                    # check if the current folder is a bigger num than current highest
                    if int(export_subfolder) > int(highest):
                        highest = exports

                except ValueError:
                    # the folder found isn't all numbers, so skip
                    continue

        # if not exports.endswith('.DS_Store'):
        #     if not highest:
        #         highest = exports
        #     else:
        #         if int(exp) > int(high):
        #             highest = exports


    return os.path.join(highest)


# search for .log file, but returns list if any duplicates found
def findlogfile(root):
    logfile = ''
    duplicates = []

    for file in os.listdir(root):
        if file.endswith('.log'):
            if not logfile:
                # a log file hasn't been found before
                logfile = os.path.join(root, file)
            # if file.endswith('.DS_Store'): # ??
            #     x = file
            else:
                dupilcate.append(file)

    # no duplicates found, so just the found logfile
    if not duplicates:
        return logfile

    return duplicates


# accounts for future ver where it uses 'info.xslx' + 'info.old_style.csv'
def findinfofile(root):
    # in future will include 'info.xlsx'
    possiblenames = ('info.csv', 'info.old_style.csv')

    for file in os.listdir(root):
        if file in possiblenames:
            return os.path.join(root, file)
