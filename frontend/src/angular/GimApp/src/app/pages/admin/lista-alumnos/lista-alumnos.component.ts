import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { UsuariosService } from 'src/app/services/usuarios.service';

@Component({
  selector: 'app-lista-alumnos',
  templateUrl: './lista-alumnos.component.html',
  styleUrls: ['./lista-alumnos.component.css']
})
export class ListaAlumnosComponent implements OnInit{

  usuarios: any[] = [];
  arrayAlumnos: any;
  currentPage:any = 1;
  totalPaginas: number = 0;
  pages: number[] = [];
  searchTerm: string = '';
  isSearching: boolean = false;
  allAlumnos: any[] = []; // Para almacenar todos los alumnos para búsqueda
  
  // Variables para el modal de edición
  editForm: FormGroup;
  selectedAlumno: any = null;
  isModalOpen: boolean = false;

  constructor(
    private usuariosService: UsuariosService,
    private formBuilder: FormBuilder
  ) {
    this.editForm = this.formBuilder.group({
      nombre: ['', Validators.required],
      apellido: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      edad: ['', [Validators.required, Validators.pattern(/^\d+$/), Validators.min(1), Validators.max(120)]],
      dni: ['', [Validators.required, Validators.pattern(/^\d+$/)]]
    });

    // Debug: Suscribirse a los cambios del formulario
    this.editForm.statusChanges.subscribe(status => {
    });
  }

  ngOnInit() {
    this.loadAlumnos(this.currentPage);
  }

  get rol() {
    return localStorage.getItem('rol');
  }

  loadAlumnos(page: any) {
    this.usuariosService.getAlumnos(page).subscribe((data: any) => {
      this.arrayAlumnos = data.alumnos;
      this.currentPage = data.page;
      this.totalPaginas = data.pages;

      this.pages = Array.from({length: this.totalPaginas}, (_, i) => i + 1);
      
      // Cargar todos los alumnos para búsqueda (solo en la primera carga)
      if (page === 1 && this.allAlumnos.length === 0) {
        this.loadAllAlumnos();
      }
    });
  }

  loadAllAlumnos() {
    // Cargar todas las páginas de alumnos para búsqueda
    this.usuariosService.getAlumnos(1).subscribe((data: any) => {
      this.allAlumnos = data.alumnos;
      
      // Si hay más páginas, cargar las siguientes
      if (data.pages > 1) {
        for (let i = 2; i <= data.pages; i++) {
          this.usuariosService.getAlumnos(i).subscribe((pageData: any) => {
            this.allAlumnos = this.allAlumnos.concat(pageData.alumnos);
          });
        }
      }
    });
  }

  searchAlumnos() {
    if (this.searchTerm.trim() === '') {
      this.isSearching = false;
      this.loadAlumnos(1);
      return;
    }

    this.isSearching = true;
    
    // Filtrar por nombre y apellido
    this.arrayAlumnos = this.allAlumnos.filter((alumno: any) => {
      const nombreCompleto = `${alumno.usuario?.nombre} ${alumno.usuario?.apellido}`.toLowerCase();
      const searchLower = this.searchTerm.toLowerCase();
      
      return nombreCompleto.includes(searchLower);
    });
    
    this.currentPage = 1;
    this.totalPaginas = 1;
    this.pages = [1];
  }

  clearSearch() {
    this.searchTerm = '';
    this.isSearching = false;
    this.loadAlumnos(1);
  }


  eliminarAlumno(userId: number, event?: Event) {
    if (event) {
      event.stopPropagation(); // Evitar que se abra el modal
    }
    
    if (confirm('¿Estás seguro de que quieres eliminar este alumno?')) {
      this.usuariosService.deleteUser(userId).subscribe(
        (response) => {
          // Actualizar lista local
          const index = this.arrayAlumnos.findIndex((usuario: { id: number; }) => usuario.id === userId);
          if (index !== -1) {
            this.arrayAlumnos.splice(index, 1);
          }
          
          // También actualizar allAlumnos si está en modo búsqueda
          if (this.isSearching) {
            const allIndex = this.allAlumnos.findIndex((usuario: { id: number; }) => usuario.id === userId);
            if (allIndex !== -1) {
              this.allAlumnos.splice(allIndex, 1);
            }
          }
          
          // Si no estamos en modo búsqueda, recargar la página actual
          if (!this.isSearching) {
            this.loadAlumnos(this.currentPage);
          }
        },
        (error) => {
          console.error('Error al eliminar el alumno:', error);
          alert('Error al eliminar el alumno');
        }
      );
    }
  }

  // Método para suspender/activar alumno
  toggleSuspension(alumno: any, event?: Event) {
    if (event) {
      event.stopPropagation(); // Evitar que se abra el modal
    }
    
    const isSuspended = alumno.usuario?.suspendido;
    const action = isSuspended ? 'activar' : 'suspender';
    const reason = isSuspended ? '¿Estás seguro de que quieres activar este alumno?' : '¿Estás seguro de que quieres suspender este alumno?';
    
    if (confirm(reason)) {
      this.usuariosService.toggleSuspension(alumno.usuario.id, !isSuspended).subscribe({
        next: (response) => {
          // Actualizar el estado local
          alumno.usuario.suspendido = !isSuspended;
          
          // Actualizar en arrayAlumnos
          const index = this.arrayAlumnos.findIndex((a: any) => a.id === alumno.id);
          if (index !== -1) {
            this.arrayAlumnos[index].usuario.suspendido = !isSuspended;
          }
          
          // Actualizar en allAlumnos si está en modo búsqueda
          if (this.isSearching) {
            const allIndex = this.allAlumnos.findIndex((a: any) => a.id === alumno.id);
            if (allIndex !== -1) {
              this.allAlumnos[allIndex].usuario.suspendido = !isSuspended;
            }
          }
          
          const status = !isSuspended ? 'suspendido' : 'activado';
          alert(`Alumno ${status} correctamente`);
        },
        error: (error) => {
          console.error(`Error al ${action} el alumno:`, error);
          alert(`Error al ${action} el alumno`);
        }
      });
    }
  }

  // Método para abrir el modal de edición
  openEditModal(alumno: any, event?: Event) {
    if (event) {
      event.stopPropagation(); // Evitar cualquier propagación de eventos
    }
    
    this.selectedAlumno = alumno;
    
    // Establecer los valores del formulario
    this.editForm.patchValue({
      nombre: alumno.nombre || '',
      apellido: alumno.apellido || '',
      email: alumno.email || '',
      edad: alumno.edad || '',
      dni: alumno.dni || ''
    });
    
    // Marcar todos los campos como tocados para mostrar validaciones
    this.editForm.markAllAsTouched();
    
    
    // Mostrar el modal usando Bootstrap
    const modalElement = document.getElementById('editAlumnoModal');
    if (modalElement) {
      const modal = new (window as any).bootstrap.Modal(modalElement);
      modal.show();
      this.isModalOpen = true;
    }
  }

  // Método para guardar los cambios del alumno
  saveAlumno() {
    if (this.isFormValid() && this.selectedAlumno) {
      const formData = this.editForm.value;
      
      // Actualizar el usuario asociado al alumno
      this.usuariosService.updateUser(this.selectedAlumno.id, formData).subscribe(
        (response) => {
          
          // Actualizar la lista local
          const index = this.arrayAlumnos.findIndex((alumno: any) => alumno.id === this.selectedAlumno.id);
          if (index !== -1) {
            this.arrayAlumnos[index] = { ...this.arrayAlumnos[index], ...formData };
          }
          
          // Cerrar el modal
          this.closeModal();
          
          // Mostrar mensaje de éxito
          alert('Alumno actualizado correctamente');
        },
        (error) => {
          console.error('Error al actualizar el alumno:', error);
          alert('Error al actualizar el alumno');
        }
      );
    }
  }


  // Método para validar el formulario manualmente
  isFormValid(): boolean {
    return this.editForm?.valid ?? false;
  }

  // Método para cerrar el modal
  closeModal() {
    const modalElement = document.getElementById('editAlumnoModal');
    if (modalElement) {
      const modal = (window as any).bootstrap.Modal.getInstance(modalElement);
      if (modal) {
        modal.hide();
      }
    }
    this.isModalOpen = false;
    this.selectedAlumno = null;
    this.editForm.reset();
  }
}

