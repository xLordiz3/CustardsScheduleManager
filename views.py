"""
Routes and views for the flask application.
"""
import os
import re
from datetime import datetime
from site import abs_paths
from flask import render_template, request, jsonify, redirect, url_for
import flask_login
#from WorkThing import app, utils
from workthing import app
#from workthing import users
import utils, workextract
from apscheduler.schedulers.background import BackgroundScheduler
import json

# Scheduling Weekly Email Pull, Not functioning currently
def weeklyUpdate():
    print("Getting Schedule")
    current = utils.getCurrentSchedule()
    workextract.ProcessSchedule(current)    

sch = BackgroundScheduler()
sch.add_job(weeklyUpdate, 'cron', day_of_week=6, hour=11, minute= 0)
sch.start()
# End Scheduling

# Should be obselete
tradeShift1 = []
tradeShift2 = []
#

# Flask Login 
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
users = {}
users["admin"] = {'password': "bluesprings"}
for e in utils.getEmployeesObjects():
    if e.role == 'Manager' or e.role == 'Owner':
        pa = e.name[0:3] + str(e.phone)[-3:]
        name = re.match(r'(\w* \w{2,})', e.name)
        if name is None:
            users[e.name] = { 'password': pa }
        else:
            name = name[0]
            name = re.match(r'(\w* \w{1})', name)
            users[name[0]] = { 'password': pa }

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(name):
    if name not in users:
        print("No User")
        return
    user = User()
    user.id = name
    return user

@app.route('/login', methods=['POST', 'GET'])
def login():
    users = {}
    users["admin"] = {'password': "bluesprings"}
    for e in utils.getEmployeesObjects():
        if e.role == 'Manager' or e.role == 'Owner':
            pa = e.name[0:3] + str(e.phone)[-3:]
            name = re.match(r'(\w* \w{2,})', e.name)
            if name is None:
                users[e.name] = { 'password': pa }
            else:
                name = name[0]
                name = re.match(r'(\w* \w{1})', name)
                users[name[0]] = { 'password': pa }
    if(request.method == 'GET'):
        return render_template(
            'login.html'
        )
    name = request.form['name']
    if name in users and request.form['password'] == users[name]['password']:
        user = User()
        user.id = name
        flask_login.login_user(user)
        print(flask_login.current_user.id)
        return redirect(url_for('home'))
    return 'Bad Login'

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))


# End Flask Login

# Home Page with schedule
@app.route('/', methods=['POST', 'GET'])
@app.route('/home', methods=['POST', 'GET'])
@flask_login.login_required
def home():
    """Renders weeks shifts"""
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
        curdate = utils.getDaysOfWeek().currentDate.strftime('%m/%d/%Y'),
        curday =str(utils.getDaysOfWeek().currentDayWord).upper(),
        fdate = utils.getDaysOfWeek().firstDate.strftime('%m/%d/%Y'),
        ldate = utils.getDaysOfWeek().lastDate.strftime('%m/%d/%Y'),
        sch = utils.getWeekSchedule(utils.getDaysOfWeek()),
        shifts = utils.getShiftsPerDay(utils.getWeekSchedule(utils.getDaysOfWeek())),
        emps = utils.getEmployees()
    )

# Lists Employees and statistics, waiting rewrite, nonfunctional
@app.route('/employees', methods=['POST', 'GET'])
@flask_login.login_required
def employees():
    """Renders list of employees and stats"""
    averages = [None, None, None, None]
    selemp = None
    if(request.method == 'POST'):
        selemp = request.form['emps']
        curshifts, averages = utils.getEmployeeHistory(selemp)
        #print(selemp)
    else:
        curshifts = None
        selemps = None
                
    return render_template(
        'employees.html',
        title='Employees',
        year=datetime.now().year,
        message='Employee Statistics',
        emps = utils.getEmployees(),
        name = selemp,
        shifts = curshifts,
        total = averages[0],
        nums = averages[1],
        avg = averages[2],
        #weektotal = averages[3]
    )

# Page for developer access
@app.route('/dev', methods=['POST', 'GET'])
@flask_login.login_required
def dev():
    """Renders the about page."""
    import workextract
    #print(request.form)
    if(request.method == 'POST'):
        if(request.form.get('getpdf') == 'Get PDF'):
            #print("yay")
            current = utils.getCurrentSchedule()
            workextract.ProcessSchedule(current)
        elif(request.form.get('impcsv')):
            csv = request.form.get('selcsv')
            print(csv)
        elif(request.form.get('imppdf')):
            pdf = request.files['selpdf']
            print(pdf.filename)
            pdf.save(os.path.join(app.config['UPLOADED_PHOTOS'], pdf.filename))
            workextract.ProcessSchedule(os.path.join(app.config['UPLOADED_PHOTOS'], pdf.filename))
    return render_template(
        'dev.html',
        title='Developer',
        year=datetime.now().year,
        message='Server side fiddling tools.'
    )

# Old switch shift, obselete should be alright to remove
@app.route('/shiftchange', methods=['POST', 'GET'])
@flask_login.login_required
def shiftchange():
    se1 = None
    ss1 = None
    se2 = None
    ss2 = None
    e1 = "yes"
    e1w = []
    e2w = []
    e2 = ""
    e3 = ""
    e4 = ""
    e5 = ""
    changetype = ""
    if(request.method == 'POST'):
        if(request.form.get('emp1') == "First Employee"):
            se1 = request.form.get('scemps')
            e1w = utils.getEmployeeWeek(se1)
            changetype = request.form.get('ct')
            tradeShift1.clear()
            tradeShift2.clear()
            print(se1, e1w)
        if(request.form.get('sh1') == "Trade"):
            ss1 = request.form.get('scshift')
            se1 = request.form.get('se1')
            changetype = "Trade"
            print("Trade")
        if(request.form.get('sh1') == "Give Away"):
            ss1 = request.form.get('scshift')
            se1 = request.form.get('se1')
            changetype = "Give"
            print("Give")
        if(request.form.get('sh1') == "Edit"):
            print("Edit")
        if(request.form.get('emp2') == "Second Employee"):
            changetype = request.form.get('ct')
            ss1 = request.form.get('ss1')
            se1 = request.form.get('se1')
            se2 = request.form.get('scemps2')
            e2w = utils.getEmployeeWeek(se2)
            print("Second Employee")   
            print(se2)         
        if(request.form.get('ct') == "Give" and request.form.get('e5') == "yes"):
            ss1 = request.form.get('ss1').replace("'", "").replace("{", "").replace("}", "")
            ss2 = ""
            se1 = request.form.get('se1')
            se2 = request.form.get('scemps2')
            changetype = request.form.get('ct')
            tradeShift1.append(se1)
            tradeShift1.append(ss1)
            tradeShift2.append(se2)
            tradeShift2.append(ss2)
            print(tradeShift1, tradeShift2)
            print("Confirm")
        if(request.form.get('ct') == "Trade" and request.form.get('e5') == "yes"):           
            ss1 = request.form.get('ss1').replace("'", "").replace("{", "").replace("}", "")
            ss2 = request.form.get('scshift2').replace("'", "").replace("{", "").replace("}", "")
            se1 = request.form.get('se1')
            se2 = request.form.get('se2')
            print(ss1, se1, ss2, se2)
            changetype = request.form.get('ct')
            tradeShift1.append(se1)
            tradeShift1.append(ss1)
            tradeShift2.append(se2)
            tradeShift2.append(ss2)
            print("Confirm")
        if(request.form.get("sh2") == "Confirm"):
            changetype = request.form.get('ct')
            print(changetype, tradeShift1, tradeShift2)
            if(changetype == "Trade"):
                print("Trading")
                utils.switchShifts(tradeShift1[0], tradeShift1[1], tradeShift2[0], tradeShift2[1])
            else:
                print("Giving")
                utils.switchShifts(tradeShift1[0], tradeShift1[1], tradeShift2[0])
            #print(ts1.employee, ts1.day)
            #utils.switchShifts(shiftTrade[2], shiftTrade[0], shiftTrade[3], shiftTrade[1])
            print("Completed")
        #print(e1w)
        e1 = request.form.get('e1')
        e2 = request.form.get('e2')
        e3 = request.form.get('e3')
        e4 = request.form.get('e4')
        e5 = request.form.get('e5')
    return render_template(
        'shiftchange.html',
        title = "Shift Change",
        year = datetime.now().year,
        message = "Switching or Giving up Shifts",
        emps = utils.getEmployees(),
        selemp1 = se1,
        ph1 = e1,
        ct = changetype,
        e1week = e1w,
        ph2 = e2,
        selemp2 = se2,
        e2week = e2w,
        shift1 = ss1,
        ph3 = e3,
        ph4 = e4,
        shift2 = ss2,
        ph5 = e5,
    )

# Old Employee Edit, should be good to remove
#@app.route('/editemp', methods=['POST', 'GET'])
def editemp():
    t = "init"
    if(request.method == 'POST'):
        if (request.form.get('esel') == "Select"):
            print(request.form.get('sempse'))
            print(utils.getEmployeeWeek(request.form.get('sempse')))
            t = "esel"
        if (request.form.get('ssel') == "Select"):
            print(utils.getWeekSchedule())
            t = "ssel"
    return render_template(
        'edit.html',
        title = "Edit",
        message = "Edit Employees",
        emps = utils.getEmployees(),
        shifts = utils.getWeekSchedule(utils.getDaysOfWeek()),
        type = t
    )

# Edit Shift, waiting rewrite, functional
@app.route('/editshi', methods=['POST', 'GET'])
@flask_login.login_required
def editshi(typet=None, eshift=None):
    t = "ssel"
    s = None
    st = None
    et = None
    if(request.method == 'POST'):
        if(request.form.get('shiftsel') == "Select"):
            temp = request.form.get('shift')
            temp = temp.replace("'", "")
            temp = temp.replace("(", "")
            temp = temp.replace(")", "")
            temp = temp.replace("\"", "")
            tempA = temp.split(",")
            print(temp, tempA)
            s = utils.Shift(tempA)
            #tempd = s.date.split("-")
            print(s.employee, s.date, type(s.date))
            t = "eshift"
            temp = s.time.replace(" ", "")
            temp = temp.split("-")
            tst = temp[0].split(":")
            if(int(tst[0]) < 11):
                tst[0] = int(tst[0]) + 12 
            st = str(tst[0]) + ":" + str(tst[1])
            tet = temp[1].split(":")
            if(int(tet[0]) < 11):
                tet[0] = int(tet[0]) + 12
            et = str(tet[0]) + ":" + str(tet[1])                 
            print(st, et)
        if(request.form.get('sss') == "Change"):
            starttime = request.form.get('st')
            endtime = request.form.get('et')
            tst = starttime.split(":")
            if(int(tst[0]) > 12):
                tst[0] = int(tst[0]) - 12 
            st = str(tst[0]) + ":" + str(tst[1])
            tet = endtime.split(":")
            if(int(tet[0]) > 12):
                tet[0] = int(tet[0]) - 12
            et = str(tet[0]) + ":" + str(tet[1])   
            newTime = st + "-" + et
            print(newTime)
            newName = request.form.get('empin')
            s = utils.Shift()
            s.fromAdd(request.form.get('emp'), request.form.get('time').replace(" ", ""), request.form.get('day').replace(" ", ""), request.form.get('date').replace(" ", ""))
            s.printShift()
            #s.getHours()
            if( newName is s.employee):
                utils.editShift(s, newTime)
            else:
                utils.editShift(s, newTime, newName)
        if request.form.get('sdel') == "Delete":
            s = utils.Shift()
            s.fromAdd(request.form.get('emp'), request.form.get('time').replace(" ", ""), request.form.get('day').replace(" ", ""), request.form.get('date').replace(" ", ""))
            utils.deleteShift(s)
        if(typet is not None and eshift is not None):
            print(eshift)
    return render_template(
        'edit.html',
        title = "Edit",
        message = "Edit Shifts",
        shifts = utils.getWeekSchedule(utils.getDaysOfWeek()),
        selshift = s,
        start = st,
        end = et,
        type = t,
        emps = utils.getEmployees()
    )

# Add Employee to database
@app.route('/addemp', methods=['POST', 'GET'])
@flask_login.login_required
def addemployee():
    role = utils.getRoles()
    if(request.method == 'POST'):
        if(request.form.get('addempsel') == 'Add Employee'):
            emp = utils.Employee(request.form)
            emp.addEmployee()
    return render_template(
        'add.html',
        title = "Add Employee",
        #message = "Add Employee",
        type = "emp",
        roles = role
    )
# Add shift to database, waiting rewrite
@app.route('/addshi', methods=['POST', 'GET'])
@flask_login.login_required
def addshift():
    today = datetime.today()
    days=["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    names = utils.getEmployees()
    if(request.method == 'POST'):
        if(request.form.get("addshisel") == "Add Shift"):
            en = request.form.get('empname')
            ets = request.form.get('st')
            ete = request.form.get('et')
            edy = request.form.get('day')
            edt = request.form.get('date')
            et = utils.timeCorrection(ets, ete)
            shift = utils.Shift()
            shift.fromAdd(en, et, edy, edt)
            utils.addShift(shift)

   # if (request.form.get(""))
    return render_template(
        'add.html',
        title = "Add",
        message = "Add Shift",
        type = "shi",
        days = days,
        today = today,
        emps = names
    )

# Lists all shifts
@app.route('/shifts', methods=['POST', 'GET'])
@flask_login.login_required
def shifts():
    if(request.method == 'POST'):
        if(request.form.get('shiedit') == 'Edit'):
            #print(request.form.get('eshift'))
            #editshi("eshift", request.form.get('eshift'))
            print(request.form.get('eshift'))
            s = request.form.get('eshift')
            s = s.replace("(", "")
            s = s.replace("'", "")
            s = s.replace(")", "")
           # s = s.replace(" ", "")
            print(s)
            temp = s.split(",")
            shift = []
            for s in temp:
                s = s.lstrip()
                shift.append(s)
            print(shift)
            e = utils.Shift()
            e.edt(shift)
            e.getHours()
            #e.printShift()
            times = e.time.split("-")
            starttime = times[0]
            endtime = times[1]
            print(times)
            tst = starttime.split(":")
            if(int(tst[0]) < 12):
                tst[0] = int(tst[0]) + 12 
            st = str(tst[0]) + ":" + str(tst[1])
            tet = endtime.split(":")
            if(int(tet[0]) < 12):
                tet[0] = int(tet[0]) + 12
            et = str(tet[0]) + ":" + str(tet[1])  
            print(st, et)
            datetest = datetime.strptime(e.date, "%Y-%m-%d")
            days=["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
            print(days[datetest.weekday()])
            e.day = days[datetest.weekday()]
            return render_template(
                'edit.html',
                title = "Edit",
                message = "Edit Shifts",
                #shifts = utils.getWeekSchedule(utils.getDaysOfWeek()),
                selshift = e,
                start = st,
                end = et,
                type = "eshift",
                emps = utils.getEmployees()
            )
    else:
        return render_template(
            'allshifts.html',
            title = "Shifts",
            message = "All Shifts",
            shifts = utils.getAllShifts()
    )

# Employee get api, for HomeAssistant use later
@app.route('/api/employees/<string:name>', methods=['GET', 'POST'])
def apiemp(name):
    print(name)
    shifts = utils.getEmployeeWeek(name)
    for i in shifts:
        print(i)
    return jsonify(shifts)

# Edit page, can choose to edit Employees or Shifts
@app.route('/edit', methods=['POST', 'GET'])
@flask_login.login_required
def edit():
    return render_template(
        'editm.html',
        title = "Edit",
        type = "select",
        emps = utils.getEmployees(),
        shifts = utils.getAllShifts()
    )

# New Edit Employee
@app.route('/edit/employee/<string:name>', methods=['POST', 'GET'])
@flask_login.login_required
def editempm(name):
    #name = request.form['emp']
    emp = utils.getEmployee(name)
    rolelist = utils.getRoles()
    roles = []
    roles.append(emp.role)
    for r in rolelist:
        if(r != emp.role):
            roles.append(r)
    #print(roles)
    #print("here")
    return render_template(
        'editm.html',
        title = "Edit Employee",
        type = "employee",
        roles = roles,
        selemp = emp
    )

# Edit Employee database write
@app.route('/editempconf', methods = ['POST', 'GET'])
@flask_login.login_required
def editempconf():
    emp = utils.Employee(request.form)
    emp.editEmployee()
    return "Complete"

# New Switching shifts
@app.route('/switch', methods=['POST', 'GET'])
@flask_login.login_required
def switchPage():
    return render_template(
        'switch.html',
        title="Change Shifts",
        message="Trade or Give Up Shifts",
        emps = utils.getEmployees()
    )

# Returns employee shifts for shift change
@app.route('/switchemp', methods=['POST', 'GET'])
@flask_login.login_required
def switchemp():
    if request.method == 'POST':
        emp = request.form['emp']
        print(emp)
        print(utils.getEmployeeWeek(emp))
        return jsonify(utils.getEmployeeWeek(emp))

# Confirming Switch Shifts, waiting rewrite
@app.route('/switchconf', methods=['POST', 'GET'])
@flask_login.login_required
def switchconf():
    s1 = utils.Shift()
    s2 = utils.Shift()
    if request.method == 'POST':
        ss1 = request.form['s1']
        ss2 = request.form['s2']
        if( ss2 == ""):
            e2 = request.form['e2']
        stype = request.form['type']
        s1.fromJSON(ss1)
        s1.printShift()
        print("Type:", stype)
        if(ss2 != ""):
            s2.fromJSON(ss2)
            s2.printShift()
        else:
            #print(e2)
            s2.setName(e2)
            s2.printShift()
        utils.switch(flask_login.current_user.id, stype, s1, s2)
    return "Complete"
