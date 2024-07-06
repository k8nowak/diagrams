from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, send_from_directory
from openai import OpenAI
import subprocess

load_dotenv()
api_key = os.getenv('API_KEY')

client = OpenAI(api_key=api_key)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure the UPLOAD_FOLDER directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET', 'POST'])
def index():
    response = None
    file_path = None
    if request.method == 'POST':
        user_input = request.form['user_input']
        prompt = f"Write me a LaTeX file that uses the tikz library, and create code that would precisely and accurately create the mathematical diagram described here: {user_input}"
        # Make the API call
        result = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at writing LaTeX code using the tikz library. Only reply with the requested code, with no commentary."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        response = result.choices[0].message.content.strip()

        # Save the LaTeX code to a .tex file
        latex_file = os.path.join(app.config['UPLOAD_FOLDER'], 'output.tex')
        with open(latex_file, 'w') as f:
            f.write(response)

        # Compile the LaTeX file to PDF
        try:
            subprocess.run(['pdflatex', '-output-directory', app.config['UPLOAD_FOLDER'], latex_file], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error compiling LaTeX: {e}")
        
        # Convert the PDF to SVG
        pdf_file = os.path.join(app.config['UPLOAD_FOLDER'], 'output.pdf')
        svg_file = os.path.join(app.config['UPLOAD_FOLDER'], 'output.svg')
        try:
            subprocess.run(['pdf2svg', pdf_file, svg_file], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error converting PDF to SVG: {e}")

        # Check if the SVG file was created
        if os.path.exists(svg_file):
            file_path = 'output.svg'
        else:
            print("SVG file was not created.")

    return render_template('index.html', response=response, file_path=file_path)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
