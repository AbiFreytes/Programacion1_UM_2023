import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from "@angular/common/http";
import { Router } from "@angular/router";

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
export class RegisterComponent {
  signupForm!: FormGroup;
  url = '/api'

  constructor (
    private formBuilder: FormBuilder,
    private http : HttpClient,
    private router: Router,
  ) {}

  ngOnInit() {
    this.signupForm = this.formBuilder.group({
      nombre: ['', Validators.required],
      apellido: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      contrasena: ['', Validators.required],
      edad: ['', [Validators.required, Validators.pattern(/^\d+$/), Validators.min(1), Validators.max(120)]],
      dni: ['', [Validators.required, Validators.pattern(/^\d+$/)]],
    })
  }

  signUp(dataLogin:any = {}) {
    // dataSignUp = {nombre: "Abril", apellido: "Freytes", email: "a.f@email.com", contrasena: "hola123"}
    console.log('Registrando nuevo usuario');
    this.http.post(this.url + '/auth/register', this.signupForm.value)
    .subscribe(res=>{
      alert("Solicitud de registro exitosa, recibirá una notificación a su mail al ser confirmada");
      this.signupForm.reset();
      this.router.navigate(['login']);
    },err=>{
      alert("Error de algun tipo");
  })
}
}