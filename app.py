from flask import Flask,render_template,request,session
import os, uuid,time

from fontTools.subset import save_font
from matplotlib.artist import kwdoc
from pandas.io.sas.sas_constants import file_type_length
from werkzeug.utils import secure_filename
from flask import flash
import document_processor
from document_processor import extract_text
from feature_extractor import extract_ngrams,map_to_taxonomy,normalize_text


app=Flask(__name__,template_folder='templates')

app.secret_key = "your_secret_key"
UPLOAD_FOLDER='uploads'
RESUME_FOLDER=os.path.join(UPLOAD_FOLDER, 'resumes')
JOB_DESC_FOLDER=os.path.join(UPLOAD_FOLDER, 'job_descriptions')

os.makedirs(UPLOAD_FOLDER,exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)
os.makedirs(JOB_DESC_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS={'pdf','docx','txt'}
MAX_FILE_SIZE=16 * 1024 * 1024   #16mb

app.config['UPLOAD_FOLDER']= UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH']=MAX_FILE_SIZE

WEIGHTS = {
    "skills": 2.0,
    "keywords": 1.0,
    "education": 3.0
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower()in ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    ext=filename.rsplit('.',1)[1].lower()
    unique_name=f"{uuid.uuid4()}.{ext}"
    return unique_name

def create_unique_filename_time(filename):
    ext=filename.rsplit('.',1)[1].lower()
    timestamp=str(int(time.time()))  #time in seconds now
    unique_time=f"{timestamp}_{filename}"
    return unique_time

def calculate_match_score(resume_data,job_data):
    score=0
    if not resume_data or not job_data:
        return 0,[],[]
    resume_skills=resume_data.get('skills',[])
    job_skills=job_data.get('skills',[])

    matched_skills=set(resume_skills)&set(job_skills)
    if matched_skills:
       score+=len(matched_skills)*WEIGHTS["skills"]

    resume_keywords=[kw.lower()for kw in resume_data.get('keywords',[])]
    job_keywords=[kw.lower() for kw in job_data.get('keywords',[])]


    matched_keywords=set(resume_keywords)&set(job_keywords)
    if matched_keywords:
       score+=len(matched_keywords)*WEIGHTS['keywords']

    resume_education = resume_data.get("education", [])
    job_education = job_data.get("education", [])

    # Check if any education requirement matches
    education_match = False
    if resume_education and job_education:
        for job_edu in job_education:
            for resume_edu in resume_education:
                if job_edu.lower() in resume_edu.lower() or resume_edu.lower() in job_edu.lower():
                    education_match = True
                    break
            if education_match:
                break
            if education_match:
                break
    if education_match:
        score += WEIGHTS["education"]

    max_possible_score = (len(job_skills) * WEIGHTS["skills"]) + (
            len(job_keywords) * WEIGHTS["keywords"]) + WEIGHTS["education"]

    if max_possible_score <= 0:
        match_percentage = 0
    else:
        match_percentage = (score / max_possible_score) * 100

    return match_percentage, list(matched_skills), list(matched_keywords)

@app.route('/',methods=['GET','POST'])
def welcome():
    return render_template('welcome.html')

@app.route('/upload',methods=["GET","POST"])
def upload():
    if request.method=="POST":
        if 'file' not in request.files or 'file_type' not in request.form:
            flash('Error: Missing file or selection.', "error")
            return render_template('upload.html')

        file=request.files['file']
        file_type=request.form['file_type']

        if file.filename=="":
            flash('Error: no file selected',"error")
            return render_template('upload.html')

        if not allowed_file(file.filename):
            flash('Error:only DOCX,PDF and TXT file are allowed','error')
            return render_template('upload.html')

        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            flash(f'Error: File exceeds maximum size limit of {MAX_FILE_SIZE / 1024 / 1024:.1f}MB', 'error')
            return render_template('upload.html'), 400

        try:
            filename=secure_filename(file.filename)
            unique_filename=generate_unique_filename(filename)

            if file_type=='resume':
                save_folder=RESUME_FOLDER
            elif file_type=='job_description':
                save_folder=JOB_DESC_FOLDER
            else:
                flash('inavlid file type selected','error')
                return render_template('upload.html'),400
            os.makedirs(save_folder,exist_ok=True)
            file_path = os.path.join(save_folder, unique_filename)
            file.save(file_path)  # Save the file securely

            extracted_text=extract_text(file_path)
            session['file_path']=file_path
            session['extracted_text']=extracted_text
            print("extracted text stored in session",session.get('extracted_text'))

            normalized_text=normalize_text(extracted_text)
            extracted_keywords=extract_ngrams(normalized_text,num_keywords=10,ngram_range=(1,3))
            matched_skills=map_to_taxonomy(extracted_keywords)

            session['extracted_keywords']=extracted_keywords
            session['matched_skills']=matched_skills

            text_file_path=file_path+'.txt'
            with open(text_file_path,'w',encoding='utf-8')as text_file:
                text_file.write(extracted_text)

            flash(f"File uploaded successfully: {unique_filename}",'success')
            return render_template('upload.html',extracted_text=extracted_text)

        except Exception as e:
            flash( f"Error:could not save the file.{str(e)}",'error')
            return render_template('upload.html'),500
    extracted_text=session.get('extracted_text','')
    return render_template('upload.html',extracted_text=extracted_text)

@app.route('/results')
def results():
    extracted_text=session.get('extracted_text','')

    resume_data = {
        "text": session.get("extracted_text", ""),
        "keywords": session.get("extracted_keywords", []),
        "skills": session.get("matched_skills", []),
        "education": session.get("education", ""),
    }

    job_data = {
        "text": session.get("job_text", ""),
        "keywords": session.get("job_keywords", []),
        "skills": session.get("job_skills", []),
        "education": session.get("job_education", ""),
    }

    match_score, matched_skills, matched_keywords = calculate_match_score(resume_data, job_data)

    return render_template('results.html',extracted_text=resume_data['text'],matched_skills=matched_skills,matched_keywords=matched_keywords,match_score=match_score)

@app.route('/help')
def help():
    return render_template('help.html')




if __name__=="__main__":
    app.run(host="127.0.0.1", port=5000 ,debug=True)



