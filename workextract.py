#from tabula import read_pdf
#from tabulate import tabulate
import camelot
import re
import datetime
import sqlite3
import shutil
import utils

class Shift:
    def __init__(self, id, name, day, date, time):
        self.id = id
        self.name = name
        self.day = day
        self.date = date
        self.time = time
        self.start = [0,0]
        self.end = [0,0]
        self.hours = 0

    def getHours(self):
        start, end = self.time.split("-")
        startH, startM = start.split(":")
        startH = float(startH)
        startM = float(startM)
        if(startH >= 11):
            self.start = [startH, startM]
        else:
            self.start = [startH + 12, startM]
        endH, endM = end.split(":")
        endH = float(endH)
        endM = float(endM)
        self.end = [endH+12, endM]
        hour = self.end[0] - self.start[0]
        if(self.end[1] != 0 or self.start[1] != 0):
            ms = self.start[1] / 60
            me = self.end[1] / 60
            m = me - ms
            self.hours = (hour + m)
        else:
            self.hours = hour

class Employee:
    def __init__(self, index, name, pay=None):
        self.index = index
        self.name = name
        self.pay = pay
        self.shifts = []
        self.hours = 0
    def insertShift(self, shift):
        self.shifts.append(shift)
    def insertHours(self, hours):
        self.hours = self.hours + hours
    def calcHours(self):
        for i in self.shifts:
            self.hours += i.hours
    def display(self):
        print(self.name, self.index, self.hours)

def ProcessSchedule(file):
    employees = []
    camtitle = camelot.read_pdf(file, flavor = 'stream')#, table_regions=['0,1000,700,550'])
    print(camtitle[0].df)
    firstday, lastday = camtitle[0].df[4][0].split(' - ')
    firstmon, firstday, firstyear = firstday.split('/')
    firstyear = "20" + firstyear
    date = datetime.date(int(firstyear), int(firstmon), int(firstday))
    cam = camelot.read_pdf(file)
    schedule = cam[0].df
    names = []
    days = []
    start = None

    #Getting name and day lists with indexes
    for i in range(len(schedule[0])):
        if(schedule[0][i] != ""):
            if(start is None):
                start = i
            if re.search(r'[0-9()]', schedule[0][i]):
                names.append([i, re.sub(r'[0-9()]','', schedule[0][i])])
            elif "." in schedule[0][i]:
                names.append([i, schedule[0][i].replace(".", "")])
            else:
                names.append([i, schedule[0][i]])
    print(names)
    for i in range(len(names)):
        emp = Employee(names[i][0], names[i][1])
        if emp is not None:
            employees.append(emp)
    for i in schedule.head():
        if(schedule[i][0] != ""):
            days.append([i,schedule[i][0], date])
            date = date + datetime.timedelta(days=1)
    print(days)
    shifts = []
    takenoff = []
    for i in range(len(names)):
        for x in range(len(days)):
            if(schedule[x+1][i+start] != ""):
                shift = Shift(names[i][0], names[i][1], days[x][1], days[x][2], schedule[x+1][i+start])
                print("Original",shift.name, shift.day, shift.time, shift.hours)
                if("OFF" in shift.time.upper()):
                    takenoff.append(shift)
                elif(re.search(r'^[a-z A-Z //]', shift.time)):
                    takenoff.append(shift)
                elif(re.search(r'[a-z A-Z //]',shift.time)):
                    shift.time = re.sub(r'[a-z A-Z //]', "", shift.time)
                    shifts.append(shift)
                else:
                    shifts.append(shift)
    poplist = []
    for i in range(len(shifts)):
        if( shifts[i].time == ""):
            poplist.append(i)
        else:
            shifts[i].getHours()
    for i in poplist:
        shifts.pop(i)
    for i in range(len(shifts)):
        for x in range(len(employees)):
            if(shifts[i].name == employees[x].name):
                employees[x].insertShift(shifts[i])
    # Get Hours
    for emp in employees:
        emp.calcHours()

    # Backup DB File
    shutil.copyfile('work.db', 'work.db.bak')
    
    # Write to DB
    with sqlite3.connect('work.db') as con:
        cur = con.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS Employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL, pay REAL, role TEXT, phone VARCHAR(18));')
        cur.execute('CREATE TABLE IF NOT EXISTS Shifts (id INTEGER PRIMARY KEY AUTOINCREMENT, employee TEXT, time TEXT, day TEXT, date TIMESTAMP, hours DOUBLE(3,2));')        
        cur.execute('SELECT name FROM Employees;')
        curemp = cur.fetchall()
        curemps = []
        for i in curemp:
            curemps.append(i[0])
        for i in employees:
            if (i.name in curemps):
                pass
            else:
               #print("Inserting", i.name)

                insert = """INSERT INTO Employees (name, role) VALUES (?, ?);"""

                data = (i.name, "Training")
                cur.execute(insert, data)
                utils.logChange("System", "Insert Employee", data[0])
        con.commit()

    with sqlite3.connect('work.db') as con:
        cur = con.cursor()
        cur.execute('SELECT employee, date FROM Shifts;')
        curshifts = cur.fetchall()
        for i in range(len(employees)):

            insert = """INSERT INTO Shifts (employee, time, day, date, hours) VALUES (?, ?, ?, ?, ?);"""

            for x in employees[i].shifts:
                if(any(str(x.date) in d[1] for d in curshifts)):
                    pass
                else:
                    #print("Inserting", x.name, x.date)
                    data = (x.name, x.time, x.day, x.date, x.hours)
                    cur.execute(insert, data)
                    shift = utils.Shift([x.name, x.date, x.day, x.time, x.hours])
                    utils.logChange("System", "Insert Shift", shift)
            con.commit()