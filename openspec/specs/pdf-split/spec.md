# pdf-split Specification

## Purpose
Dividir un PDF en varios: hoja a hoja (por ejemplo, un diploma por alumno, nombrado con el nombre que aparece en la página) o por rangos de páginas. La lógica vive en `pdf_split.py`, que también ofrece la línea de comandos.

## Requirements

### Requirement: División hoja a hoja numerada
La herramienta DEBE (SHALL) poder crear un PDF por cada página, numerado con el nombre del documento original y un número de al menos tres cifras.

#### Scenario: Diplomas numerados
- **WHEN** el usuario ejecuta `python pdf_split.py diplomas.pdf --hojas` sobre un PDF de 5 páginas
- **THEN** se crean `diplomas_001.pdf` a `diplomas_005.pdf`, cada uno con una página

### Requirement: Nombre leído de la propia página
La herramienta DEBE (SHALL) poder nombrar cada archivo de la división hoja a hoja con un texto leído de esa página (por ejemplo, el nombre del alumno de un diploma), localizado mediante un texto de referencia que aparece justo antes.

#### Scenario: Nombre en la línea siguiente a la referencia
- **WHEN** la página contiene la línea «Se otorga el presente diploma a» y en la línea siguiente «María José Fernández»
- **AND** el usuario indica `--nombre-tras "Se otorga el presente diploma a"`
- **THEN** el archivo de esa página se llama `María José Fernández.pdf`

#### Scenario: Nombre en la misma línea que la referencia
- **WHEN** la página contiene «Certificado otorgado a: Luis Gómez, con aprovechamiento.» y la referencia es «otorgado a»
- **THEN** el nombre es lo que sigue a la referencia hasta la primera coma: `Luis Gómez`

#### Scenario: Comparación flexible
- **WHEN** la referencia difiere del texto de la página solo en mayúsculas o en espacios repetidos
- **THEN** la referencia se encuentra igualmente

#### Scenario: Página sin la referencia
- **WHEN** una página no contiene el texto de referencia
- **THEN** esa página no recibe nombre y su archivo se numera
- **AND** se avisa de qué páginas se han numerado

#### Scenario: PDF sin texto
- **WHEN** el PDF es una imagen escaneada sin texto
- **THEN** ninguna página recibe nombre y todas se numeran

### Requirement: Consulta del texto de una página
La herramienta DEBE (SHALL) mostrar, con `--ver-texto N`, las líneas de texto de la página N numeradas, para que el usuario elija el texto de referencia.

#### Scenario: Ver la página 1
- **WHEN** el usuario ejecuta `python pdf_split.py diplomas.pdf --ver-texto 1`
- **THEN** se listan las líneas no vacías de la página 1 con su número y no se crea ningún archivo

### Requirement: Nombres de archivo válidos y únicos
La herramienta DEBE (SHALL) producir nombres de archivo válidos en Windows y distintos entre sí.

#### Scenario: Caracteres no permitidos
- **WHEN** el nombre leído contiene caracteres no válidos en Windows (`< > : " / \ | ? *`)
- **THEN** cada uno se sustituye por « - » y se eliminan los espacios sobrantes (`Pedro O'Connor / Ruiz` → `Pedro O'Connor - Ruiz.pdf`)

#### Scenario: Nombres repetidos
- **WHEN** dos páginas tienen el mismo nombre, sin distinguir mayúsculas
- **THEN** el segundo archivo se llama `Ana López (2).pdf`, el tercero `(3)` y así sucesivamente

#### Scenario: Nombres largos
- **WHEN** el nombre leído supera los 150 caracteres
- **THEN** se recorta a 150 caracteres

### Requirement: División por rangos
La herramienta DEBE (SHALL) crear un PDF por cada rango de una lista separada por comas, con páginas numeradas desde 1.

#### Scenario: Tres rangos
- **WHEN** el usuario ejecuta `python pdf_split.py diplomas.pdf --rangos "1-2, 3, 4-"` sobre un PDF de 5 páginas
- **THEN** se crean `diplomas_pag_1-2.pdf` (2 páginas), `diplomas_pag_3.pdf` (1 página) y `diplomas_pag_4-5.pdf` (2 páginas)

#### Scenario: Rango fuera de límites
- **WHEN** un rango pide páginas que el documento no tiene
- **THEN** la herramienta termina con un error que indica el rango y el número de páginas, sin crear archivos

### Requirement: Carpeta de salida y sobrescritura
La herramienta DEBE (SHALL) guardar los archivos en `<nombre>_dividido` junto al PDF original, salvo que se indique otra carpeta con `-d`, y NO DEBE (MUST NOT) sobrescribir archivos existentes sin `-f`.

#### Scenario: Carpeta por defecto
- **WHEN** el usuario divide `C:\cursos\diplomas.pdf` sin indicar carpeta
- **THEN** los archivos se crean en `C:\cursos\diplomas_dividido`, que se crea si no existe

#### Scenario: Archivos existentes
- **WHEN** alguno de los archivos que se van a crear ya existe y no se usa `-f`
- **THEN** la herramienta termina con un error que indica cuántos existen, sin escribir nada

### Requirement: PDF protegidos con contraseña
La herramienta DEBE (SHALL) abrir un PDF cifrado con la contraseña de `--password` y terminar con un error si falta o es incorrecta.

#### Scenario: Contraseña incorrecta
- **WHEN** el PDF está cifrado y la contraseña falta o no es correcta
- **THEN** la herramienta termina con un error que nombra el archivo, sin crear archivos
