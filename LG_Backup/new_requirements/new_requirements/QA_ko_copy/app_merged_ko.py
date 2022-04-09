from flask import Flask , request, render_template, redirect, session, flash
from flask.helpers import url_for
from qa_engine_merged import *
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


def create_answer(jsonfile_str, val):
    answer_ret= eval(jsonfile_str + val)
    new_str=json.dumps(answer_ret, indent=6)
    new_str=re.sub("hph", "-", new_str)
    ###########################
    json_val=json.loads(new_str)
    new_str=json2html.convert(json=json_val)
    return new_str
    
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
            flash("요청한 모델은 지원되지 않습니다", 'info')
            return render_template("index.html")
        else:
            #return redirect(url_for("print_question", qst=ques))
            start= time()
            global im_obj, jsonfile, jsonfile_str  #global object 
            #print("Emb_list:", len(embedding_list))
            im_obj=InteractionModule(embedding_list)
            
            jsonfile=im_obj.get_jsonfile()
            #print("jsonfile:", jsonfile)
            jsonfile_str="jsonfile"
            end=time()
            #####can be accessed from anywhere ###############
            flash(f"You have selected Model No. {model_no}", 'info')
            #flash(f"You have selected Model No. {model_no}", 'info')
            session["modelno"]=model_no
            flash("Response time {:.3f} s".format(end-start), 'info')
            return render_template("question1.html")
            #return render_template("question.html", modelno=model_no)
            #return f"you have entered <h1>{modelno}</h1>"
    else:
        return render_template("index.html")

@app.route("/question", methods=["GET", "POST"])
def handle_data():
    if request.method == "POST":
        ques=request.form.get("question")
        #submit=request.form.get("submit")
        change_model_no=request.form.get("change_model_no")
        #ind= int(submit.split('_')[-1])
        #print(type(ques), ques)
        if change_model_no:
            return redirect(url_for("home_method"))
            #return render_template("index.html")
        if ques =='':
            return render_template("question1.html")
        session["ques"]=ques
        #print("Question:", session["ques"])
        start= time()
        im_obj.answer_question(session["ques"])
        session["options"]= im_obj.keys_option
        session["scores"]=im_obj.keys_score+[0.0]
        print(session["options"])
        print(session["scores"])
        
        if len(im_obj.values_option)==0: #that is no options matched
            ###Para QA not being covered##
            print("No Para QA")
           
            end=time()
            flash("Response time {:.3f} s".format(end-start), 'info')
            
            flash(f"Sorry unable to answer your query, please contact customer care", 'info')
            flash(f"문의에 답변을 드리지 못해 죄송합니다. 고객센터로 연락주세요", 'info')
            return render_template("question1.html")
            
        elif len(im_obj.values_option)==1:
            new_str=create_answer(jsonfile_str, im_obj.values_option[0])
            session["answer"]=new_str
            end=time()
            flash("Response time {:.3f} s".format(end-start), 'info')
            return render_template("answer.html", question= ques, answer=new_str)
        end=time()
        flash("Response time {:.3f} s".format(end-start), 'info')
        return redirect(url_for("options1_data"))
        #return f"<h1>you have entered {ques}</h1>"
    else:
        return render_template("question1.html")




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
            flash(f"옵션을 선택하십시오", 'info')
            return render_template("answer.html", question= ques, answer=session["answer"])

        if ind == 1:
            return render_template("question1.html")
        else:
            start=time()
            print("No Para QA")
            end=time()
            flash("Response time {:.3f} s".format(end-start), 'info')
            
            flash(f"Sorry unable to answer your query, please contact customer care", 'info')
            flash(f"문의에 답변을 드리지 못해 죄송합니다. 고객센터로 연락주세요", 'info')
            return render_template("question1.html")
            

            #return f"<h1>ParaQA</h1>"
    else:
        return render_template("question1.html")



@app.route("/options1", methods=["GET", "POST"])
def options1_data():
    ques= session["ques"]
    opts= session["options"]
    scores= session["scores"]
    if request.method == "POST":
        #eturn redirect(url_for("print_question1"))
        options=request.form.get("options")
        try:
            ind= int(options.split('_')[-1])
        except:
            flash(f"Please Select an OPTION", 'info')
            flash(f"옵션을 선택하십시오", 'info')
            #return render_template("options.html", options= im_obj.keys_option, question= ques, score=im_obj.keys_score+[0.0])
            return render_template("options.html", options= opts, question= ques, score=scores)
        start=time()
        if ind != len(im_obj.keys_option) -1:
            new_str=create_answer(jsonfile_str, im_obj.values_option[ind])
            ###################################################
            ######################################################
            #answer_ret= eval(jsonfile_str + im_obj.values_option[ind])
            #new_str=json.dumps(answer_ret, indent=6)
            #new_str=re.sub("hph", "-", new_str)
            #json_val=json.loads(new_str)
            #new_str=json2html.convert(json=json_val)
            ##########################
            ######################################################
            session["answer"]=new_str
            end=time()
            flash("Response time {:.3f} s".format(end-start), 'info')
            return render_template("answer.html", question= ques, answer=new_str)
        else:
            print("NOT PARA QA")
            end=time()
            flash("Response time {:.3f} s".format(end-start), 'info')
            
            flash(f"Sorry unable to answer your query, please contact customer care", 'info')
            flash(f"문의에 답변을 드리지 못해 죄송합니다. 고객센터로 연락주세요", 'info')
            return render_template("question1.html")
            
            #flash("No matches found", 'info')
        #return redirect(url_for("answer_data"))
        #return f"<h1>you have entered answer {new_str}</h1>"
    else:
        #return render_template("answer.html", options=["jim", "john", "kim"])
        try:
            return render_template("options.html", options= opts, question= ques, score=scores)
        except:
            return render_template("question1.html")







if __name__=="__main__":
    app.run(host='0.0.0.0', port=5300)