

from flask import Flask,render_template,request,session
import os, uuid,time

from werkzeug.utils import secure_filename
from flask import flash

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
#
# def create_unique_filename_time(filename):
#     ext=filename.rsplit('.',1)[1].lower()
#     timestamp=str(int(time.time()))  #time in seconds now
#     unique_time=f"{timestamp}_{filename}"
#     return unique_time

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
    education_match = any(job_edu.lower() in resume_edu.lower() for job_edu in job_education for resume_edu in resume_education)

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
        if 'resume_file' not in request.files or 'job_file' not in request.files:
            flash('Error: Missing file or selection. Please upload both resume and job description files.', "error")
            return render_template('upload.html')
        resume_file = request.files['resume_file']
        job_file = request.files['job_file']

        if resume_file.filename == "" or job_file.filename == "":
            flash("Error: Both files must be selected.", "error")
            return render_template('upload.html')

        if not allowed_file(resume_file.filename) or not allowed_file(job_file.filename):
            flash("Error: Only PDF, DOCX, and TXT files are allowed.", "error")
            return render_template('upload.html')


        resume_filename=generate_unique_filename(resume_file.filename)
        job_unique_filename=generate_unique_filename(job_file.filename)

        resume_path = os.path.join(RESUME_FOLDER, resume_filename)
        job_path = os.path.join(JOB_DESC_FOLDER, job_unique_filename)

        resume_file.save(resume_path)
        job_file.save(job_path)

        try:
            resume_text = extract_text(resume_path)
            job_text = extract_text(job_path)

        except Exception as e:
            flash(f"Error saving files: {str(e)}", "error")
            return render_template('upload.html')
        try:
            if not os.path.exists(resume_path) or os.path.getsize(resume_path) == 0:
                flash("Error: Missing file or selection. Resume file could not be saved correctly.", "error")
                return render_template('upload.html')

            if not os.path.exists(job_path) or os.path.getsize(job_path) == 0:
                flash("Error: Missing file or selection. Job description file could not be saved correctly.", "error")
                return render_template('upload.html')

            resume_text = extract_text(resume_path)
            job_text = extract_text(job_path)

            # Check if text extraction was successful
            if not resume_text or not job_text:
                flash("Error: Could not extract text from uploaded files. Please ensure files contain readable text.","error")
                return render_template('upload.html')

            normalized_resume = normalize_text(resume_text)
            normalized_job = normalize_text(job_text)

            resume_keywords=extract_ngrams(normalized_resume,num_keywords=10,ngram_range=(1,3))
            job_keywords=extract_ngrams(normalized_job,num_keywords=10,ngram_range=(1,3))

            matched_resume_skills=map_to_taxonomy(resume_keywords)
            matched_job_skills=map_to_taxonomy(job_keywords)

            resume_education=[]
            job_education=[]
            session['resume_text']=resume_text
            session['job_text']=job_text
            session['resume_keywords'] = resume_keywords
            session['job_keywords'] = job_keywords
            session['resume_skills'] = matched_resume_skills
            session['job_skills'] = matched_job_skills
            session['resume_education'] = resume_education
            session['job_education'] = job_education


            flash("Files uploaded and processed successfully!", "success")
            resume_data = {
                "text": resume_text,
                "keywords": resume_keywords,
                "skills": matched_resume_skills,
                "education": resume_education,
            }

            job_data = {
                "text": job_text,
                "keywords": job_keywords,
                "skills": matched_job_skills,
                "education": job_education,
            }
            match_score, matched_skills, matched_keywords = calculate_match_score(resume_data, job_data)

            return render_template("upload.html", resume_text=resume_text, job_text=job_text, matched_resume_skills=matched_resume_skills, matched_job_skills=matched_job_skills,match_score=match_score,matched_skills=matched_skills,matched_keywords=matched_keywords)
        except Exception as e:
            flash(f"Error processing files: {str(e)}", "error")
            return render_template('upload.html')

    return render_template('upload.html')


@app.route('/results')
def results():
    # extracted_text=session.get('extracted_text','')

    resume_data = {
        "text": session.get("resume_text", ""),
        "keywords": session.get("resume_keywords", []),
        "skills": session.get("resume_skills", []),
        "education": session.get("resume_education", ""),
    }

    job_data = {
        "text": session.get("job_text", ""),
        "keywords": session.get("job_keywords", []),
        "skills": session.get("job_skills", []),
        "education": session.get("job_education", ""),
    }

    match_score, matched_skills, matched_keywords = calculate_match_score(resume_data, job_data)

    return render_template('results.html',resume_text=resume_data['text'],job_text=job_data['text'] ,matched_skills=matched_skills,matched_keywords=matched_keywords,match_score=match_score)

@app.route('/help')
def help():
    return render_template('help.html')




if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000 ,debug=True)



