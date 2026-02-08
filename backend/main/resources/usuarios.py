from flask_restful import Resource
from flask import request, jsonify
from .. import db
from main.models import UsuarioModel
from sqlalchemy import func, desc, asc
from flask_jwt_extended import jwt_required, get_jwt_identity
from main.auth.decorators import role_required

#Defino el recurso usuario
class Usuario(Resource): #A la clase usuario le indico que va a ser del tipo recurso(Resource)
    #obtener recurso
    @jwt_required()
    @role_required(roles = ["admin"])
    def get(self, id):
        usuario = db.session.query(UsuarioModel).get_or_404(id)
        current_identity = get_jwt_identity()
        if current_identity:
            return usuario.to_json_complete()
        else:
            return usuario.to_json()
        
    #eliminar recurso
    @role_required(roles = ["admin"])
    def delete(self, id):
        usuario = db.session.query(UsuarioModel).get_or_404(id)
        db.session.delete(usuario)
        db.session.commit()
        return '', 204
    
    #Modificar el recurso usuario
    @role_required(roles = ["admin"])
    def put(self, id):
        usuario = db.session.query(UsuarioModel).get_or_404(id)
        payload = request.get_json() or {}
        errors, cleaned = UsuarioModel.validate_numeric_fields(payload)
        if errors:
            return {'error': 'Datos inválidos', 'fields': errors}, 400
        data = payload.items()
        for key, value in data:
            if key in cleaned:
                value = cleaned[key]
            setattr(usuario, key, value)
        db.session.add(usuario)
        db.session.commit()
        return usuario.to_json() , 201

#Coleccion de recurso Usuarios
class Usuarios(Resource):
    #obtener lista de los usuarios
    @jwt_required()
    @role_required(roles = ["admin","profesor"])
    def get(self):    
        page = 1
        per_page = 10
        usuarios = db.session.query(UsuarioModel)
        
        if request.args.get('page'):
            page = int(request.args.get('page'))
        if request.args.get('per_page'):
            per_page = int(request.args.get('per_page'))

         ### FILTROS ###
        
        #Busqueda por apellido
        if request.args.get('apellido'):
            usuarios=usuarios.filter(UsuarioModel.apellido.like("%"+request.args.get('apellido')+"%"))
        
        #Busqueda por email
        if request.args.get('email'):
            usuarios=usuarios.filter(UsuarioModel.email.like("%"+request.args.get('email')+"%"))
            
        #Busqueda por DNI
        if request.args.get('dni'):
            usuarios=usuarios.filter(UsuarioModel.dni.like("%"+request.args.get('dni')+"%"))

        #Busqueda por rol
        if request.args.get('rol'):
            usuarios=usuarios.filter(UsuarioModel.rol.like("%"+request.args.get('rol')+"%"))
            
        #Ordeno por edad de menor a mayor
        if request.args.get('sortby_edad'):
            usuarios=usuarios.order_by(asc(UsuarioModel.edad))

        ### FIN FILTROS ####
        
        usuarios = usuarios.paginate(page=page, per_page=per_page, error_out=True, max_per_page=30)

        # Si se está filtrando por rol profesor o alumno, usar to_json_complete para incluir información completa
        if request.args.get('rol') in ['profesor', 'alumno']:
            return jsonify({'usuarios': [usuario.to_json_complete() for usuario in usuarios],
                      'total': usuarios.total,
                      'pages': usuarios.pages,
                      'page': page
                    })
        else:
            return jsonify({'usuarios': [usuario.to_json() for usuario in usuarios],
                      'total': usuarios.total,
                      'pages': usuarios.pages,
                      'page': page
                    })

    def post(self):
        try:
            payload = request.get_json() or {}
            errors, cleaned = UsuarioModel.validate_numeric_fields(payload, required=True)
            if errors:
                return {'error': 'Datos inválidos', 'fields': errors}, 400
            payload.update(cleaned)
            usuario = UsuarioModel.from_json(payload)
            db.session.add(usuario)
            db.session.commit()
            return usuario.to_json(), 201
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint failed: usuario.email' in str(e):
                return {'error': 'El email ya está registrado', 'message': 'Ya existe un usuario con este email'}, 409
            else:
                return {'error': 'Error al crear usuario', 'message': str(e)}, 400

# Recurso para que los usuarios obtengan sus propios datos
class UsuarioActual(Resource):
    @jwt_required()
    def get(self):
        current_identity = get_jwt_identity()
        if current_identity:
            usuario = db.session.query(UsuarioModel).get_or_404(current_identity)
            return usuario.to_json()
        else:
            return {'message': 'Usuario no autenticado'}, 401
    
    @jwt_required()
    def put(self):
        current_identity = get_jwt_identity()
        if current_identity:
            usuario = db.session.query(UsuarioModel).get_or_404(current_identity)
            payload = request.get_json() or {}
            errors, cleaned = UsuarioModel.validate_numeric_fields(payload)
            if errors:
                return {'error': 'Datos inválidos', 'fields': errors}, 400
            data = payload.items()
            for key, value in data:
                # Solo permitir actualizar ciertos campos
                if key in ['nombre', 'apellido', 'email', 'edad']:
                    if key in cleaned:
                        value = cleaned[key]
                    setattr(usuario, key, value)
            db.session.add(usuario)
            db.session.commit()
            return usuario.to_json(), 201
        else:
            return {'message': 'Usuario no autenticado'}, 401



