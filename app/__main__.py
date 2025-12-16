from flask import Flask, render_template



app = Flask(__name__)


@app.route('/')
def concent_form():
    return render_template("consent.html")

@app.route('/survey')
def survey():
    return render_template("survey.html")

@app.route('/fingerprint')
def fingerprint():
    return render_template("fingerprint.html")

@app.route('/thankyou')
def thankyou():
    pass
# main driver function
if __name__ == '__main__':
    app.run()