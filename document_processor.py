import os
import fitz
import docx


def extract_from_pdf(pdf_path):
 # getting text from the pdf file
    text=""
    try:
     with fitz.open(pdf_path) as doc:
        for page in doc:
            text+=page.get_text('text')
    except Exception as e:
      print(f"error processing PDF file {pdf_path}:{e}")
    return text


def extract_from_docx(docx_path):
    text=''
    try:
        doc=docx.Document(docx_path)
        text='\n'.join([para.text for para in doc.paragraphs])
    except  Exception as e:
        print(f"error processing DOCX file{docx_path}:{e}")
    return text


def extract_from_txt(txt_path):
    text=''
    try:
        with open(txt_path,'r',encoding="utf-8") as file:
            text=file.read()
    except Exception as  e:
        print(f"error processing TXT file{txt_path}:{e}")
    return text


def extract_text(file_path):
    # now we will be extracting the file according to the need
  if not os.path.exists(file_path):
      print(f"file not found:{file_path}")
      return ""
  ext=file_path.lower().split(".")[-1]
  if ext=='pdf':
        return extract_from_pdf(file_path)
  elif ext=='docx':
        return extract_from_docx(file_path)
  elif ext=='txt':
        return extract_from_txt(file_path)
  else:
        print(f"unsupported file format:{ext}")
        return ""


if __name__=='__main__':
    test_file='sample.pdf'
    extracted_text=extract_text(test_file)
    print('extracted text:',extracted_text[:500])






