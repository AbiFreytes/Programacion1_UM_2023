from .. import db
from datetime import datetime


class Planificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lunes = db.Column(db.String, nullable=False)
    martes = db.Column(db.String, nullable=False)
    miercoles = db.Column(db.String, nullable=False)
    jueves = db.Column(db.String, nullable=False)
    viernes = db.Column(db.String, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relación con alumno específico (muchas planificaciones por alumno)
    id_alumno = db.Column(db.Integer, db.ForeignKey('alumno.id'), nullable=False)
    alumno = db.relationship('Alumno', back_populates='planificaciones')
    
    # Relación con profesor que creó la planificación
    id_profesor = db.Column(db.Integer, db.ForeignKey('profesor.id'), nullable=False)
    profesor = db.relationship('Profesor', backref=db.backref('planificaciones_creadas', lazy='dynamic'))

    def __repr__(self):
        return '<Planificacion: %r >' % (self.id)

    def to_json(self):
        from .alumno import Alumno
        from .profesor import Profesor
        
        alumno = db.session.query(Alumno).get(self.id_alumno)
        profesor = db.session.query(Profesor).get(self.id_profesor)
        
        planificacion_json = {
            'id': self.id,
            'lunes': str(self.lunes),
            'martes': str(self.martes),
            'miercoles': str(self.miercoles),
            'jueves': str(self.jueves),
            'viernes': str(self.viernes),
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_modificacion': self.fecha_modificacion.isoformat() if self.fecha_modificacion else None,
            'id_alumno': self.id_alumno,
            'id_profesor': self.id_profesor,
            'alumno': alumno.to_json() if alumno else None,
            'profesor': profesor.to_json() if profesor else None
        }
        return planificacion_json

    @staticmethod
    def from_json(planificacion_json):
        id = planificacion_json.get('id')
        lunes = planificacion_json.get('lunes')
        martes = planificacion_json.get('martes')
        miercoles = planificacion_json.get('miercoles')
        jueves = planificacion_json.get('jueves')
        viernes = planificacion_json.get('viernes')
        id_alumno = planificacion_json.get('id_alumno')
        id_profesor = planificacion_json.get('id_profesor')
        
        return Planificacion(id=id,
                    lunes=lunes,
                    martes=martes,
                    miercoles=miercoles,
                    jueves=jueves,
                    viernes=viernes,
                    id_alumno=id_alumno,
                    id_profesor=id_profesor
                    )
