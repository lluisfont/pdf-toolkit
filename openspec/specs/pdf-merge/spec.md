# pdf-merge Specification

## Purpose
Unir varios PDF en un único documento, en el orden que elige el usuario, pudiendo tomar solo algunas páginas de cada archivo. La lógica vive en `pdf_merge.py`, que también ofrece la línea de comandos.

## Requirements

### Requirement: Fusión en el orden indicado
La herramienta DEBE (SHALL) crear un único PDF con las páginas de los archivos de entrada en el mismo orden en que se indican.

#### Scenario: Tres archivos
- **WHEN** el usuario ejecuta `python pdf_merge.py a.pdf b.pdf c.pdf -o resultado.pdf`
- **THEN** `resultado.pdf` contiene las páginas de `a.pdf`, después las de `b.pdf` y después las de `c.pdf`
- **AND** se informa del número de páginas tomadas de cada archivo y del total

#### Scenario: Sin archivo de salida indicado
- **WHEN** el usuario no indica `-o`
- **THEN** el resultado se guarda como `fusionado.pdf` en la carpeta actual

### Requirement: Carpetas como entrada
La herramienta DEBE (SHALL) aceptar carpetas como entrada y añadir todos los PDF que contienen, en orden natural de nombre por defecto.

#### Scenario: Orden natural
- **WHEN** la carpeta contiene `doc1.pdf`, `doc2.pdf` y `doc10.pdf`
- **THEN** se fusionan en el orden `doc1`, `doc2`, `doc10`

#### Scenario: Orden por fecha
- **WHEN** el usuario añade `--orden fecha`
- **THEN** los PDF de la carpeta se ordenan por fecha de modificación, del más antiguo al más reciente

#### Scenario: La salida está dentro de la carpeta de entrada
- **WHEN** el archivo de salida está en la carpeta que se va a fusionar
- **THEN** ese archivo no se incluye como entrada

#### Scenario: Carpeta sin PDF
- **WHEN** una carpeta indicada no contiene ningún PDF
- **THEN** se muestra un aviso y se continúa con el resto de entradas

### Requirement: Rangos de páginas por archivo
La herramienta DEBE (SHALL) permitir elegir qué páginas se toman de cada archivo añadiendo `:rango` a su nombre, con páginas numeradas desde 1.

#### Scenario: Sintaxis de rangos
- **WHEN** el usuario indica `informe.pdf:1-3,5,8-`
- **THEN** se toman las páginas 1 a 3, la 5 y de la 8 hasta el final
- **AND** `-3` significa de la 1 a la 3

#### Scenario: Reordenar o repetir páginas
- **WHEN** el usuario indica `doc.pdf:3,1`
- **THEN** la página 3 va antes que la 1 en el resultado

#### Scenario: Ruta de Windows con letra de unidad
- **WHEN** el usuario indica `C:\carpeta\doc.pdf:2-3`
- **THEN** la letra de unidad no se confunde con el separador del rango y se toman las páginas 2 y 3

#### Scenario: Rango fuera de límites
- **WHEN** el rango pide una página que el documento no tiene
- **THEN** la herramienta termina con un error que indica el rango y el número de páginas del documento
- **AND** no se crea el archivo de salida

### Requirement: Marcadores por archivo de origen
La herramienta DEBE (SHALL) añadir, con la opción `--marcadores`, un marcador por cada archivo de origen con su nombre sin extensión; sin esa opción DEBE (SHALL) conservar los marcadores que ya traían los archivos.

#### Scenario: Con marcadores
- **WHEN** el usuario fusiona `doc1.pdf` y `doc2.pdf` con `--marcadores`
- **THEN** el índice del PDF resultante tiene las entradas `doc1` y `doc2`, cada una apuntando a la primera página de su archivo

### Requirement: PDF protegidos con contraseña
La herramienta DEBE (SHALL) abrir los PDF cifrados con la contraseña de `--password` y NO DEBE (MUST NOT) fusionar un PDF cifrado sin una contraseña válida.

#### Scenario: Sin contraseña
- **WHEN** una entrada está cifrada y no se indica contraseña, o es incorrecta
- **THEN** la herramienta termina con un error que nombra el archivo y sugiere `--password`

#### Scenario: Con contraseña correcta
- **WHEN** se indica la contraseña correcta con `--password`
- **THEN** las páginas de ese PDF se incluyen en el resultado

### Requirement: Protección del archivo de salida
La herramienta NO DEBE (MUST NOT) sobrescribir un archivo existente salvo que se indique `-f`.

#### Scenario: La salida ya existe
- **WHEN** el archivo de salida ya existe y no se usa `-f`
- **THEN** la herramienta termina con un error sin modificar el archivo

#### Scenario: Extensión de la salida
- **WHEN** el nombre de salida no termina en `.pdf`
- **THEN** se le añade la extensión `.pdf`

### Requirement: Progreso sin depender de la consola
La función de fusión DEBE (SHALL) informar del progreso mediante una función `informar` que recibe como parámetro, para poder usarse desde la ventana ejecutada sin consola.

#### Scenario: Uso desde la ventana
- **WHEN** la ventana llama a la fusión con su propia función `informar`
- **THEN** los mensajes de progreso se muestran en la barra de estado y nada se escribe en la consola
