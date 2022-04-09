from flask import Flask , request, render_template, redirect, session, flash
from flask.helpers import url_for
from qa_engine import *
import json
import re
from time import time
from json2html import json2html

#app = Flask(__name__, template_folder='templates')
#app.secret_key= "AFGhjuyk" #secret ket required to work with session, 
#as data stored inside session are encrypted in server

app = Flask(__name__)
app.secret_key= "AFGhjuyk" #flash and session requires seccret key to encod ethe msgs
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

@app.route("/")
def hello_world():
    
    return "<p>Welcome !</p>"

@app.route("/home", methods=["POST", "GET"])
def home_method():
    if request.method == "POST":
        model_no=request.form.get("modelno")
        modelno_found, embedding_list =check_modelno(model_no)
        if not modelno_found:
            flash("requested model NOT Supported", 'info')
            return render_template("index.html")
        else:
            #return redirect(url_for("print_question", qst=ques))
            start= time()
            global im_obj, jsonfile, jsonfile_str  #global object 
            im_obj=InteractionModule(embedding_list)
            
            jsonfile=im_obj.get_jsonfile()
            jsonfile_str="jsonfile"
            end=time()
            #####can be accessed from anywhere ###############
            flash(f"You have selected Model No. {model_no}", 'info')
            session["modelno"]=model_no
            flash("Response time {:.3f} s".format(end-start), 'info')
            return render_template("question.html")
            #return render_template("question.html", modelno=model_no)
            #return f"you have entered <h1>{modelno}</h1>"
    else:
        return render_template("index.html")

@app.route("/question", methods=["GET", "POST"])
def handle_data():
    if request.method == "POST":
        ques=request.form.get("question")
        #print(type(ques), ques)
        if ques =='':
            return render_template("question.html")
        session["ques"]=ques
        start= time()
        im_obj.answer_question(session["ques"])
        end=time()
        flash("Response time {:.3f} s".format(end-start), 'info')
        return redirect(url_for("options_data"))
        #return f"<h1>you have entered {ques}</h1>"
    else:
        return render_template("question.html")

@app.route("/options", methods=["GET", "POST"])
def options_data():
    ques= session["ques"]
    if request.method == "POST":
        #eturn redirect(url_for("print_question1"))
        options=request.form.get("options")
        try:
            ind= int(options.split('_')[-1])
        except:
            flash(f"Please Select an OPTION", 'info')
            return render_template("options.html", options= im_obj.keys_option, question= ques, score=im_obj.keys_score+[0.0])
        start=time()
        if ind != len(im_obj.keys_option) -1:
            answer_ret= eval(jsonfile_str + im_obj.values_option[ind])
            new_str=json.dumps(answer_ret, indent=6)
            new_str=re.sub("hph", "-", new_str)
            ###########################
            json_val=json.loads(new_str)
            new_str=json2html.convert(json=json_val)
            ##########################
            session["answer"]=new_str
            end=time()
            flash("Response time {:.3f} s".format(end-start), 'info')
            return render_template("answer.html", question= ques, answer=new_str)
        else:
            #return render_template("question.html")

            im_obj.string_matching()
            end=time()
            flash("Response time {:.3f} s".format(end-start), 'info')
            return redirect(url_for("options1_data"))
        #return redirect(url_for("answer_data"))
        #return f"<h1>you have entered answer {new_str}</h1>"
    else:
        #return render_template("answer.html", options=["jim", "john", "kim"])
        return render_template("options.html", options= im_obj.keys_option, question= ques, score=im_obj.keys_score+[0.0])

@app.route("/answer", methods=["GET", "POST"])
def answer_data():
    ques= session["ques"]
    if request.method == "POST":
        #eturn redirect(url_for("print_question1"))
        options=request.form.get("options")
        try:
            ind= int(options.split('_')[-1])
        except:
             flash(f"Please Select an OPTION", 'info')
             return render_template("answer.html", question= ques, answer=session["answer"])
        if ind == 1:
            return render_template("question.html")
        else:
            start=time()
            im_obj.string_matching()
            end=time()
            flash("Response time {:.3f} s".format(end-start), 'info')
            return redirect(url_for("options1_data"))
            #return f"<h1>you have entered answer</h1>"
    else:
        return render_template("question.html")

@app.route("/answer1", methods=["GET", "POST"])
def answer1_data():
    ques= session["ques"]
    if request.method == "POST":
        #eturn redirect(url_for("print_question1"))
        options=request.form.get("options")
        try:
            ind= int(options.split('_')[-1])
        except:
            flash(f"Please Select an OPTION", 'info')
            return render_template("answer1.html", question= ques, answer=session["answer"])

        if ind == 1:
            return render_template("question.html")
        elif ind ==2:
            flash(f"Sorry unable to answer your query, please contact customer care", 'info')
            return render_template("question.html")
        else:
            start=time()
            ans, refs= im_obj.paraqa([ques])
            ###########################
            #json_val=json.loads(refs)
            refs=json2html.convert(json=refs)
            ##########################
            session["refs"]=refs
            session["answer"]=ans
            end=time()
            flash("Response time {:.3f} s".format(end-start), 'info')
            if ans=='':
                flash(f"Sorry unable to answer your query, please contact customer care", 'info')
                return render_template("question.html")
            else:
                return render_template("answer2.html", question=ques, answer=ans, ref=refs)

            #return f"<h1>ParaQA</h1>"
    else:
        return render_template("question.html")

@app.route("/answer2", methods=["GET", "POST"])
def answer2_data():
    ques= session["ques"]
    refs=session["refs"]
    ans=session["answer"]
    if request.method == "POST":
        #eturn redirect(url_for("print_question1"))
        options=request.form.get("options")
        try:
            ind= int(options.split('_')[-1])
        except:
            flash(f"Please Select an OPTION", 'info')
            return render_template("answer2.html", question=ques, answer=ans, ref=refs)

        if ind == 1:
            return render_template("question.html")
        else:
            flash(f"Sorry unable to answer your query, please contact customer care", 'info')
            return render_template("question.html")
    else:
        return render_template("question.html")

@app.route("/options1", methods=["GET", "POST"])
def options1_data():
    ques= session["ques"]
    if request.method == "POST":
        #eturn redirect(url_for("print_question1"))
        options=request.form.get("options")
        try:
            ind= int(options.split('_')[-1])
        except:
            flash(f"Please Select an OPTION", 'info')
            return render_template("options.html", options= im_obj.keys_option_1, question= ques, score=im_obj.keys_score_1+[0.0])
        start=time()
        if ind != len(im_obj.keys_option_1) -1:
            answer_ret= eval(jsonfile_str + im_obj.values_option_1[ind])
            new_str=json.dumps(answer_ret, indent=6)
            new_str=re.sub("hph", "-", new_str)
            ###########################
            json_val=json.loads(new_str)
            new_str=json2html.convert(json=json_val)
            ##########################
            session["answer"]=new_str
            end=time()
            flash("Response time {:.3f} s".format(end-start), 'info')
            return render_template("answer1.html", question= ques, answer=new_str)
        else:
            end=time()
            flash("Response time {:.3f} s".format(end-start), 'info')
            #return redirect(url_for("specific_data", question= ques))
            return render_template("specific.html", question= ques)
        #return redirect(url_for("answer_data"))
        #return f"<h1>you have entered answer {new_str}</h1>"
    else:
        #return render_template("answer.html", options=["jim", "john", "kim"])
        return render_template("options.html", options= im_obj.keys_option_1, question= ques, score=im_obj.keys_score_1+[0.0])

@app.route("/specific", methods=["GET", "POST"])
def specific_data():
    ques= session["ques"]
    if request.method == "POST":
        #eturn redirect(url_for("print_question1"))
        options=request.form.get("options")
        try:
            ind= int(options.split('_')[-1])
        except:
            flash(f"Please Select an OPTION", 'info')
            return render_template("specific.html", question= ques)

        if ind == 1:
            start=time()
            ans, refs= im_obj.paraqa([ques])
            ###########################
            #json_val=json.loads(refs)
            refs=json2html.convert(json=refs)
            ##########################
            session["refs"]=refs
            session["answer"]=ans
            end=time()
            flash("Response time {:.3f} s".format(end-start), 'info')
            if ans=='':
                flash(f"Sorry unable to answer your query, please contact customer care", 'info')
                return render_template("question.html")
            else:
                return render_template("answer2.html", question=ques, answer=ans, ref=refs)
            #return render_template("question.html")
            #return f"<h1>ParaQA</h1>"
        else:
            flash(f"Sorry unable to answer your query, please contact customer care", 'info')
            return render_template("question.html")
            #return redirect(url_for("options1_data"))
            #return f"<h1>you have entered answer</h1>"
    else:
        return render_template("question.html")




if __name__=="__main__":
    app.run(host='0.0.0.0', port=5100)