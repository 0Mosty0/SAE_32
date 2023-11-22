# Le Framework (générateur de pages HTML)
from flask import Flask, render_template

# Application Flask
app = Flask(__name__)

# Pages HTML
pageACCUEIL = "templates/base.html"

############################################################################################
@app.route("/")
def index():
   return render_template(pageACCUEIL)

# Script de débuggage
if __name__ == "__main__":
   app.run(host='0.0.0.0', debug = True)