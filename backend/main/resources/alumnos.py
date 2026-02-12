from flask_restful import Resource
from flask import request, jsonify
from .. import db
from main.models import AlumnoModel, PlanificacionModel, UsuarioModel
from sqlalchemy import func, desc, asc
from main.auth.decorators import role_required
from flask_jwt_extended import jwt_required, get_jwt_identity

class UsuariosAlumnos(Resource):
    #obtener lista de los alumnos
    @jwt_required()
    @role_required(roles = ["admin",'profesor'])
    def get(self):
        page = 1
        per_page = 10
        alumnos = db.session.query(AlumnoModel)
        
        if request.args.get('page'):
            page = int(request.args.get('page'))
        if request.args.get('per_page'):
            per_page = int(request.args.get('per_page'))

        #Busqueda por id
        if request.args.get('id'):
            alumnos=alumnos.filter(AlumnoModel.id.like("%"+request.args.get('id')+"%"))
            
        #Busqueda por id_usuario
        if request.args.get('id_usuario'):
            alumnos=alumnos.filter(AlumnoModel.id_usuario.like("%"+request.args.get('id_usuario')+"%"))
        
        #Busqueda por nro_socio
        if request.args.get('nro_socio'):
            alumnos=alumnos.filter(AlumnoModel.nro_socio.like("%"+request.args.get('nro_socio')+"%"))
            
        #Orden por id_usuario
        if request.args.get('sortby_usuarios'):
            alumnos=alumnos.order_by(desc(AlumnoModel.id_usuario))
        
        #Orden por nro_socio
        if request.args.get('sortby_nro_socio'):
            alumnos=alumnos.order_by(asc(AlumnoModel.nro_socio))

        #Obtener valor paginado
        alumnos = alumnos.paginate(page=page, per_page=per_page, error_out=True, max_per_page=30)


        return jsonify({'alumnos': [alumno.to_json() for alumno in alumnos],
                  'total': alumnos.total,
                  'pages': alumnos.pages,
                  'page': page
                })
    
    @jwt_required()
    @role_required(roles = ['admin', 'profesor'])
    def post(self):
        try:
            planificaciones_ids = request.get_json().get('planificaciones')
            alumno = AlumnoModel.from_json(request.get_json())
            
            if planificaciones_ids:
                planificaciones = PlanificacionModel.query.filter(PlanificacionModel.id.in_(planificaciones_ids)).all()
                alumno.planificaciones.extend(planificaciones)
                
            db.session.add(alumno)
            db.session.commit()
            return alumno.to_json(), 201
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint failed: alumno.nro_socio' in str(e):
                return {'error': 'Número de socio duplicado', 'message': 'Ya existe un alumno con este número de socio'}, 409
            else:
                return {'error': 'Error al crear alumno', 'message': str(e)}, 400

class UsuarioAlumno(Resource): #A la clase usuarioalumno le indico que va a ser del tipo recurso(Resource)
    #obtener recurso
    @jwt_required()
    @role_required(roles = ['admin', 'profesor'])
    def get(self, id):
        alumno = db.session.query(AlumnoModel).get_or_404(id)
        return alumno.to_json()
    
    #eliminar recurso
    @jwt_required()
    @role_required(roles = ['admin', 'profesor'])
    def delete(self, id):
        alumno = db.session.query(AlumnoModel).get_or_404(id)
        db.session.delete(alumno)
        db.session.commit()
        return '', 204
    #Modificar el recurso usuario
    @jwt_required()
    @role_required(roles = ['admin', 'profesor'])
    def put(self, id):
        alumno = db.session.query(AlumnoModel).get_or_404(id)
        data = request.get_json().items()
        for key, value in data:
            setattr(alumno, key, value)
        db.session.add(alumno)
        db.session.commit()
        return alumno.to_json() , 201

class AlumnoByUsuario(Resource):
    """Recurso para que los alumnos obtengan su información por id_usuario"""
    @jwt_required()
    @role_required(roles = ['alumno'])
    def get(self, id_usuario):
        # Buscar el alumno por id_usuario
        alumno = db.session.query(AlumnoModel).filter_by(id_usuario=id_usuario).first()
        
        if not alumno:
            return {'error': 'Alumno no encontrado'}, 404
            
        return alumno.to_json()
