import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { UsuariosService } from 'src/app/services/usuarios.service';

@Component({
  selector: 'app-lista-profesores',
  templateUrl: './lista-profesores.component.html',
  styleUrls: ['./lista-profesores.component.css']
})
export class ListaProfesoresComponent implements OnInit {
  usuarios: any[] = [];
  arrayProfesores: any;
  currentPage:any = 1;
  totalPaginas: number = 0;
  pages: number[] = [];
  searchTerm: string = '';
  isSearching: boolean = false;
  allProfesores: any[] = []; // Para almacenar todos los profesores para búsqueda
  
  // Variables para el modal de edición
  editForm: FormGroup;
  selectedProfesor: any = null;
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
      dni: ['', [Validators.required, Validators.pattern(/^\d+$/)]],
      especialidad: ['', Validators.required]
    });

    // Debug: Suscribirse a los cambios del formulario
    this.editForm.statusChanges.subscribe(status => {
      console.log('Form status:', status);
      console.log('Form valid:', this.editForm.valid);
      console.log('Form errors:', this.editForm.errors);
      console.log('Form value:', this.editForm.value);
    });
  }

  ngOnInit() {
    this.loadProfesores(this.currentPage);
  }

  get rol() {
    return localStorage.getItem('rol');
  }

  loadProfesores(page: any) {
    this.usuariosService.getProfesores(page).subscribe((data: any) => {
      this.arrayProfesores = data.usuarios;
      this.currentPage = data.page;
      this.totalPaginas = data.pages;
      console.log('Pagina actual:', this.currentPage);
      console.log('JSON data:', this.arrayProfesores);
      console.log('Total de paginas:', this.totalPaginas);

      this.pages = Array.from({length: this.totalPaginas}, (_, i) => i + 1);
      
      // Cargar todos los profesores para búsqueda (solo en la primera carga)
      if (page === 1 && this.allProfesores.length === 0) {
        this.loadAllProfesores();
      }
    });
  }

  loadAllProfesores() {
    // Cargar todas las páginas de profesores para búsqueda
    this.usuariosService.getProfesores(1).subscribe((data: any) => {
      this.allProfesores = data.usuarios;
      
      // Si hay más páginas, cargar las siguientes
      if (data.pages > 1) {
        for (let i = 2; i <= data.pages; i++) {
          this.usuariosService.getProfesores(i).subscribe((pageData: any) => {
            this.allProfesores = this.allProfesores.concat(pageData.usuarios);
          });
        }
      }
    });
  }

  searchProfesores() {
    if (this.searchTerm.trim() === '') {
      this.isSearching = false;
      this.loadProfesores(1);
      return;
    }

    this.isSearching = true;
    
    // Filtrar por nombre y apellido
    this.arrayProfesores = this.allProfesores.filter((profesor: any) => {
      const nombreCompleto = `${profesor.nombre} ${profesor.apellido}`.toLowerCase();
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
    this.loadProfesores(1);
  }

  eliminarProfesor(userId: number, event?: Event) {
    if (event) {
      event.stopPropagation(); // Evitar que se abra el modal
    }
    
    if (confirm('¿Estás seguro de que quieres eliminar este profesor?')) {
      this.usuariosService.deleteUser(userId).subscribe(
        (response) => {
          console.log('Usuario eliminado con éxito', userId);
          // Actualizar lista
          const index = this.arrayProfesores.findIndex((usuario: { id: number; }) => usuario.id === userId);
          if (index !== -1) {
            this.arrayProfesores.splice(index, 1);
          }
        }
      );
    }
  }

  // Método para abrir el modal de edición
  openEditModal(profesor: any, event?: Event) {
    if (event) {
      event.stopPropagation(); // Evitar cualquier propagación de eventos
    }
    
    this.selectedProfesor = profesor;
    
    // Establecer los valores del formulario
    // Extraer la especialidad del array r_profesor
    let especialidad = '';
    let profesorId = null;
    if (profesor.r_profesor && profesor.r_profesor.length > 0) {
      especialidad = profesor.r_profesor[0].especialidad || '';
      profesorId = profesor.r_profesor[0].id;
    }
    
    this.editForm.patchValue({
      nombre: profesor.nombre || '',
      apellido: profesor.apellido || '',
      email: profesor.email || '',
      edad: profesor.edad || '',
      dni: profesor.dni || '',
      especialidad: especialidad
    });
    
    // Guardar el ID del profesor para la actualización
    this.selectedProfesor.profesor_id = profesorId;
    
    // Marcar todos los campos como tocados para mostrar validaciones
    this.editForm.markAllAsTouched();
    
    console.log('Profesor seleccionado:', profesor);
    console.log('Formulario después de patchValue:', this.editForm.value);
    console.log('Formulario válido:', this.editForm.valid);
    
    // Mostrar el modal usando Bootstrap
    const modalElement = document.getElementById('editProfesorModal');
    if (modalElement) {
      const modal = new (window as any).bootstrap.Modal(modalElement);
      modal.show();
      this.isModalOpen = true;
    }
  }

  // Método para guardar los cambios del profesor
  saveProfesor() {
    if (this.isFormValid() && this.selectedProfesor) {
      const formData = this.editForm.value;
      
      // Actualizar el usuario asociado al profesor
      this.usuariosService.updateUser(this.selectedProfesor.id, formData).subscribe(
        (response) => {
          console.log('Usuario actualizado con éxito', response);
          
          // Si hay especialidad, actualizar también el profesor
          if (formData.especialidad && this.selectedProfesor.profesor_id) {
            this.usuariosService.updateProfesor(this.selectedProfesor.profesor_id, { especialidad: formData.especialidad }).subscribe(
              (profesorResponse) => {
                console.log('Especialidad del profesor actualizada', profesorResponse);
              },
              (error) => {
                console.error('Error al actualizar especialidad del profesor:', error);
              }
            );
          }
          
          // Actualizar la lista local
          const index = this.arrayProfesores.findIndex((profesor: any) => profesor.id === this.selectedProfesor.id);
          if (index !== -1) {
            // Actualizar los datos del usuario
            this.arrayProfesores[index] = { ...this.arrayProfesores[index], ...formData };
            
            // Actualizar la especialidad en r_profesor si existe
            if (this.arrayProfesores[index].r_profesor && this.arrayProfesores[index].r_profesor.length > 0) {
              this.arrayProfesores[index].r_profesor[0].especialidad = formData.especialidad;
            }
          }
          
          // Cerrar el modal
          this.closeModal();
          
          // Mostrar mensaje de éxito
          alert('Profesor actualizado correctamente');
        },
        (error) => {
          console.error('Error al actualizar el profesor:', error);
          alert('Error al actualizar el profesor');
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
    const modalElement = document.getElementById('editProfesorModal');
    if (modalElement) {
      const modal = (window as any).bootstrap.Modal.getInstance(modalElement);
      if (modal) {
        modal.hide();
      }
    }
    this.isModalOpen = false;
    this.selectedProfesor = null;
    this.editForm.reset();
  }
}

