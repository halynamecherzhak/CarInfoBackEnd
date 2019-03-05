import secrets
from functools import wraps
import pyodbc
from flask import Flask, request, Response
from flask_cors import CORS
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

CORS(app)

conn = pyodbc.connect(
    r'DRIVER={ODBC Driver 13 for SQL Server};'
    r'SERVER=DESKTOP-9RUEM2K;'
    r'DATABASE=CarInfoDB;'
    r'UID=carinfo;'
    r'PWD=Aa1111!!;'
    r'MARS_Connection=Yes'
)


def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers['Authorization'].split(' ')[1]
        if not auth or not check_auth(auth):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


def check_auth(token):
    cursor = conn.cursor()
    cursor.execute("exec CheckToken '" + token + "'")
    for row in cursor.fetchall():
        return row[0]


class Register(Resource):
    def post(self):
        data = request.form.to_dict(flat=False)
        email = data['Email'][0]
        password = data['Password'][0]
        full_name = data['FirstName'][0] + ' ' + data['LastName'][0]
        cursor = conn.cursor()
        cursor.execute("exec CreateUser '" + email + "', '" + password + "', '" + full_name + "'")
        conn.commit()
        return 1


class Token(Resource):
    def post(self):
        data = request.form.to_dict(flat=False)
        email = data['username'][0]
        password = data['password'][0]
        cursor = conn.cursor()
        command = ("exec CheckUserInfo '" + email + "', '" + password + "'")
        cursor.execute(command)
        user_id = cursor.fetchone()[0]
        if user_id > 0:
            token = secrets.token_hex(20)
            command = ("exec InsertUserToken '" + token + "', " + str(user_id))
            cursor.execute(command)
            conn.commit()
            return {"access_token": token, 'expires_in': 360000}
        else:
            return Response(
                'Could not verify your credentials', 405,
                {'WWW-Authenticate': 'Basic realm="Login Required"'})


class TopBrands(Resource):
    def get(self):
        cursor = conn.cursor()
        cursor.execute("exec GetTopFourBrands")
        desc = cursor.description
        column_names = [col[0] for col in desc]
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(column_names, row)))
        return result


class Brands(Resource):
    def get(self):
        cursor = conn.cursor()
        cursor.execute("exec GetBrands")
        desc = cursor.description
        column_names = [col[0] for col in desc]
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(column_names, row)))
        return result


class Brand(Resource):
    def get(self):
        cursor = conn.cursor()
        brand_id = request.args.get('brandId')
        cursor.execute("exec GetBrandById @BrandId=" + brand_id)
        desc = cursor.description
        column_names = [col[0] for col in desc]
        result = []
        for row in cursor.fetchall():
            return dict(zip(column_names, row))


class TopModels(Resource):
    def get(self):
        cursor = conn.cursor()
        brand_id = request.args.get('brandId')
        cursor.execute("exec GetBrandTopModels @BrandId=" + brand_id)
        desc = cursor.description
        column_names = [col[0] for col in desc]
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(column_names, row)))
        return result


class Models(Resource):
    def get(self):
        cursor = conn.cursor()
        brand_id = request.args.get('brandId')
        cursor.execute("exec GetBrandModels @BrandId=" + brand_id)
        desc = cursor.description
        column_names = [col[0] for col in desc]
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(column_names, row)))
        return result


class Model(Resource):
    def get(self):
        cursor = conn.cursor()
        model_id = request.args.get('modelId')
        cursor.execute("exec GetModelById @ModelId=" + model_id)
        desc = cursor.description
        column_names = [col[0] for col in desc]
        result = {}
        for row in cursor.fetchall():
            result = dict(zip(column_names, row))
        result['Photos'] = result['Photos'].split(' ')
        return result


class UserFavoriteModel(Resource):
    @requires_auth
    def get(self):
        model_id = request.args.get('modelId')
        token = request.headers['Authorization'].split(' ')[1]
        cursor = conn.cursor()
        cursor.execute("exec GetUserIdByToken '" + token + "'")
        result = cursor.fetchone()
        user_id = result[0]
        cursor = conn.cursor()
        cursor.execute("exec CheckExistFavoriteUserModel " + str(user_id) + ", " + model_id)
        result = cursor.fetchone()[0]
        return result

    @requires_auth
    def post(self):
        model_id = request.args.get('modelId')
        token = request.headers['Authorization'].split(' ')[1]
        cursor = conn.cursor()
        cursor.execute("exec GetUserIdByToken '" + token + "'")
        result = cursor.fetchone()
        user_id = result[0]
        cursor = conn.cursor()
        cursor.execute("exec SetUserFavoriteModel " + str(user_id) + ", " + model_id)
        conn.commit()
        return 1

    @requires_auth
    def delete(self):
        model_id = request.args.get('modelId')
        token = request.headers['Authorization'].split(' ')[1]
        cursor = conn.cursor()
        cursor.execute("exec GetUserIdByToken '" + token + "'")
        result = cursor.fetchone()
        user_id = result[0]
        cursor = conn.cursor()
        cursor.execute("exec DeleteUserFavoriteModel " + str(user_id) + ", " + model_id)
        conn.commit()
        return 1


class UserFavoriteModelIds(Resource):
    def get(self):
        token = request.headers['Authorization'].split(' ')[1]
        cursor = conn.cursor()
        cursor.execute("exec GetUserIdByToken '" + token + "'")
        result = cursor.fetchone()
        user_id = result[0]
        cursor = conn.cursor()
        cursor.execute("exec GetUsersFavoriteModelIds " + str(user_id))
        result = []
        for row in cursor.fetchall():
            result.append(row[0])
        return result


api.add_resource(TopBrands, '/GetTopFourBrands')
api.add_resource(Brands, '/GetBrands')
api.add_resource(Brand, '/GetBrandById')
api.add_resource(TopModels, '/GetTopBrandModels')
api.add_resource(Models, '/GetModels')
api.add_resource(Model, '/GetModelById')
api.add_resource(Register, '/Register')
api.add_resource(Token, '/Token')
api.add_resource(UserFavoriteModel, '/UserFavoriteModel')
api.add_resource(UserFavoriteModelIds, '/UserFavoriteModelIds')

if __name__ == '__main__':
    app.run()
