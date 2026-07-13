# San Mex Invoice Layout

## Descripción
Este módulo proporciona una plantilla de factura QWeb completamente personalizada (PDF) para Odoo 15, adaptada a las necesidades y diseño de SANMEX. Reemplaza el diseño nativo de las facturas e integra la información del comprobante fiscal digital (CFDI) para México.

## Características Principales
* **Diseño Personalizado:** Plantilla estricta en formato A4 con colores corporativos, logotipo de la empresa y estructura de información optimizada.
* **Integración CFDI:** Muestra de forma nativa la cadena original, sellos digitales (SAT y emisor) y código QR del CFDI obtenidos del módulo de localización.
* **Datos Dinámicos:** Información de la empresa (teléfono, correo, sitio web con íconos de FontAwesome), datos del cliente y direcciones extraídos dinámicamente.
* **Datos Bancarios en el Diario:** Agrega campos personalizados en la configuración del diario contable (Banco, Número de Cuenta, Cuenta Clave) para imprimirse automáticamente en las instrucciones de pago de la factura.
* **Detalle de Pagos:** Muestra el historial de pagos realizados a la factura y el saldo pendiente (Importe adeudado).
* **Formato de Papel Específico:** Incluye un `report.paperformat` personalizado para garantizar la correcta renderización y distribución de espacios del PDF con `wkhtmltopdf`.

## Dependencias
* `account` (Módulo base de facturación)
* `cdfi_invoice` (Localización mexicana para facturación electrónica)

## Instalación
1. Coloque el directorio `san_mex_invoice_layout` dentro de su ruta de addons de Odoo 15.
2. Active el Modo Desarrollador en Odoo.
3. Vaya a Aplicaciones > Actualizar lista de aplicaciones.
4. Busque el módulo "San Mex Invoice Layout" e instálelo.

## Configuración
### 1. Datos de la Compañía
Asegúrese de configurar correctamente los datos de la compañía en *Ajustes > Usuarios y Compañías > Compañías*, incluyendo:
* Logotipo de la empresa
* Teléfono
* Correo electrónico
* Sitio web

### 2. Datos Bancarios para Depósito
Para que las instrucciones de pago se impriman correctamente en el PDF de la factura:
1. Vaya a *Facturación > Configuración > Diarios contables*.
2. Seleccione el diario correspondiente (por ejemplo, Transferencias o Banco principal).
3. Vaya a la pestaña **Datos Bancarios** y complete los campos:
   * Banco
   * Número de Cuenta
   * Cuenta Clave