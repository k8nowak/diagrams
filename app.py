from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, send_from_directory
from openai import OpenAI
import subprocess

load_dotenv()
api_key = os.getenv('API_KEY')
use_model = 'gpt-4o'

client = OpenAI(api_key=api_key)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure the UPLOAD_FOLDER directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def ensure_latex_document_structure(latex_code):
    # Check if the required elements are present, and add them if missing
    if '\\documentclass' not in latex_code:
        latex_code = '\\documentclass{standalone}\n' + latex_code
    if '\\usepackage' not in latex_code:
        latex_code = '\\usepackage{tikz}\n' + latex_code
    if '\\begin{document}' not in latex_code:
        latex_code = latex_code + '\n\\begin{document}\n'
    if '\\end{document}' not in latex_code:
        latex_code = latex_code + '\n\\end{document}\n'
    return latex_code

@app.route('/', methods=['GET', 'POST'])
def index():
    response = None
    file_path = None
    user_input = ''
    if request.method == 'POST':
        user_input = request.form['user_input']
        prompt = f"Write me a LaTeX file that uses the tikz library, and create code that would precisely and accurately create the mathematical diagram described here: {user_input}. Ensure the document includes \\documentclass{{standalone}}, \\usepackage{{tikz}}, \\begin{{document}}, and \\end{{document}}."
        # Make the API call
        result = client.chat.completions.create(
            model=use_model,
            messages=[
                {"role": "system", "content": "You are an expert at writing LaTeX code using the tikz library. Only reply with the requested code, with no commentary."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        response = result.choices[0].message.content.strip()

        # Debugging: Print the raw response from the API
        print("Raw API response:")
        print(repr(response))  # Use repr to show hidden characters

        # Remove backticks and leading "latex\n" from the response
        response = response.replace("```latex", "").replace("```", "").strip()
        if response.startswith("latex\n"):
            response = response[6:].strip()

        # Ensure the LaTeX code includes all required elements
        response = ensure_latex_document_structure(response)

        # Debugging: Print the final LaTeX content
        print("Final LaTeX content:")
        print(repr(response))  # Use repr to show hidden characters

        # Save the LaTeX code to a .tex file
        latex_file = os.path.join(app.config['UPLOAD_FOLDER'], 'output.tex')
        with open(latex_file, 'w') as f:
            f.write(response)

        # Read back the file content to verify
        with open(latex_file, 'r') as f:
            file_content = f.read()

        # Debugging: Print the content read back from the file
        print("Content read back from the file:")
        print(repr(file_content))  # Use repr to show hidden characters

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

    return render_template('index.html', response=response, file_path=file_path, user_input=user_input)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

