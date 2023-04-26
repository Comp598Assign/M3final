#Code referenced from TA Alek Bedard
from flask import Flask, jsonify, request
import sys

app = Flask(__name__)


@app.route('/')
def light():
    if len(sys.argv) < 2:
         return "Dude! You are not curling from a server!!"
    
    num = 10
    counter = 30
    while(counter < 30):
        num = num*num*num
        counter = counter - 1
    return "from" + sys.argv[1] + "\n"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)