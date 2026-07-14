# Módulo de Personalizaciones para San Mex Company

Este módulo de Odoo 15 introduce personalizaciones específicas para la empresa San Mex, enfocándose en el flujo de trabajo de compras.

## Características

- **Informe de Análisis de Proveedores ("Provider Group"):**
  - Se añade un nuevo informe accesible desde el menú **Compras > Informes > Grupo de Proveedores**.
  - El informe se basa en las **líneas de pedido de compra**, ofreciendo una vista detallada de cada producto comprado.
  - **Columnas Principales:** Muestra información clave como el Pedido de Compra, Producto, Descripción, Cantidad, Precio Unitario, Proveedor, Fecha del Pedido y la Nota Interna.
  - **Totales Financieros:** Incluye una fila de sumatoria para el "Subtotal sin Impuestos" y el "Total".
  - **Filtros Avanzados:** Permite filtrar por los diferentes estados de la orden de compra (Solicitud de cotización, Orden de Compra, Bloqueado, etc.) y por los distintos tipos de pago personalizados.
  - **Agrupación Dinámica:** Por defecto, los registros se agrupan por `Mes del Pedido > Proveedor > Pedido de Compra > Tipo de Pago`. Se pueden utilizar otras agrupaciones como Producto o Cuenta Analítica.

- **Orden de Compra Excepcional:**
  - Añade un campo booleano `exceptional_purchase_order` al modelo de orden de compra (`purchase.order`).
  - Este campo permite marcar una orden de compra como "excepcional".
  - Se muestra en el formulario de la orden de compra para una fácil identificación.

- **Nota Interna:**
  - Agrega un campo de texto de varias líneas `internal_note` al modelo de orden de compra.
  - Este campo está diseñado para añadir comentarios o notas internas que no son visibles para el proveedor.
  - Se encuentra disponible en el formulario de la orden de compra.

- **Traducciones:**
  - Incluye traducciones para los nuevos campos y vistas en Español (es) y Español de México (es_MX), asegurando una experiencia de usuario consistente para los hablantes de español.

- **Ícono de Aplicación:**
  - El módulo está configurado como una aplicación de Odoo con un ícono personalizado para una mejor identificación en el menú de aplicaciones.

## Instalación

1.  Asegúrate de que este módulo (`san_mex_company_custom`) esté en tu carpeta de `addons`.
2.  Reinicia el servidor de Odoo (especialmente si es la primera instalación o si se han añadido/modificado archivos Python `.py`).
3.  Ve a `Aplicaciones` en Odoo, busca "San Mex Company Custom" y haz clic en "Instalar" o "Actualizar".
