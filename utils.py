import datetime as dt
import sqlite3
import re
import email, imaplib, os
import utils, workextract
import json

class Employee:
    def __init__(self, dict):
        self.id = dict['id']
        self.name = dict['name']
        self.role = dict['role']
        self.phone = dict['phone']
    """
    def __init__(self, *args):
        if(len(args) == 1):
            e = args[0]
            self.id = e[0]
            self.name = e[1]
            self.role = e[2]
            self.phone = e[3]
        if(len(args) == 2):
            self.id = None
            self.name = args[0]
            self.role = args[1]
        if(len(args) == 3):
            self.id = None
            self.name = args[0]
            self.role = args[1]
            self.phone = args[2]
        if(len(args) == 4):
            self.id = args[0]
            self.name = args[1]
            self.role = args[2]
            self.phone = args[3]
    """
    def addEmployee(self):
        print("Adding Employee", self.name, self.role, self.phone)
        sql = """INSERT INTO Employees (name, role, phone) VALUES (?, ?, ?);"""
        data = [self.name.upper(), self.role, self.phone]
        with sqlite3.connect('work.db') as con:
            cur = con.cursor()
            cur.execute(sql, data)
            con.commit()
    def editEmployee(self):
        print("Updating Employee", self.name, self.role, self.phone)
        sql = """UPDATE Employees SET name = ?, role = ?, phone = ? WHERE id = ?"""
        data = [self.name, self.role, self.phone, self.id]
        with sqlite3.connect('work.db') as con:
            cur = con.cursor()
            cur.execute(sql, data)
            con.commit()      

class Edit:
    def __init__(self):
        self.employee1
        self.employee2
        self.shift1
        self.shift2
    def LogChange(self):
        print("Logging Change")

class week:
    def __init__(self, curdayW, curday, curdate, firstdate, lastdate, prevdate):
        self.currentDayWord = curdayW
        self.currentDay = curday
        self.currentDate = curdate
        self.firstDate = firstdate
        self.lastDate = lastdate
        self.prevDate = prevdate
        self.days=["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

class Shift:
    def __init__(self, shift=None):
        if(shift == None):
            shift = ["","","","",""]
        self.employee = shift[0]
        self.date = shift[1]
        self.day = shift[2]
        self.time = shift[3]
        self.hours = shift[4]
    def fromEmp(self,emp, shift):
        self.employee = emp
        self.time = shift.time
        self.day = shift.day
        self.date = shift.date
        self.hours = shift.hours
    def toDict(self):
        d = {"Name": self.employee, "Time": self.time, "Day": self.day, "Date": self.date, "Hours": self.hours }
        return d
    def apiToDict(self):
        d = {"Date": self.date, "Day": self.day, "Time": self.time, "Hours": self.hours }
        return d
    def fromAdd(self, emp, time, day, date):
        self.employee = emp
        self.time = time
        self.day = day
        self.date = date
        self.getHours()
    def getHours(self):
        #print(self.time)
        start, end = self.time.split("-")
        startH, startM = start.split(":")
        startH = float(startH)
        startM = float(startM)
        if(startH >= 11):
            self.start = [startH, startM]
            #print(self.start)
        else:
            self.start = [startH + 12, startM]
            #print(self.start)
        endH, endM = end.split(":")
        endH = float(endH)
        endM = float(endM)
        self.end = [endH+12, endM]
        #print(self.end)
        hour = self.end[0] - self.start[0]
        #print(hour)
        if(self.end[1] != 0 or self.start[1] != 0):
            ms = self.start[1] / 60
            me = self.end[1] / 60
            m = me - ms
            self.hours = (hour + m)
        else:
            self.hours = hour
    def edt(self, ins):
        self.employee = ins[0]
        self.date = ins[1]
        self.time = ins[2]
        self.hours = self.getHours()
    def fromJSON(self, shift):
        s = json.loads(shift)
        self.employee = s['_name']
        self.date = s['_date']
        self.day = s['_day']
        self.time = s['_time']
        self.hours = s['_hours']
        if(self.hours is None):
            self.hours = self.getHours()
    def setName(self, name):
        self.employee = name 
    def setTime(self, time):
        self.time = time
        self.getHours()
    def printShift(self):
        print(self.employee, self.time, self.day, self.date, self.hours)
    
def getDaysOfWeek():    
    date = dt.datetime.today()
    day = date.weekday()
    first = None
    last = None
    f = day
    l = day
    if(day == 6):
        last = date
    elif(day == 0):
        first = date
    for i in range(7):
        f = f - 1
        l = l + 1
        #print(l)
        if(f == 0 and first == None):
            first = date - dt.timedelta(days = i + 1)
        if(l == 6):
            last = date + dt.timedelta(days = i + 1)
            #print(last)
    prev = first - dt.timedelta(days = 1)
    w = week(dt.datetime.today().strftime('%A'), day, date, first, last, prev)
    return w

def DB():
    c = sqlite3.connect('work.db')
    return c

def getWeekSchedule(w):
    w = getDaysOfWeek()
    shifts = []
    sql = """SELECT Shifts.employee, Shifts.date, Shifts.day, Shifts.time, Shifts.hours 
        FROM Shifts
        INNER JOIN Employees on Shifts.employee = Employees.name
        WHERE Shifts.date > ?
        AND Shifts.date < ?
        ORDER BY  
        Shifts.date ASC,
        CASE Employees.role
        when 'Owner' then 1
        when 'Manager' then 2
        when 'Shift Leader' then 3
        when 'Employee' then 4
        when 'Training' then 5
        end,
        Shifts.time;"""
    data = [w.prevDate, w.lastDate]
    c = DB()
    cur = c.cursor()
    cur.execute(sql, data)
    sch = cur.fetchall()
    for s in sch:
        shift = Shift(s)
        shifts.append(shift)
    return shifts

def getShiftsPerDay(shifts):
    days=["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    spd = []
    for day in days:
        for shift in shifts:
            if(day == shift.day):
                spd.append([day,shift])
    return spd

def getEmployees():
    emps = [""]
    c = DB()
    cur = c.cursor()
    cur.execute("SELECT DISTINCT name FROM Employees;" )
    e = cur.fetchall()
    for emp in e:
        emp = re.sub(r'[^a-z A-Z]',"", str(emp))
        emps.append(emp)
    return emps

def getEmployeesObjects():
    emps = []
    with sqlite3.connect('work.db') as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = "SELECT DISTINCT id, name, role, phone FROM Employees;" 
        cur.execute(sql)
        e = cur.fetchall()
        for emp in e:
            emp = Employee(emp)
            emps.append(emp)
        con.row_factory = None
    return emps

def getEmployee(name):
    with sqlite3.connect('work.db') as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        sql = """SELECT id, name, role, phone FROM Employees WHERE name = ?;"""
        data = [name,]
        cur.execute(sql, data)
        res = cur.fetchone()
        emp = Employee(res)
        con.row_factory = None
    return emp

def getEmployeeHistory(emp):
    c = DB()
    cur = c.cursor()
    sel = "SELECT * FROM Shifts WHERE employee = ? ORDER BY date DESC;"
    data = (emp,)
    cur.execute(sel, data)
    res = cur.fetchall()
    totalhours = 0.0
    averagehours = 0.0
    numshifts = 0
    weekhours = 0.0
    shifts = []
    for i in res:
        print(i)
        shift = Shift(i)
        shifts.append(shift)
        totalhours = totalhours + i[4]
        numshifts = numshifts + 1
    if(numshifts > 0):
        averagehours = totalhours / numshifts
    else:
        averagehours = 0
        weekhours = 0
    print("Total Hours:",totalhours, "Number of Shifts:", numshifts, "Average Hours:", averagehours)
    return shifts, [totalhours, numshifts, averagehours]#, weekhours]

def getEmployeeWeek(emp):
    shifts = []
    c = DB()
    cur = c.cursor()
    sel = "SELECT employee, date, day, time, hours FROM Shifts WHERE employee = ? AND date >= ? AND date <= ? ORDER BY date;"
    w = getDaysOfWeek()
    data = (emp, w.prevDate, w.lastDate)
    cur.execute(sel, data)
    res = cur.fetchall()
    for i in res:
        shift = Shift(i)
        shifts.append(shift.apiToDict())
    return shifts

def getRoles():
    roles = []
    with sqlite3.connect('work.db') as con:
        con.row_factory = lambda cursor, row: row[0]
        sql = "SELECT DISTINCT role FROM Employees;"
        cur = con.cursor()
        cur.execute(sql)
        roles = cur.fetchall()
    return roles


def switch(user, type, shift1, shift2=None, shift3=None):
    print(type)
    with sqlite3.connect('work.db') as con:
        cur = con.cursor()
        if(type == "TRADE" and shift2 != None):
            update = """UPDATE Shifts SET employee = ? WHERE employee = ? AND date = ? AND  time = ?;"""
            data = (shift2.employee, shift1.employee, shift1.date, shift1.time)
            cur.execute(update, data)
            con.commit()
            data = (shift1.employee, shift2.employee, shift2.date, shift2.time)
            cur.execute(update, data)
            con.commit()
            logChange(user, "Trade", [shift1, shift2]) 
        elif(type == "GIVE"):
            print("Giving")
            update = """UPDATE Shifts SET employee = ? WHERE employee = ? AND date = ? AND  time = ?;"""
            data = (shift2.employee, shift1.employee, shift1.date, shift1.time)
            cur.execute(update, data)
            con.commit()
            logChange(user, "Give", [shift1, shift2])
        elif(type == "SPLIT"):
            print("Split")
        elif(type == "TRADESTART" and shift2 != None):
            start1, end1 = shift1.time.split("-")
            start2, end2 = shift2.time.split("-")
            newtime1 = start2 + "-" + end1
            newtime2 = start1 + "-" + end2
            shift1.setTime(newtime1)
            shift2.setTime(newtime2)
            print("End Trade:",shift1.employee, shift1.time, shift2.employee, shift2.time)
            update = """UPDATE Shifts SET time = ?, hours = ? WHERE employee = ? AND date = ?;"""
            data = (shift1.time, shift1.hours, shift1.employee, shift1.date)
            cur.execute(update, data)
            con.commit()
            data = (shift2.time, shift2.hours, shift2.employee, shift2.date)
            cur.execute(update, data)
            con.commit()
            logChange(user, "Trade Start", [shift1, shift2])
        elif(type == "TRADEEND" and shift2 != None):
            start1, end1 = shift1.time.split("-")
            start2, end2 = shift2.time.split("-")
            newtime1 = start1 + "-" + end2
            newtime2 = start2 + "-" + end1
            shift1.setTime(newtime1)
            shift2.setTime(newtime2)
            print("End Trade:",shift1.employee, shift1.time, shift2.employee, shift2.time)
            update = """UPDATE Shifts SET time = ?, hours = ? WHERE employee = ? AND date = ?;"""
            data = (shift1.time, shift1.hours, shift1.employee, shift1.date)
            cur.execute(update, data)
            con.commit()
            data = (shift2.time, shift2.hours, shift2.employee, shift2.date)
            cur.execute(update, data)
            con.commit()
            logChange(user, "Trade End", [shift1, shift2])
      


#def importCSV(csv):
def switchShifts(e1, shift1, e2, shift2 = None, user = None):
    s1 = Shift()
    s2 = Shift()
    print("User", user)
    print("Shift 1",shift1)
    print("Shift 2", shift2)
    s1.fromForm(e1, shift1)     
    with sqlite3.connect('work.db') as con:
        cur = con.cursor()
        update = """UPDATE Shifts SET employee = ? WHERE date = ? AND employee = ? AND time = ?;"""
        data = (e2, s1.date, e1, s1.time)
        cur.execute(update, data)
        con.commit()
    if(shift2 is not None):
        s2.fromForm(e2, shift2)
        with sqlite3.connect('work.db') as con:
            cur = con.cursor()
            print("2nd Employee Update")
            update = """UPDATE Shifts SET employee = ? WHERE date = ? AND employee = ? AND time = ?;"""
            data = (e1, s2.date, e2, s2.time)
            cur.execute(update, data)
            con.commit()
    

def editShift(shift, newTime, newName=None):
    if newName is None:
        print("Time Change")
        sql = """UPDATE Shifts 
                 SET time = ?
                 WHERE ROWID in 
                 (SELECT ROWID 
                 FROM Shifts 
                 WHERE employee=? AND date=? AND time=? 
                 ORDER BY ROWID DESC 
                 LIMIT 1);"""
        data = [newTime, shift.employee, shift.date, shift.time]
    else:
        print("Name and Time Change")
        sql = """UPDATE Shifts 
                 SET time = ?, employee = ? 
                 WHERE ROWID in 
                 (SELECT ROWID 
                 FROM Shifts 
                 WHERE employee=? AND date=? AND time=? 
                 ORDER BY ROWID DESC 
                 LIMIT 1);"""
        data = [newTime, newName, shift.employee, shift.date, shift.time]
    print(data)
    with sqlite3.connect('work.db') as con:
        cur = con.cursor()
        cur.execute(sql, data)
        con.commit()

def addShift(shift):
    sql = """INSERT INTO Shifts (employee, time, day, date, hours) VALUES (?, ?, ?, ?, ?);"""
    data = [shift.employee, shift.time, shift.day, shift.date, shift.hours]
    print(data)
    with sqlite3.connect('work.db') as con:
        cur = con.cursor()
        cur.execute(sql, data)
        con.commit()
def deleteEmployee(emp):
    sql = """"""

def deleteShift(shift):
        sql = """DELETE FROM Shifts  
                 WHERE ROWID in 
                 (SELECT ROWID 
                 FROM Shifts 
                 WHERE employee=? AND date=? AND time=? 
                 ORDER BY ROWID DESC 
                 LIMIT 1);"""
        data = [shift.employee, shift.date, shift.time]
        with sqlite3.connect('work.db') as con:
            cur = con.cursor()
            cur.execute(sql, data)
            con.commit()
    
def shiftFromSelect(shift):
    s = re.search(r"^{'Name': '(.*)', 'Time': '(.*)', 'Day': '(.*)', 'Date': '(.*)', 'Hours': (\d*.?\d*)}", shift)
    ss = [s.group(1), s.group(2), s.group(3), s.group(4)]
    return ss

def timeCorrection(st, et):
    s = st.split(':')
    e = et.split(':')
    start = ""
    end = ""
    if(int(s[0]) > 12):
        t = int(s[0]) - 12
        start = str(t) + ":" + str(s[1])
    else:
        start = st
    if(int(e[0]) > 12):
        t = int(e[0]) - 12
        end = str(t) + ":" + e[1]
    else:
        end = et
    final = start + "-" + end
    return final

def logChange(user, action, shifts):
    cur = dt.datetime.now()
    cur = cur.strftime("%m/%d/%Y %H:%M:%S")
    with open("wt.log", 'a') as w:
        if action == "Insert Employee":
            msg = "["+cur+"]: {" + user + "} " + action + " " + shifts + "\n"
            print(msg)
            w.write(msg)
        elif action == "Insert Shift":
            msg = "["+cur+"]: {" + user + "} " + action + " (" + shifts.employee + ", " + str(shifts.date) + ", " + shifts.time + ")\n"
            print(msg)
            w.write(msg)
        elif action == "Give":
            msg = "["+cur+"]: {" + user + "} " + action + " (" + shifts[0].employee + ", " + shifts[0].date + ", " + shifts[0].time + ") To (" + shifts[1].employee + ")\n"
            print(msg)
            w.write(msg)
        else:
            msg = "["+cur+"]", user, action, shifts + "\n"
            print(msg)
            w.write(msg)
    #with open("") as log:

def getAllShifts():
    shifts = []
    with sqlite3.connect('work.db') as con:
        cur = con.cursor()
        sql = """SELECT employee, date, time FROM Shifts ORDER BY date DESC;"""
        cur.execute(sql)
        res = cur.fetchall()
        for r in res:
            s = Shift()
            s.edt(r)
            shifts.append(s)
    return shifts
