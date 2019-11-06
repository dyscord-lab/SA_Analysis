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
def findhighest(path):
    highest = ''
    for exports in os.listdir(path):

        if not highest:
            highest = exports
        else:
            exp = int(exports)
            high = int(highest)
            if exp > high:
                highest = exports

    return os.path.join(path, highest)


# search for .log file, but returns list if any duplicates found
def findlogfile(root):
    logfile = ''
    duplicates = []

    for file in os.listdir(root):
        if file.endswith('.log'):
            if not logfile:
                logfile = os.path.join(root, file)
            if file.endswith('.DS_Store'):
                x = file
            else:
                dupilcate.append(file)

    # if no duplicates found
    if not duplicates:
        return logfile

    participant = os.path.split(root)[1]
    day = os.path.split(os.path.split(root)[0])[1]

    print('\nduplicates found for ' + str(day) + '_' + str(participant))
    print(duplicates)

    return duplicates


# accounts for future ver where it uses 'info.xslx' + 'info.old_style.csv'
def findinfofile(root):
    # in future will include 'info.xlsx'
    possiblenames = ('info.csv', 'info.old_style.csv')

    for file in os.listdir(root):
        if file in possiblenames:
            return os.path.join(root, file)
