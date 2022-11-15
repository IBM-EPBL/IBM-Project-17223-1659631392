from flask import Flask,render_template,request,session,redirect,url_for,flash,jsonify

from werkzeug.security import generate_password_hash, check_password_hash

import ibm_db,bcrypt,requests,io,json

import ibm_boto3
from ibm_botocore.client import Config, ClientError

connection = ibm_db.connect("DATABASE=bludb;HOSTNAME=9938aec0-8105-433e-8bf9-0fbb7e483086.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=32459;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=dhq06480;PWD=RU3oAevR87GjcL1s",'','')

COS_ENDPOINT="https://s3.jp-tok.cloud-object-storage.appdomain.cloud"
COS_API_KEY_ID="Rn7yT8V81grCqj7fP1R33bi9ENOza2XF0wqjoV3XOZQH"
COS_INSTANCE_CRN="crn:v1:bluemix:public:cloud-object-storage:global:a/640be09080b0456c8f013b1b42ceb249:5818c20b-0847-4f5c-b78e-08c75250ff51::"


cos = ibm_boto3.resource("s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_INSTANCE_CRN,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT
)

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route("/",methods=['GET'])
def home():
    if 'email' not in session:
      return redirect(url_for('login'))
    return render_template('index.html')

@app.route("/upload",methods=['GET','POST'])
def upload():
    if 'email' not in session:
      return redirect(url_for('login'))
    if request.method == 'POST':
      imageurl = request.form['URloftheImage']
      if not imageurl:
        render_template('upload.html',error="fill url")
      url="https://api.spoonacular.com/food/images/analyze"
      API_KEY = "c6b26a53ad36401c969cff947ee122d7"
      res = requests.get(url,params={"imageUrl":imageurl,"apiKey":API_KEY})
      print(res,res.content)
      data = json.loads(res.content)
      return render_template('results.html', title="page", jsonfile=json.dumps(data))
    return render_template('upload.html')  

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

@app.route('/uploader',methods=['POST'])
def uploader():
  name_file=request.form['imageURL']
  print("working fine")
  f = request.files['file']
  try:
      part_size = 1024 * 1024 * 5

      file_threshold = 1024 * 1024 * 15

      transfer_config = ibm_boto3.s3.transfer.TransferConfig(
            multipart_threshold=file_threshold,
            multipart_chunksize=part_size
        )

      content = f.read()
      cos.Object('foodbucket', name_file).upload_fileobj(
                Fileobj=io.BytesIO(content),
                Config=transfer_config
            )
      return redirect(url_for('index'))
      

  except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
        return redirect(url_for('index'))

  except Exception as e:
        print("Unable to complete multi-part upload: {0}".format(e))
        return redirect(url_for('index'))

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