# This will contain functions to identify skills and other important elements
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.stem import PorterStemmer,WordNetLemmatizer
from nltk.tokenize import word_tokenize

nltk.download('punkt_tab')
nltk.download('wordnet')

stemmer=PorterStemmer()
lemmatizer=WordNetLemmatizer()

SKILLS_DATABASE={
    'programming':['python','java','C++','javascript','SQL','R'],
    'data science':['machine learning','deep learning','data analysis','tensorflow','pandas','numpy'],
    "web development": ["HTML", "CSS", "JavaScript", "React", "Flask", "Django"],
    "cloud computing": ["AWS", "Azure", "Google Cloud", "Docker", "Kubernetes"],
    "soft skills": ["Communication", "Teamwork", "Leadership", "Problem Solving"]
}
SKILL_SYNONYMS={
    "ml": "machine learning",
    "deep learning models": "deep learning",
    "ai": "artificial intelligence",
    "data viz": "data visualization",
    "nlp": "natural language processing"
}
RESUME_JOB_DESC= {
    "resume": {
            "text": "Extracted resume text...",
            "keywords": ["machine learning", "deep learning", "Python", "TensorFlow"],
            "skills": ["Python", "TensorFlow", "Keras", "NLP"],
            "education": "Master's in Computer Science"
   },
    "job_description": {
        "text": "Extracted job description text...",
        "keywords": ["data science", "Python", "machine learning", "NLP"],
        "skills": ["Python", "NLP", "Data Science"],
        "education": "Bachelor's in Computer Science"
   }
}


def map_to_taxonomy(extracted_skills):
    matched_skills=[]
    for skill in extracted_skills:
        skill_lower=skill.lower()
        normalized_skill=SKILL_SYNONYMS.get(skill_lower,skill_lower)
        for category,skills_list in SKILLS_DATABASE.items():
            if normalized_skill in skills_list:
                matched_skills.append((skill,category))
                break
    return matched_skills

def normalize_text(text):

    text=text.lower()
    words=word_tokenize(text)
    normalize_words=[lemmatizer.lemmatize(stemmer.stem(word)) for word in words]
    return ' '.join(normalize_words)

def extract_keywords(text,num_keywords=5):
    documents=[text]
    vectorizer=TfidfVectorizer(stop_words='english',ngram_range=(1,2))
    tfidf_matrix=vectorizer.fit_transform(documents)
    feature_names=vectorizer.get_feature_names_out()
    scores=tfidf_matrix.toarray().flatten()
    sorted_indices=scores.argsort()[::-1]
    top_keywords=[feature_names[i] for i in sorted_indices[:num_keywords]]
    return top_keywords

def extract_ngrams(text,num_keywords=5,ngram_range=(2,3)):
    documents=[text]
    vectorizer=TfidfVectorizer(stop_words='english',ngram_range=ngram_range)
    tfidf_matrix=vectorizer.fit_transform(documents)
    feature_names=vectorizer.get_feature_names_out()
    scores=tfidf_matrix.toarray().flatten()
    sorted_indices=scores.argsort()[::-1]
    top_ngrams=[feature_names[i] for i in sorted_indices[:num_keywords]]
    return top_ngrams

def extracted_technical_skills(text,skills_list):
    skills_found=[skill for skill in skills_list if skill.lower() in text.lower()]
    return skills_found

def extract_soft_skills(text,soft_skills_list):
    soft_skills_found=[skill for skill in soft_skills_list if skill.lower()in text.lower()]
    return soft_skills_found

def extract_education(text):
  degree_pattern=r"(Bachelor|Master|PhD|B\.Sc|M\.Sc|B\.Tech|M\.Tech)[\w\s]+"
  matches=re.findall(degree_pattern,text,re.IGNORECASE)
  return matches

if __name__=='__main__':
    resume_text='i have experience in python,machine learning,and flask development, i also have strong communication skills'
    print("keywords extracted:",extract_keywords(resume_text,num_keywords=5))

    skills_list = ['Python', 'machine learning', 'SQl', 'tensorflow', 'flask']
    resume_text = 'i have experience in python,machine learning,and flask development, i also have strong communication skills'
    print('technical skills found:',extracted_technical_skills(resume_text,skills_list))

    soft_skills_list = ['Communication Skills', 'Leadership & Management', ' Teamwork & Collaboration',
                        'Problem-Solving & Critical Thinking', 'Time Management & Organization',
                        'Adaptability & Flexibility', 'Customer Service & Interpersonal Relations',
                        ' Work Ethic & Attitude']
    resume_text='having a strong work experience'
    print("soft skills found",extract_soft_skills(resume_text,soft_skills_list))

    resume_text="I have a Bachelor's degree in Computer Science and an M.Sc in Data Science."
    print(extract_education(resume_text))

    extracted_keywords=extract_ngrams(resume_text,num_keywords=5,ngram_range=(2,3))

    test_skills = ['Python', 'machine learning', 'leadership', 'AWS', 'ML']
    mapped_skills=map_to_taxonomy(test_skills)
    print('mapped_skills',mapped_skills)

    text_sample='I am analyzing data and running machine learning models.'
    normalized_text=normalize_text(text_sample)
    print(normalized_text)
