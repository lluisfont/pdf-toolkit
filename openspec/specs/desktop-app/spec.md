# desktop-app Specification

## Purpose
Ventana de escritorio (`pdf_toolkit.py`, Tkinter) con una pestaña por herramienta, para usar la fusión y la división de PDF sin la línea de comandos. Cada pestaña reutiliza la lógica de su módulo (`pdf_merge.py`, `pdf_split.py`).

## Requirements

### Requirement: Ventana con pestañas
La aplicación DEBE (SHALL) mostrar una sola ventana con una pestaña por herramienta: «Fusionar» y «Dividir».

#### Scenario: Abrir la aplicación
- **WHEN** el usuario ejecuta `python pdf_toolkit.py` o `pythonw pdf_toolkit.py`
- **THEN** se abre la ventana «PDF Toolkit» con las pestañas Fusionar y Dividir

#### Scenario: Ejecución sin consola
- **WHEN** la aplicación se ejecuta con `pythonw`
- **THEN** todas las funciones trabajan igual, porque ninguna escribe en la consola

### Requirement: Nitidez con escalado de pantalla
En Windows, la aplicación DEBE (SHALL) declararse compatible con el escalado de pantalla (DPI) y ajustar el tamaño inicial de la ventana a ese escalado.

#### Scenario: Pantalla al 125 %
- **WHEN** Windows tiene el escalado de pantalla al 125 %
- **THEN** el texto se ve nítido y la ventana se abre a 1,25 veces su tamaño base (920×580)

### Requirement: Lista de archivos para fusionar
La pestaña Fusionar DEBE (SHALL) permitir montar y ordenar la lista de PDF que se van a fusionar.

#### Scenario: Añadir archivos y carpetas
- **WHEN** el usuario pulsa «Añadir PDF…» o «Añadir carpeta…»
- **THEN** los PDF se añaden al final de la lista mostrando nombre, número de páginas, rango y carpeta
- **AND** los de una carpeta se añaden en orden natural de nombre

#### Scenario: PDF protegido en la lista
- **WHEN** se añade un PDF cifrado
- **THEN** su columna de páginas muestra 🔒 en lugar del número

#### Scenario: Archivo ilegible
- **WHEN** se añade un archivo que no se puede leer como PDF
- **THEN** se avisa y el archivo no se añade

#### Scenario: Reordenar
- **WHEN** el usuario arrastra una fila, usa «▲ Subir» / «▼ Bajar» con una o varias filas seleccionadas, o pulsa «Ordenar A-Z»
- **THEN** el orden de la lista cambia y la fusión respeta ese orden

#### Scenario: Quitar
- **WHEN** el usuario pulsa «Quitar» o la tecla Supr con filas seleccionadas, o «Vaciar»
- **THEN** esas filas, o todas, desaparecen de la lista

### Requirement: Páginas por archivo en la fusión
La pestaña Fusionar DEBE (SHALL) permitir elegir con doble clic qué páginas se toman de cada archivo, con la misma sintaxis de rangos que la línea de comandos, y validarlas contra el número de páginas del archivo.

#### Scenario: Rango válido
- **WHEN** el usuario hace doble clic en una fila y escribe `1-3,5`
- **THEN** la columna Rango muestra `1-3,5` y solo esas páginas se fusionan

#### Scenario: Rango inválido
- **WHEN** el rango tiene un formato incorrecto o pide páginas que el archivo no tiene
- **THEN** se muestra un error y el rango anterior se conserva

#### Scenario: Volver a todas
- **WHEN** el usuario deja el rango vacío
- **THEN** la columna Rango muestra «todas»

### Requirement: Ejecución de la fusión
La pestaña Fusionar DEBE (SHALL) pedir dónde guardar el resultado y NO DEBE (MUST NOT) permitir que el archivo de salida sea uno de los de entrada.

#### Scenario: Fusión correcta
- **WHEN** el usuario pulsa «Fusionar…» y elige un destino
- **THEN** se crea el PDF con las opciones elegidas (marcadores por archivo, contraseña) y se informa del número de páginas
- **AND** mientras trabaja, el botón queda desactivado y la barra de estado muestra el progreso

#### Scenario: Error durante la fusión
- **WHEN** falla la fusión (por ejemplo, falta la contraseña de un PDF protegido)
- **THEN** se muestra el error en un mensaje y la ventana sigue utilizable

### Requirement: Selección del PDF para dividir
La pestaña Dividir DEBE (SHALL) cargar el PDF elegido, pidiendo la contraseña si está cifrado, y mostrar su número de páginas y el texto de su primera página.

#### Scenario: Cargar un PDF
- **WHEN** el usuario pulsa «Elegir…» y abre `diplomas.pdf`
- **THEN** se muestra la ruta y el número de páginas, la carpeta de salida pasa a ser `diplomas_dividido` junto al original y se listan las líneas de texto de la página 1

#### Scenario: PDF sin texto
- **WHEN** la página 1 no tiene texto
- **THEN** la lista indica que la página no tiene texto y sugiere que puede ser un PDF escaneado

### Requirement: Elección del nombre con un clic
En la división hoja a hoja con nombre leído de la página, la pestaña Dividir DEBE (SHALL) permitir elegir la línea del nombre haciendo clic en ella dentro del texto de la página 1, y usar como referencia el texto de la línea anterior.

#### Scenario: Clic en el nombre del alumno
- **WHEN** el usuario hace clic en la línea «María José Fernández», precedida de «Se otorga el presente diploma a»
- **THEN** el campo «Texto antes del nombre» pasa a valer «Se otorga el presente diploma a» y la vista previa muestra el nombre detectado en cada página

#### Scenario: Clic en la primera línea
- **WHEN** la línea elegida es la primera de la página y no tiene línea anterior
- **THEN** se usa la línea en esa misma posición de cada página

#### Scenario: Referencia escrita a mano
- **WHEN** el usuario escribe otro texto de referencia y pulsa «Detectar» o Intro
- **THEN** la vista previa se recalcula con esa referencia

### Requirement: Vista previa de la división
La pestaña Dividir DEBE (SHALL) mostrar, antes de escribir nada, la lista de archivos que se crearán con sus páginas, y permitir cambiar cada nombre con doble clic.

#### Scenario: Páginas sin nombre detectado
- **WHEN** en alguna página no se encuentra el nombre
- **THEN** esa fila aparece en naranja con el nombre numerado y la barra de estado indica cuántas hay

#### Scenario: Renombrar a mano
- **WHEN** el usuario hace doble clic en una fila y escribe un nombre
- **THEN** el nombre se limpia de caracteres no válidos, se le añade `.pdf` y la fila deja de estar en naranja

#### Scenario: Rangos en directo
- **WHEN** en el modo «Por rangos» el usuario escribe los rangos
- **THEN** la vista previa se actualiza con cada pulsación y los rangos no válidos se indican en la barra de estado

### Requirement: Ejecución de la división
La pestaña Dividir DEBE (SHALL) pedir confirmación antes de sobrescribir archivos existentes y ofrecer abrir la carpeta de salida al terminar.

#### Scenario: Archivos existentes
- **WHEN** alguno de los archivos que se van a crear ya existe en la carpeta de salida
- **THEN** se pregunta si sobrescribirlos y, si el usuario responde que no, no se escribe nada

#### Scenario: Nombres repetidos tras renombrar
- **WHEN** después de renombrar a mano dos filas tienen el mismo nombre
- **THEN** antes de escribir se les añade `(2)`, `(3)`… para que no se pisen

#### Scenario: División correcta
- **WHEN** termina la división
- **THEN** la barra de estado indica cuántos archivos se crearon y dónde, y se ofrece abrir la carpeta
