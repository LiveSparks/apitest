from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import func
import math

app = Flask(__name__)
app.config['DEBUG'] = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:***password***@localhost:5432/apitest'
db = SQLAlchemy(app)

distanceLimit = 2 #distance in Kms

class pincodes(db.Model):
	__tablename__='pincodes'

	key = db.Column(db.String, primary_key=True)
	place_name = db.Column(db.String)
	admin_name1 = db.Column(db.String)
	latitude = db.Column(db.Float)
	longitude = db.Column(db.Float)
	accuracy = db.Column(db.Integer)

	def __repr__(self):
		'''
		data={
			'key':str(self.key),
			'place_name':str(self.place_name),
			'admin_name1':str(self.admin_name1),
			'latitude':self.latitude,
			'longitude':self.longitude,
			'accuracy':self.accuracy
		}
		'''
		return "%r%r%r%r'%r'%r" % (self.key,self.place_name,self.admin_name1,self.latitude,self.longitude,self.accuracy)
		#return data

class geolocation(db.Model):
	__tablename__='geolocation'

	key = db.Column(db.Integer, primary_key=True)
	geometry = db.Column(db.Binary)
	name = db.Column(db.String)
	category = db.Column(db.String)
	parent = db.Column(db.String)

	def __repr__(self):
		return "%r%r%r" % (self.name,self.category,self.parent)

@app.route('/')
def hello_world():
	#data = db.session.query(pincodes).first()
	data = pincodes.query.get('IN/110001')
	msg = getFormatedRow(data)
	return msg


@app.route('/post_location',methods=['POST'])
def post_location():
	if request.method == 'POST':
		key = request.form['pincode']
		place_name = request.form['place_name']
		admin_name1 = request.form['admin_name1']
		latitude = request.form['latitude']
		longitude = request.form['longitude']
		accuracy = request.form['accuracy']


		#return pincode
		data=db.session.query(pincodes).filter_by(key=key).scalar()
		if data is not None:
			msg = 'This Pincode Already Exists!\n'
			msg += str(getFormatedRow(data))
			return msg
		else:
			#data = db.session.query(pincodes).filter_by(place_name=place_name).order_by('ABS(latitude - %f)' % float(latitude))
			#data = pincodes.query.order_by('ABS(latitude - %f)' % float(latitude)).limit(10).all()
			msg = ''
			if(not dataExists(key)):
				return 'You must supply a pincode!'
			if(not dataExists(place_name)):
				return 'You must supply a place name!'
			data = pincodes.query.order_by('(( 3959 * acos( cos( radians(%f) ) * cos( radians( pincodes.latitude ) ) * cos( radians( pincodes.longitude ) - radians(%f) ) + sin( radians(%f) ) * sin( radians( pincodes.latitude ) ) ) )*1.60934)' % (float(latitude),float(longitude),float(latitude))).limit(1).all()
			row = getFormatedRow(data)
			distance = ( 3959 * math.acos( math.cos( math.radians(float(latitude)) ) * math.cos( math.radians( float(row['latitude']) ) ) * math.cos( math.radians( float(row['longitude']) ) - math.radians(float(longitude)) ) + math.sin( math.radians(float(latitude)) ) * math.sin( math.radians( float(row['latitude']) ) ) ) )*1.60934
			if distance < distanceLimit:
				msg += 'A location already exists within '+str(distanceLimit)+'Kms of given coorinates.\n'
				msg += str(row)
				addAllowed=False
			else:
				addAllowed = True
			if(addAllowed):
				newRow = pincodes(
					key=key,
					place_name=place_name,
					admin_name1=formDataFormat(admin_name1),
					latitude=formDataFormat(latitude),
					longitude=formDataFormat(longitude),
					accuracy=formDataFormat(accuracy)
				)
				db.session.add(newRow)
				db.session.commit()
				data = pincodes.query.get(key)
				msg += 'New Data Added\n'
				msg += str(getFormatedRow(data))
			return msg

@app.route('/get_using_self',methods=['GET'])
def get_using_sef():
	try:
		latitude=float(request.args.get('latitude'))
		longitude=float(request.args.get('longitude'))
	except:
		return 'You must supply valid arguments!'

	data = pincodes.query.order_by('(( 3959 * acos( cos( radians(%f) ) * cos( radians( pincodes.latitude ) ) * cos( radians( pincodes.longitude ) - radians(%f) ) + sin( radians(%f) ) * sin( radians( pincodes.latitude ) ) ) )*1.60934)' % (float(latitude),float(longitude),float(latitude))).all()
	data = sort_by_distance(data,latitude,longitude)
	msg = 'Pincodes within 5Kms of given cordinates:\n'
	msg+=str(data)
	return msg

@app.route('/get_using_postgres',methods=['GET'])
def get_using_postgres():
	try:
		latitude=float(request.args.get('latitude'))
		longitude=float(request.args.get('longitude'))
	except:
		return 'You must supply valid arguments!'

	data = pincodes.query.filter('((point(77.216,28.633)<@>point(pincodes.longitude,pincodes.latitude))*1.60934::double precision)<5').order_by('((point(77.216,28.633)<@>point(pincodes.longitude,pincodes.latitude))*1.60934::double precision)').all()
	newList=[]
	for i in data:
		row = getFormatedRow(i)
		newList.append(row['key'])
	msg = 'Pincodes within 5Kms of given cordinates:\n'
	msg += str(newList)
	return msg

@app.route('/get_place',methods=['GET'])
def get_place():
	try:
		latitude=float(request.args.get('latitude'))
		longitude=float(request.args.get('longitude'))
	except:
		return 'You must supply valid arguments!'

	loc='point('+str(longitude)+' '+str(latitude)+')'
	data = geolocation.query.filter(func.st_contains(geolocation.geometry,func.st_geometryfromtext(loc,4326))).all()

	if str(data)=='[]':
		return "Given point doesn't fall under any known location!"
	#data = geolocation.query.limit(1).all()
	row = getFormatedPlace(data)
	msg='The Point falls under:\n'
	msg+=str(row)
	return msg


def sort_by_distance(data,latitude,longitude):
	#recursionAllowed=True
	newList=[]
	for i in data:
		#while(recursionAllowed):
		row=getFormatedRow(i)
		distance = distance = ( 3959 * math.acos( math.cos( math.radians(float(latitude)) ) * math.cos( math.radians( float(row['latitude']) ) ) * math.cos( math.radians( float(row['longitude']) ) - math.radians(float(longitude)) ) + math.sin( math.radians(float(latitude)) ) * math.sin( math.radians( float(row['latitude']) ) ) ) )*1.60934
		if distance < 5:
			newList.append(row['key'])
		else:
			#recursionAllowed=False
			break
	return newList

def getFormatedPlace(data):
	data=str(data)
	data=data.split("'")
	row={
		'name':data[1],
		'category':data[3],
		'parent':data[5]
	}
	return row

def getFormatedRow(data):
	data = str(data)
	data = data.split("'")
	row = {'key':data[1],
		'place_name':data[3],
		'admin_name1':data[5],
		'latitude':data[6],
		'longitude':data[7],
		'accuracy':data[8],
	}
	return row

def formDataFormat(data):
	if data=='NULL':
		return None
	else:
		return data

def dataExists(data):
	if data=='NULL' or data=='':
		return False
	else:
		return True


if __name__ == '__main__':
	app.run()