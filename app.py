from flask import Flask, render_template, request, redirect
from apscheduler.schedulers.background import BackgroundScheduler
from getStudents import getStudents
from pytz import timezone
from getFreePeriod import getFreePeriod
from send import send
#from datetime import datetime, time
import datetime
from password import password
from threading import Timer


app = Flask(__name__, static_url_path='', static_folder='static',)

# All times are localized and interpreted in this timezone.
TIMEZONE = timezone("America/New_York")

OPEN_TIME = datetime.time(7, 0)
CLOSE_TIME = datetime.time(23, 45)


# Manage the school schedule, and keep track of registered students
class RegistrationManager():
    # All times are localized and interpreted in this timezone.

    # Constructor
    def __init__(self):
        # self.cron = BackgroundScheduler()
        # self.cron.add_job(func=lambda: self.sendMail(),
        #                   trigger='cron',
        #                   hour=CLOSE_TIME.hour,
        #                   minute=CLOSE_TIME.minute,
        #                   timezone=TIMEZONE)
        # self.cron.add_job(func=lambda: self.refreshStudents(),
        #                   trigger='cron',
        #                   hour=OPEN_TIME.hour,
        #                   minute=OPEN_TIME.minute,
        #                   timezone=TIMEZONE)
        # self.cron.start()
    # Setup recurring events to send mail, and refresh the student list
            


        # Always refresh on startup
        self.refreshStudents()
        
    # Destructor
    def __del__(self):
        # Shut down the recurring events when finished
        self.cron.shutdown()
    
    
    # Require a login to prevent outside users
    loggedIn = False

    def checkLogin(self, guess):
        if guess == password:
            registration.loggedIn = True
            return True
        else:
            return False
    # Properties
    # =========================
    # Check whether registration is currently open
    def isOpen(self):
        timeNow = datetime.datetime.now(TIMEZONE).time()
        if self.isWednesday():
            return (OPEN_TIME <= timeNow) and (timeNow <= datetime.time(10, 15))
        else:
            return (OPEN_TIME <= timeNow) and (timeNow <= CLOSE_TIME)
    

    # Get the names of all currently unregistered students
    def unregisteredStudents(self):
        return [name for name in self.students if self.students[name].signedIn == False]

    # Actions
    # =========================
    # Refresh the list of students for the current day
    def refreshStudents(self):
        print("Refreshing student list.")
        self.freePeriod = getFreePeriod()
        self.students = getStudents(self.freePeriod)

    # Send mail containing the list of unregistered students
    def sendMail(self):
        print("Sending mail.")
        send(self.unregisteredStudents())

    # Attempt to register a student name, returns false if there's an error
    def register(self, student):
        if not self.isOpen():
            return "Error: Registration is not open"

        if student not in self.students:
            return "Error: Student not found"

        if self.students[student].signedIn:
            return "Warning: Student already signed in"

        self.students[student].signedIn = True
        return "Ok"
    
    def isWednesday(self):
        dayOfWeek = datetime.datetime.now(TIMEZONE).strftime("%A")
        return(dayOfWeek == "Wednesday")
    
    #####SET TIMERS FOR OPEN AND CLOSING TASKS
    def awaitOpen(self):
        timeNow = datetime.datetime.now(TIMEZONE).time()
        deltaH = timeNow.hour - OPEN_TIME.hour
        deltaM = timeNow.minute - OPEN_TIME.minute
        deltaS = timeNow.second - OPEN_TIME.second
        seconds = deltaH*3600 + deltaM*60 + deltaS
                
        t = Timer(seconds, registration.refreshStudents)
        t.start() 


    def awaitClose(self):
        timeNow = datetime.datetime.now(TIMEZONE).time()
        if(registration.isWednesday()):
            WEDNESDAY_TIME = datetime.time(10, 15)
            deltaH = timeNow.hour - WEDNESDAY_TIME.hour
            deltaM = timeNow.minute - WEDNESDAY_TIME.minute
            deltaS = timeNow.second - WEDNESDAY_TIME.second
            seconds = deltaH*3600 + deltaM*60 + deltaS
        else:
            deltaH = timeNow.hour - CLOSE_TIME.hour
            deltaM = timeNow.minute - CLOSE_TIME.minute
            deltaS = timeNow.second - CLOSE_TIME.second
            seconds = deltaH*3600 + deltaM*60 + deltaS

        t = Timer(seconds, registration.sendMail)
        t.start() 


registration = RegistrationManager()




@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    elif request.method == "POST":
        guess = request.form.get("guess")
        if registration.checkLogin(guess):
            return redirect("/")
        else:
            return render_template("login.html")
        


@app.route('/', methods=["GET", "POST"])
def home():
    if not registration.loggedIn:
        return redirect("/login")
        
    # If this is a form submission, attempt to register the student
    if request.method == "POST":
        student = request.form["student"]
        print(f"Registering '{student}': {registration.register(student)}")
    # if the time is between 7:00 and 9:30 return active page, if time is outside 7:00 - 9:30 return the inactive page
    # store the students who login between 7:00 and 9:30 and send an email at 9:30 with the list
    if registration.isOpen():
        return render_template("open.html", names=registration.unregisteredStudents())

    return render_template("closed.html")


if __name__ == '__main__':
    app.run(debug=False, port=8000)
