from flask import Flask,render_template,request,session,redirect,url_for,flash,jsonify,send_from_directory

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import ibm_db,bcrypt,requests,os,json,time

import ibm_boto3
from ibm_botocore.client import Config, ClientError

connection = ibm_db.connect("DATABASE=bludb;HOSTNAME=9938aec0-8105-433e-8bf9-0fbb7e483086.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=32459;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=dhq06480;PWD=RU3oAevR87GjcL1s",'','')

COS_ENDPOINT="https://s3.tok.ap.cloud-object-storage.appdomain.cloud"
COS_API_KEY_ID="Rn7yT8V81grCqj7fP1R33bi9ENOza2XF0wqjoV3XOZQH"
COS_INSTANCE_CRN="crn:v1:bluemix:public:cloud-object-storage:global:a/640be09080b0456c8f013b1b42ceb249:5818c20b-0847-4f5c-b78e-08c75250ff51:bucket:foodbucket"
QUOTES_API_KEY = "PYJjtF5GfXACVzwHQQZhog==2sCe1sq4OtJew6N0"
FOOD_API_KEY = "c6b26a53ad36401c969cff947ee122d7"

cos = ibm_boto3.client(service_name="s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_INSTANCE_CRN,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT)

UPLOAD_FOLDER = './foods'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


@app.route("/",methods=['GET'])
def home():
    quote="Take care of your body. It is the only place you have to live"
    if 'email' not in session:
      return redirect(url_for('login'))
    category = 'food'
    api_url = 'https://api.api-ninjas.com/v1/quotes?category={}'.format(category)
    response = requests.get(api_url, headers={'X-Api-Key': QUOTES_API_KEY})
    if response.status_code == requests.codes.ok:
      jsonResponse = response.json()
    else:
      print("Error:", response.status_code, response.text)
    return render_template('index.html',todaysquote=jsonResponse[0]['quote'],author=jsonResponse[0]['author'])

# @app.route("/upload",methods=['GET','POST'])
# def upload():
#     if 'email' not in session:
#       return redirect(url_for('login'))
#     if request.method == 'POST':
#       imageurl = request.form['URloftheImage']
#       if not imageurl:
#         render_template('upload.html',error="fill url")
#       url="https://api.spoonacular.com/food/images/analyze"
#       API_KEY = "c6b26a53ad36401c969cff947ee122d7"
#       res = requests.get(url,params={"imageUrl":imageurl,"apiKey":API_KEY})
#       print(res,res.content)
#       data = json.loads(res.content)
#       return render_template('results.html', title="page", jsonfile=json.dumps(data))
#     return render_template('upload.html')  

@app.route("/login", methods=['GET','POST'])
def login():
    error = ''
    if request.method == 'POST':
      email = request.form['usermail']
      password = request.form['password']

      if not email or not password:
        return render_template('login.html',error='Please fill all fields')
      query = "SELECT * FROM users WHERE EMAIL=?"
      stmt = ibm_db.prepare(connection, query)
      ibm_db.bind_param(stmt,1,email)
      ibm_db.execute(stmt)
      isUser = ibm_db.fetch_assoc(stmt)
      print(isUser,password)
      print(isUser['PASSWORD'])
      print(password)

      if not isUser:
        return render_template('login.html',error='Invalid Credentials = '+email, flash_message="True")

      isPasswordMatch = bcrypt.checkpw(password.encode('utf-8'),isUser['PASSWORD'].encode('utf-8'))


      if not isPasswordMatch:
        return render_template('login.html',error='Invalid Credentials'+password+" "+isUser['PASSWORD'])

      session['email'] = isUser['EMAIL']
      flash("You are successfully logged in");
      return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/register')
@app.route("/register",methods=['GET','POST'])
def register():
  if request.method == 'POST':
    email = request.form['email']
    password = request.form['password']
    name = request.form['username']

    if not email or not password or not name:
      return render_template('register.html',error='Please fill all fields')
    
    hash=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

    query = "SELECT * FROM users WHERE EMAIL=?"
    stmt = ibm_db.prepare(connection, query)
    ibm_db.bind_param(stmt,1,email)
    ibm_db.execute(stmt)
    isUser = ibm_db.fetch_assoc(stmt)
    
    if not isUser:
      insert_sql = "INSERT INTO users(EMAIL,PASSWORD,NAME,CREATED_ON) VALUES (?,?,?,CURRENT TIMESTAMP)"
      prep_stmt = ibm_db.prepare(connection, insert_sql)
      ibm_db.bind_param(prep_stmt, 1, email)
      ibm_db.bind_param(prep_stmt, 2, hash)
      ibm_db.bind_param(prep_stmt, 3, name)
      ibm_db.execute(prep_stmt)
      return redirect(url_for('login'))
    else:
      return render_template('register.html', msg='Mail is already in use')

  return render_template('register.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploader',methods=['GET','POST'])
def uploader():
  if 'email' not in session:
      return redirect(url_for('login'))
  if request.method == 'POST':
    file = request.files['file']
    if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            try:
              cos.upload_file(Filename=filename,Bucket='foodbucket',Key=file.filename)
            except Exception as e:
              print(Exception,e)
            else:
              print('File uploaded')
              app.logger.info('File Uploaded')
            # return redirect(COS_ENDPOINT+"/foodbucket/"+file.filename)
              imageurl = COS_ENDPOINT+"/foodbucket/"+file.filename
              url = "https://api.spoonacular.com/food/images/analyze"
              res = requests.get(url,params={"imageUrl":imageurl,"apiKey":FOOD_API_KEY})
              print(res,res.content)
              data = json.loads(res.content)
              app.logger.info('Results Fetched')
              return render_template('results.html', title="page", jsonfile=json.dumps(data))
            # return send_from_directory(app.config['UPLOAD_FOLDER'],filename)
    app.logger.error('testing error log')
    return render_template('upload.html',error='Drag and drop a file or select add Image. TRIED')
  return render_template('upload.html',error='Drag and drop a file or select add Image.')

@app.route('/profile')
def profile():
  if 'email' not in session:
    return redirect(url_for('login'))
  return render_template('profile.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash("You are successfully logged out");
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, port=8000)