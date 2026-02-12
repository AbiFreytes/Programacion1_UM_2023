from flask_restful import Resource
from flask import request, jsonify
from .. import db
from main.models import ProfesorModel, UsuarioModel
from sqlalchemy import func, desc
from flask_jwt_extended import jwt_required, get_jwt_identity
from main.auth.decorators import role_required


class UsuariosProfesores(Resource):
    #obtener lista de los Profesores
    @jwt_required()
    @role_required(roles = ['admin', 'profesor', 'alumno'])
    def get(self):
        page = 1
        per_page = 10
        profesores = db.session.query(ProfesorModel)
        
        if request.args.get('page'):
            page = int(request.args.get('page'))
        if request.args.get('per_page'):
            per_page = int(request.args.get('per_page'))

                ### FILTROS ###
        
        #Busqueda por especialidad
        if request.args.get('especialidad'):
            profesores=profesores.filter(ProfesorModel.especialidad.like("%"+request.args.get('especialidad')+"%"))
        
        #Ordeno por especialidad
        if request.args.get('sortby_especialidad'):
            profesores=profesores.order_by(desc(ProfesorModel.especialidad))
            
        #Ordeno por id de usuario
        if request.args.get('sortby_nrUsuario'):
            profesores=profesores.outerjoin(ProfesorModel.id_usuario).group_by(ProfesorModel.id).order_by(func.count(UsuarioModel.id).desc())
        
        ### FIN FILTROS ####
        
        profesores = profesores.paginate(page=page, per_page=per_page, error_out=True, max_per_page=30)

        profesores_json = [profesor.to_json() for profesor in profesores]
        usuarios_json = []
        for profesor in profesores_json:
            usuario = profesor.get('usuario', {})
            usuario_legacy = {
                **usuario,
                'r_profesor': [{
                    'id': profesor.get('id'),
                    'id_usuario': profesor.get('id_usuario'),
                    'especialidad': profesor.get('especialidad')
                }]
            }
            usuarios_json.append(usuario_legacy)

        return jsonify({'profesores': profesores_json,
                  'usuarios': usuarios_json,
                  'total': profesores.total,
                  'pages': profesores.pages,
                  'page': page
                })
    
    @jwt_required()
    @role_required(roles = ['admin'])
    def post(self):
        try:
            planificaciones_ids = request.get_json().get('planificaciones')
            profesor = ProfesorModel.from_json(request.get_json())
            
            if planificaciones_ids:
                from main.models import PlanificacionModel
                planificaciones = PlanificacionModel.query.filter(PlanificacionModel.id.in_(planificaciones_ids)).all()
                profesor.planificaciones.extend(planificaciones)
                
            db.session.add(profesor)
            db.session.commit()
            return profesor.to_json(), 201
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint failed: profesor.especialidad' in str(e):
                return {'error': 'Especialidad duplicada', 'message': 'Ya existe un profesor con esta especialidad'}, 409
            else:
                return {'error': 'Error al crear profesor', 'message': str(e)}, 400

class UsuarioProfesor(Resource): #A la clase UsuarioProfesor le indico que va a ser del tipo recurso(Resource)
    @jwt_required()
    @role_required(roles = ['admin', 'profesor', 'alumno'])
    def get(self, id):
        profesor = db.session.query(ProfesorModel).get_or_404(id)
        return profesor.to_json()
    
    @jwt_required()
    @role_required(roles = ['admin'])
    def delete(self, id):
        profesor = db.session.query(ProfesorModel).get_or_404(id)
        db.session.delete(profesor)
        db.session.commit()
        return '', 204
    
    @jwt_required()
    @role_required(roles = ['admin'])
    #Modificar el recurso usuario
    def put(self, id):
        profesor = db.session.query(ProfesorModel).get_or_404(id)
        data = request.get_json().items()
        for key, value in data:
            setattr(profesor, key, value)
        db.session.add(profesor)
        db.session.commit()
        return profesor.to_json() , 201

class ProfesorByUsuario(Resource):
    """Recurso para que los profesores obtengan su información por id_usuario"""
    @jwt_required()
    @role_required(roles = ['profesor'])
    def get(self, id_usuario):
        # Buscar el profesor por id_usuario
        profesor = db.session.query(ProfesorModel).filter_by(id_usuario=id_usuario).first()
        
        if not profesor:
            return {'error': 'Profesor no encontrado'}, 404
            
        return profesor.to_json()

class ProfesoresPublicos(Resource):
    """Endpoint público para obtener profesores sin autenticación (para página de inicio)"""
    def get(self):
        page = 1
        per_page = 10
        profesores = db.session.query(ProfesorModel)
        
        if request.args.get('page'):
            page = int(request.args.get('page'))
        if request.args.get('per_page'):
            per_page = int(request.args.get('per_page'))

        ### FILTROS ###
        
        #Busqueda por especialidad
        if request.args.get('especialidad'):
            profesores=profesores.filter(ProfesorModel.especialidad.like("%"+request.args.get('especialidad')+"%"))
        
        #Ordeno por especialidad
        if request.args.get('sortby_especialidad'):
            profesores=profesores.order_by(desc(ProfesorModel.especialidad))
            
        #Ordeno por id de usuario
        if request.args.get('sortby_nrUsuario'):
            profesores=profesores.outerjoin(ProfesorModel.id_usuario).group_by(ProfesorModel.id).order_by(func.count(UsuarioModel.id).desc())
        
        ### FIN FILTROS ####
        
        profesores = profesores.paginate(page=page, per_page=per_page, error_out=True, max_per_page=30)

        return jsonify({'profesores': [profesor.to_json_publico() for profesor in profesores],
                  'total': profesores.total,
                  'pages': profesores.pages,
                  'page': page
                })
