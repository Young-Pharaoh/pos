"""Bilingual (Spanish / Arabic) interface strings.

This is a plain dictionary-based translation table rather than Qt's
``.ts``/``.qm`` linguist tooling, which keeps the packaging pipeline
simple (no ``lrelease`` build step) at the cost of not being extractable
by Qt Linguist. For two languages and a small screen count this trade-off
favours simplicity.

The current interface language is process-global state (`get_language` /
`set_language`), which is an acceptable simplification for a single-window
desktop app with no concurrency. UI widgets read the current language when
building labels and re-read it inside ``retranslate()`` when the user
switches languages.

Product data (``name_ar`` / ``name_es``) is unrelated to this module: those
are stored verbatim in the database in both languages regardless of which
language the interface chrome is currently displayed in.
"""

from __future__ import annotations

SPANISH = "es"
ARABIC = "ar"
LANGUAGES = (SPANISH, ARABIC)
DEFAULT_LANGUAGE = SPANISH

_LANGUAGE_NAMES = {SPANISH: "Espanol", ARABIC: "\u0627\u0644\u0639\u0631\u0628\u064a\u0629"}

STRINGS: dict[str, dict[str, str]] = {
    SPANISH: {
        "app.title": "Sistema de Inventario",
        "nav.dashboard": "Panel",
        "nav.products": "Productos",
        "nav.new_sale": "Nueva Venta",
        "nav.reports": "Reportes",
        "common.save": "Guardar",
        "common.cancel": "Cancelar",
        "common.delete": "Eliminar",
        "common.edit": "Editar",
        "common.close": "Cerrar",
        "common.continue": "Continuar",
        "common.search": "Buscar",
        "common.add": "Agregar",
        "common.new": "Nuevo",
        "common.yes": "Si",
        "common.no": "No",
        "common.ok": "Aceptar",
        "common.confirm": "Confirmar",
        "common.actions": "Acciones",
        "common.image": "Imagen",
        "common.choose_image": "Elegir imagen...",
        "common.remove_image": "Quitar imagen",
        "common.refresh": "Actualizar",
        "common.export_csv": "Exportar CSV",
        "common.warning": "Advertencia",
        "common.error": "Error",
        "common.success": "Exito",
        "common.all": "Todos",
        "common.active": "Activos",
        "common.archived": "Archivados",
        "menu.file": "Archivo",
        "menu.backup": "Respaldar base de datos",
        "menu.backup_done": "Respaldo creado en:\n{path}",
        "menu.backup_failed": "No se pudo crear el respaldo: {detail}",
        "menu.settings": "Configuracion",
        "menu.exit": "Salir",
        "menu.help": "Ayuda",
        "menu.about": "Acerca de",
        "menu.about_text": (
            "Sistema de Inventario\n"
            "Aplicacion de escritorio para inventario, ventas y reportes.\n"
            "Base de datos: {db_path}"
        ),
        "menu.language": "Idioma",
        "menu.text_scale": "Tamano de texto",
        "text_scale.normal": "Normal",
        "text_scale.large": "Grande",
        "text_scale.extra_large": "Extra grande",
        "status.db_path": "Base de datos: {path}",
        "dashboard.title": "Panel Principal",
        "dashboard.today_sales": "Ventas de Hoy",
        "dashboard.month_sales": "Ventas del Mes",
        "dashboard.month_profit": "Ganancia del Mes",
        "dashboard.inventory_value": "Valor del Inventario",
        "dashboard.low_stock": "Stock Bajo",
        "dashboard.best_sellers": "Mas Vendidos (este mes)",
        "dashboard.no_low_stock": "No hay productos con stock bajo.",
        "dashboard.no_sales_yet": "Todavia no hay ventas este mes.",
        "dashboard.units_remaining": "{stock} unidades restantes",
        "dashboard.units_sold": "{qty} vendidas",
        "products.title": "Productos",
        "products.search_placeholder": "Buscar por ID, nombre en arabe o espanol...",
        "products.column_id": "ID",
        "products.column_name_ar": "Nombre (arabe)",
        "products.column_name_es": "Nombre (espanol)",
        "products.column_stock": "Stock",
        "products.column_avg_cost": "Costo Promedio",
        "products.column_sell_price": "Precio de Venta",
        "products.column_inventory_value": "Valor en Inventario",
        "products.column_status": "Estado",
        "products.status_active": "Activo",
        "products.status_archived": "Archivado",
        "products.button_new": "Nuevo Producto",
        "products.button_edit": "Editar",
        "products.button_add_stock": "Agregar Stock",
        "products.button_archive": "Archivar",
        "products.button_restore": "Restaurar",
        "products.button_delete": "Eliminar",
        "products.no_selection": "Seleccione un producto primero.",
        "products.confirm_delete_title": "Eliminar producto",
        "products.confirm_delete_message": (
            "Esta a punto de eliminar permanentemente '{name}'.\n"
            "Esta accion no se puede deshacer. Continuar?"
        ),
        "products.confirm_archive_title": "Archivar producto",
        "products.confirm_archive_message": (
            "'{name}' tiene historial de compras o ventas, por lo que no puede "
            "eliminarse. Desea archivarlo en su lugar? Los productos archivados "
            "dejan de aparecer en Nueva Venta pero conservan su historial."
        ),
        "products.confirm_restore_title": "Restaurar producto",
        "products.confirm_restore_message": "Restaurar '{name}' como producto activo?",
        "products.deleted_message": "Producto eliminado correctamente.",
        "products.archived_message": "Producto archivado correctamente.",
        "products.restored_message": "Producto restaurado correctamente.",
        "product_dialog.title_new": "Nuevo Producto",
        "product_dialog.title_edit": "Editar Producto",
        "product_dialog.name_ar": "Nombre en arabe",
        "product_dialog.name_es": "Nombre en espanol",
        "product_dialog.purchase_price": "Precio de compra",
        "product_dialog.sell_price": "Precio de venta",
        "product_dialog.initial_stock": "Stock inicial",
        "product_dialog.image": "Imagen",
        "product_dialog.note_locked_fields": (
            "El precio de compra y el stock no se editan aqui. "
            "Use 'Agregar Stock' para registrar nuevas compras."
        ),
        "add_stock_dialog.title": "Agregar Stock: {name}",
        "add_stock_dialog.current_stock": "Stock actual: {stock}",
        "add_stock_dialog.current_price": "Precio de compra registrado: {price}",
        "add_stock_dialog.quantity": "Cantidad",
        "add_stock_dialog.unit_price": "Precio de compra por unidad",
        "add_stock_dialog.preview_new_stock": "Nuevo stock: {stock}",
        "add_stock_dialog.preview_new_average": "Nuevo costo promedio: {price}",
        "add_stock_dialog.confirm_price_change_title": "Cambio de precio de compra",
        "add_stock_dialog.confirm_price_change_message": (
            "Precio registrado: {old_price}\n"
            "Precio nuevo: {new_price}\n\n"
            "El costo promedio se recalculara a: {new_average}\n\n"
            "Desea continuar?"
        ),
        "add_stock_dialog.success": "Stock agregado correctamente.",
        "sales.title": "Nueva Venta",
        "sales.item_field_label": "Producto (ID o nombre):",
        "sales.quantity_label": "Cantidad:",
        "sales.button_add": "AGREGAR",
        "sales.column_id": "ID",
        "sales.column_product": "Producto",
        "sales.column_quantity": "Cantidad",
        "sales.column_price": "Precio",
        "sales.column_total": "Total",
        "sales.total_label": "TOTAL: {total}",
        "sales.button_complete_sale": "COMPLETAR VENTA",
        "sales.button_remove_line": "Quitar",
        "sales.item_not_found": "No se encontro ningun producto activo con '{query}'.",
        "sales.item_found_info": "{name} -- disponible: {stock}",
        "sales.empty_sale_message": "Agregue al menos un producto antes de completar la venta.",
        "sales.sale_completed_title": "Venta completada",
        "sales.sale_completed_message": "Venta #{sale_id} completada. Total: {total}",
        "sales.confirm_clear_title": "Cancelar venta",
        "sales.confirm_clear_message": "Se perderan los productos agregados. Continuar?",
        "reports.title": "Reportes",
        "reports.period_day": "Diario",
        "reports.period_month": "Mensual",
        "reports.period_year": "Anual",
        "reports.period_custom": "Rango personalizado",
        "reports.from_label": "Desde:",
        "reports.to_label": "Hasta:",
        "reports.button_generate": "Generar",
        "reports.tab_products": "Reporte de Productos",
        "reports.tab_best_sellers": "Mas Vendidos",
        "reports.tab_most_profitable": "Mas Rentables",
        "reports.tab_slow_sellers": "Menos Vendidos",
        "reports.column_purchased": "Cant. Comprada",
        "reports.column_sold": "Cant. Vendida",
        "reports.column_current_stock": "Stock Actual",
        "reports.column_purchase_unit": "Compra (Unidad, periodo)",
        "reports.column_purchase_unit_tooltip": (
            "Precio unitario promedio pagado durante el periodo seleccionado "
            "(vacio si no hubo compras en el periodo)."
        ),
        "reports.column_purchase_total": "Compra Total",
        "reports.column_current_avg_cost": "Costo Promedio Actual",
        "reports.column_current_avg_cost_tooltip": (
            "Costo promedio ponderado vigente ahora mismo (usado para el "
            "valor del inventario), no del periodo seleccionado."
        ),
        "reports.column_sell_unit": "Venta (Unidad)",
        "reports.column_sell_total": "Venta Total",
        "reports.column_profit": "Ganancia",
        "reports.column_inventory_value": "Valor en Inventario",
        "reports.totals_row_label": "TOTALES",
        "reports.rank": "#",
        "reports.column_item": "Producto",
        "reports.column_sell_through_pct": "% Rotacion",
        "reports.qty_sold": "Vendidos",
        "reports.profit": "Ganancia",
        "reports.sell_through": "{sold} de {available} disponibles ({pct}%)",
        "reports.no_data": "No hay datos para el periodo seleccionado.",
        "reports.export_success": "Reporte exportado a:\n{path}",
        "reports.export_failed": "No se pudo exportar el reporte: {detail}",
        "reports.slow_sellers_hint": (
            "Tasa de rotacion = unidades vendidas / (unidades vendidas + stock actual). "
            "Un porcentaje bajo indica que el producto se mueve lentamente en relacion "
            "a lo que hay disponible."
        ),
        "settings.title": "Configuracion",
        "settings.low_stock_threshold": "Umbral de stock bajo",
        "settings.default_sell_price": "Precio de venta por defecto",
        "settings.currency_symbol": "Simbolo de moneda",
        "settings.language": "Idioma de la aplicacion",
        "settings.saved": "Configuracion guardada.",
        "error.item_not_found": "No se encontro el producto con ID {item_id}.",
        "error.item_inactive": "El producto {item_id} esta archivado y no se puede vender.",
        "error.insufficient_stock": (
            "Stock insuficiente para el producto {item_id}: "
            "solicitado {requested}, disponible {available}."
        ),
        "error.deletion_not_allowed": (
            "El producto {item_id} tiene historial de compras o ventas y no "
            "puede eliminarse. Archivelo en su lugar."
        ),
        "error.database_unavailable": "No se pudo acceder a la base de datos. {detail}",
        "error.name_ar_required": "El nombre en arabe es obligatorio.",
        "error.name_es_required": "El nombre en espanol es obligatorio.",
        "error.negative_purchase_price": "El precio de compra no puede ser negativo.",
        "error.negative_sell_price": "El precio de venta no puede ser negativo.",
        "error.negative_initial_stock": "El stock inicial no puede ser negativo.",
        "error.invalid_quantity": "La cantidad debe ser un numero entero positivo.",
        "error.invalid_price": "El precio debe ser un numero valido mayor o igual a cero.",
        "error.invalid_threshold": "El umbral debe ser un numero entero no negativo.",
        "error.unexpected": "Ocurrio un error inesperado: {detail}",
        "error.image_load_failed": "No se pudo cargar la imagen seleccionada.",
    },
    ARABIC: {
        "app.title": "\u0646\u0638\u0627\u0645 \u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u062e\u0632\u0648\u0646",
        "nav.dashboard": "\u0644\u0648\u062d\u0629 \u0627\u0644\u062a\u062d\u0643\u0645",
        "nav.products": "\u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a",
        "nav.new_sale": "\u0628\u064a\u0639 \u062c\u062f\u064a\u062f",
        "nav.reports": "\u0627\u0644\u062a\u0642\u0627\u0631\u064a\u0631",
        "common.save": "\u062d\u0641\u0638",
        "common.cancel": "\u0625\u0644\u063a\u0627\u0621",
        "common.delete": "\u062d\u0630\u0641",
        "common.edit": "\u062a\u0639\u062f\u064a\u0644",
        "common.close": "\u0625\u063a\u0644\u0627\u0642",
        "common.continue": "\u0645\u062a\u0627\u0628\u0639\u0629",
        "common.search": "\u0628\u062d\u062b",
        "common.add": "\u0625\u0636\u0627\u0641\u0629",
        "common.new": "\u062c\u062f\u064a\u062f",
        "common.yes": "\u0646\u0639\u0645",
        "common.no": "\u0644\u0627",
        "common.ok": "\u0645\u0648\u0627\u0641\u0642",
        "common.confirm": "\u062a\u0623\u0643\u064a\u062f",
        "common.actions": "\u0625\u062c\u0631\u0627\u0621\u0627\u062a",
        "common.image": "\u0635\u0648\u0631\u0629",
        "common.choose_image": "\u0627\u062e\u062a\u064a\u0627\u0631 \u0635\u0648\u0631\u0629...",
        "common.remove_image": "\u0625\u0632\u0627\u0644\u0629 \u0627\u0644\u0635\u0648\u0631\u0629",
        "common.refresh": "\u062a\u062d\u062f\u064a\u062b",
        "common.export_csv": "\u062a\u0635\u062f\u064a\u0631 CSV",
        "common.warning": "\u062a\u0646\u0628\u064a\u0647",
        "common.error": "\u062e\u0637\u0623",
        "common.success": "\u0646\u062c\u0627\u062d",
        "common.all": "\u0627\u0644\u0643\u0644",
        "common.active": "\u0646\u0634\u0637",
        "common.archived": "\u0645\u0624\u0631\u0634\u0641",
        "menu.file": "\u0645\u0644\u0641",
        "menu.backup": "\u0646\u0633\u062e \u0627\u062d\u062a\u064a\u0627\u0637\u064a \u0644\u0642\u0627\u0639\u062f\u0629 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a",
        "menu.backup_done": "\u062a\u0645 \u0625\u0646\u0634\u0627\u0621 \u0627\u0644\u0646\u0633\u062e\u0629 \u0627\u0644\u0627\u062d\u062a\u064a\u0627\u0637\u064a\u0629 \u0641\u064a:\n{path}",
        "menu.backup_failed": "\u062a\u0639\u0630\u0631 \u0625\u0646\u0634\u0627\u0621 \u0627\u0644\u0646\u0633\u062e\u0629 \u0627\u0644\u0627\u062d\u062a\u064a\u0627\u0637\u064a\u0629: {detail}",
        "menu.settings": "\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a",
        "menu.exit": "\u062e\u0631\u0648\u062c",
        "menu.help": "\u0645\u0633\u0627\u0639\u062f\u0629",
        "menu.about": "\u062d\u0648\u0644 \u0627\u0644\u0628\u0631\u0646\u0627\u0645\u062c",
        "menu.about_text": (
            "\u0646\u0638\u0627\u0645 \u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u062e\u0632\u0648\u0646\n"
            "\u062a\u0637\u0628\u064a\u0642 \u0633\u0637\u062d \u0627\u0644\u0645\u0643\u062a\u0628 \u0644\u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u0648\u0627\u0644\u0645\u0628\u064a\u0639\u0627\u062a \u0648\u0627\u0644\u062a\u0642\u0627\u0631\u064a\u0631.\n"
            "\u0642\u0627\u0639\u062f\u0629 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a: {db_path}"
        ),
        "menu.language": "\u0627\u0644\u0644\u063a\u0629",
        "menu.text_scale": "\u062d\u062c\u0645 \u0627\u0644\u0646\u0635",
        "text_scale.normal": "\u0639\u0627\u062f\u064a",
        "text_scale.large": "\u0643\u0628\u064a\u0631",
        "text_scale.extra_large": "\u0643\u0628\u064a\u0631 \u062c\u062f\u0627\u064b",
        "status.db_path": "\u0642\u0627\u0639\u062f\u0629 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a: {path}",
        "dashboard.title": "\u0644\u0648\u062d\u0629 \u0627\u0644\u062a\u062d\u0643\u0645",
        "dashboard.today_sales": "\u0645\u0628\u064a\u0639\u0627\u062a \u0627\u0644\u064a\u0648\u0645",
        "dashboard.month_sales": "\u0645\u0628\u064a\u0639\u0627\u062a \u0627\u0644\u0634\u0647\u0631",
        "dashboard.month_profit": "\u0631\u0628\u062d \u0627\u0644\u0634\u0647\u0631",
        "dashboard.inventory_value": "\u0642\u064a\u0645\u0629 \u0627\u0644\u0645\u062e\u0632\u0648\u0646",
        "dashboard.low_stock": "\u0645\u062e\u0632\u0648\u0646 \u0645\u0646\u062e\u0641\u0636",
        "dashboard.best_sellers": "\u0627\u0644\u0623\u0643\u062b\u0631 \u0645\u0628\u064a\u0639\u0627 (\u0647\u0630\u0627 \u0627\u0644\u0634\u0647\u0631)",
        "dashboard.no_low_stock": "\u0644\u0627 \u062a\u0648\u062c\u062f \u0645\u0646\u062a\u062c\u0627\u062a \u0630\u0627\u062a \u0645\u062e\u0632\u0648\u0646 \u0645\u0646\u062e\u0641\u0636.",
        "dashboard.no_sales_yet": "\u0644\u0627 \u062a\u0648\u062c\u062f \u0645\u0628\u064a\u0639\u0627\u062a \u0628\u0639\u062f \u0647\u0630\u0627 \u0627\u0644\u0634\u0647\u0631.",
        "dashboard.units_remaining": "\u0645\u062a\u0628\u0642\u064a {stock} \u0648\u062d\u062f\u0629",
        "dashboard.units_sold": "\u062a\u0645 \u0628\u064a\u0639 {qty}",
        "products.title": "\u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a",
        "products.search_placeholder": "\u0627\u0628\u062d\u062b \u0628\u0627\u0644\u0631\u0642\u0645 \u0623\u0648 \u0627\u0644\u0627\u0633\u0645 \u0628\u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u0623\u0648 \u0627\u0644\u0625\u0633\u0628\u0627\u0646\u064a\u0629...",
        "products.column_id": "\u0627\u0644\u0631\u0642\u0645",
        "products.column_name_ar": "\u0627\u0644\u0627\u0633\u0645 (\u0639\u0631\u0628\u064a)",
        "products.column_name_es": "\u0627\u0644\u0627\u0633\u0645 (\u0625\u0633\u0628\u0627\u0646\u064a)",
        "products.column_stock": "\u0627\u0644\u0645\u062e\u0632\u0648\u0646",
        "products.column_avg_cost": "\u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u062a\u0643\u0644\u0641\u0629",
        "products.column_sell_price": "\u0633\u0639\u0631 \u0627\u0644\u0628\u064a\u0639",
        "products.column_inventory_value": "\u0642\u064a\u0645\u0629 \u0627\u0644\u0645\u062e\u0632\u0648\u0646",
        "products.column_status": "\u0627\u0644\u062d\u0627\u0644\u0629",
        "products.status_active": "\u0646\u0634\u0637",
        "products.status_archived": "\u0645\u0624\u0631\u0634\u0641",
        "products.button_new": "\u0645\u0646\u062a\u062c \u062c\u062f\u064a\u062f",
        "products.button_edit": "\u062a\u0639\u062f\u064a\u0644",
        "products.button_add_stock": "\u0625\u0636\u0627\u0641\u0629 \u0645\u062e\u0632\u0648\u0646",
        "products.button_archive": "\u0623\u0631\u0634\u0641\u0629",
        "products.button_restore": "\u0627\u0633\u062a\u0639\u0627\u062f\u0629",
        "products.button_delete": "\u062d\u0630\u0641",
        "products.no_selection": "\u064a\u0631\u062c\u0649 \u0627\u062e\u062a\u064a\u0627\u0631 \u0645\u0646\u062a\u062c \u0623\u0648\u0644\u0627.",
        "products.confirm_delete_title": "\u062d\u0630\u0641 \u0627\u0644\u0645\u0646\u062a\u062c",
        "products.confirm_delete_message": (
            "\u0623\u0646\u062a \u0639\u0644\u0649 \u0648\u0634\u0643 \u062d\u0630\u0641 '{name}' \u0646\u0647\u0627\u0626\u064a\u0627.\n"
            "\u0644\u0627 \u064a\u0645\u0643\u0646 \u0627\u0644\u062a\u0631\u0627\u062c\u0639 \u0639\u0646 \u0647\u0630\u0627 \u0627\u0644\u0625\u062c\u0631\u0627\u0621. \u0647\u0644 \u062a\u0631\u064a\u062f \u0627\u0644\u0645\u062a\u0627\u0628\u0639\u0629\u061f"
        ),
        "products.confirm_archive_title": "\u0623\u0631\u0634\u0641\u0629 \u0627\u0644\u0645\u0646\u062a\u062c",
        "products.confirm_archive_message": (
            "'{name}' \u0644\u062f\u064a\u0647 \u0633\u062c\u0644 \u0645\u0634\u062a\u0631\u064a\u0627\u062a \u0623\u0648 \u0645\u0628\u064a\u0639\u0627\u062a\u060c \u0644\u0630\u0644\u0643 \u0644\u0627 \u064a\u0645\u0643\u0646 "
            "\u062d\u0630\u0641\u0647. \u0647\u0644 \u062a\u0631\u064a\u062f \u0623\u0631\u0634\u0641\u062a\u0647 \u0628\u062f\u0644\u0627 \u0645\u0646 \u0630\u0644\u0643\u061f \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a "
            "\u0627\u0644\u0645\u0624\u0631\u0634\u0641\u0629 \u0644\u0627 \u062a\u0638\u0647\u0631 \u0641\u064a \u0628\u064a\u0639 \u062c\u062f\u064a\u062f \u0648\u0644\u0643\u0646\u0647\u0627 \u062a\u062d\u062a\u0641\u0638 \u0628\u0633\u062c\u0644\u0647\u0627."
        ),
        "products.confirm_restore_title": "\u0627\u0633\u062a\u0639\u0627\u062f\u0629 \u0627\u0644\u0645\u0646\u062a\u062c",
        "products.confirm_restore_message": "\u0647\u0644 \u062a\u0631\u064a\u062f \u0627\u0633\u062a\u0639\u0627\u062f\u0629 '{name}' \u0643\u0645\u0646\u062a\u062c \u0646\u0634\u0637\u061f",
        "products.deleted_message": "\u062a\u0645 \u062d\u0630\u0641 \u0627\u0644\u0645\u0646\u062a\u062c \u0628\u0646\u062c\u0627\u062d.",
        "products.archived_message": "\u062a\u0645 \u0623\u0631\u0634\u0641\u0629 \u0627\u0644\u0645\u0646\u062a\u062c \u0628\u0646\u062c\u0627\u062d.",
        "products.restored_message": "\u062a\u0645 \u0627\u0633\u062a\u0639\u0627\u062f\u0629 \u0627\u0644\u0645\u0646\u062a\u062c \u0628\u0646\u062c\u0627\u062d.",
        "product_dialog.title_new": "\u0645\u0646\u062a\u062c \u062c\u062f\u064a\u062f",
        "product_dialog.title_edit": "\u062a\u0639\u062f\u064a\u0644 \u0627\u0644\u0645\u0646\u062a\u062c",
        "product_dialog.name_ar": "\u0627\u0644\u0627\u0633\u0645 \u0628\u0627\u0644\u0639\u0631\u0628\u064a\u0629",
        "product_dialog.name_es": "\u0627\u0644\u0627\u0633\u0645 \u0628\u0627\u0644\u0625\u0633\u0628\u0627\u0646\u064a\u0629",
        "product_dialog.purchase_price": "\u0633\u0639\u0631 \u0627\u0644\u0634\u0631\u0627\u0621",
        "product_dialog.sell_price": "\u0633\u0639\u0631 \u0627\u0644\u0628\u064a\u0639",
        "product_dialog.initial_stock": "\u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u0627\u0644\u0623\u0648\u0644\u064a",
        "product_dialog.image": "\u0627\u0644\u0635\u0648\u0631\u0629",
        "product_dialog.note_locked_fields": (
            "\u0644\u0627 \u064a\u0645\u0643\u0646 \u062a\u0639\u062f\u064a\u0644 \u0633\u0639\u0631 \u0627\u0644\u0634\u0631\u0627\u0621 \u0623\u0648 \u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u0645\u0646 \u0647\u0646\u0627. "
            "\u0627\u0633\u062a\u062e\u062f\u0645 '\u0625\u0636\u0627\u0641\u0629 \u0645\u062e\u0632\u0648\u0646' \u0644\u062a\u0633\u062c\u064a\u0644 \u0645\u0634\u062a\u0631\u064a\u0627\u062a \u062c\u062f\u064a\u062f\u0629."
        ),
        "add_stock_dialog.title": "\u0625\u0636\u0627\u0641\u0629 \u0645\u062e\u0632\u0648\u0646: {name}",
        "add_stock_dialog.current_stock": "\u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u0627\u0644\u062d\u0627\u0644\u064a: {stock}",
        "add_stock_dialog.current_price": "\u0633\u0639\u0631 \u0627\u0644\u0634\u0631\u0627\u0621 \u0627\u0644\u0645\u0633\u062c\u0644: {price}",
        "add_stock_dialog.quantity": "\u0627\u0644\u0643\u0645\u064a\u0629",
        "add_stock_dialog.unit_price": "\u0633\u0639\u0631 \u0627\u0644\u0634\u0631\u0627\u0621 \u0644\u0644\u0648\u062d\u062f\u0629",
        "add_stock_dialog.preview_new_stock": "\u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u0627\u0644\u062c\u062f\u064a\u062f: {stock}",
        "add_stock_dialog.preview_new_average": "\u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u062a\u0643\u0644\u0641\u0629 \u0627\u0644\u062c\u062f\u064a\u062f: {price}",
        "add_stock_dialog.confirm_price_change_title": "\u062a\u063a\u064a\u0631 \u0633\u0639\u0631 \u0627\u0644\u0634\u0631\u0627\u0621",
        "add_stock_dialog.confirm_price_change_message": (
            "\u0627\u0644\u0633\u0639\u0631 \u0627\u0644\u0645\u0633\u062c\u0644: {old_price}\n"
            "\u0627\u0644\u0633\u0639\u0631 \u0627\u0644\u062c\u062f\u064a\u062f: {new_price}\n\n"
            "\u0633\u064a\u062a\u0645 \u0625\u0639\u0627\u062f\u0629 \u062d\u0633\u0627\u0628 \u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u062a\u0643\u0644\u0641\u0629 \u0625\u0644\u0649: {new_average}\n\n"
            "\u0647\u0644 \u062a\u0631\u064a\u062f \u0627\u0644\u0645\u062a\u0627\u0628\u0639\u0629\u061f"
        ),
        "add_stock_dialog.success": "\u062a\u0645\u062a \u0625\u0636\u0627\u0641\u0629 \u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u0628\u0646\u062c\u0627\u062d.",
        "sales.title": "\u0628\u064a\u0639 \u062c\u062f\u064a\u062f",
        "sales.item_field_label": "\u0627\u0644\u0645\u0646\u062a\u062c (\u0627\u0644\u0631\u0642\u0645 \u0623\u0648 \u0627\u0644\u0627\u0633\u0645):",
        "sales.quantity_label": "\u0627\u0644\u0643\u0645\u064a\u0629:",
        "sales.button_add": "\u0625\u0636\u0627\u0641\u0629",
        "sales.column_id": "\u0627\u0644\u0631\u0642\u0645",
        "sales.column_product": "\u0627\u0644\u0645\u0646\u062a\u062c",
        "sales.column_quantity": "\u0627\u0644\u0643\u0645\u064a\u0629",
        "sales.column_price": "\u0627\u0644\u0633\u0639\u0631",
        "sales.column_total": "\u0627\u0644\u0625\u062c\u0645\u0627\u0644\u064a",
        "sales.total_label": "\u0627\u0644\u0625\u062c\u0645\u0627\u0644\u064a: {total}",
        "sales.button_complete_sale": "\u0625\u062a\u0645\u0627\u0645 \u0627\u0644\u0628\u064a\u0639",
        "sales.button_remove_line": "\u0625\u0632\u0627\u0644\u0629",
        "sales.item_not_found": "\u0644\u0645 \u064a\u0639\u062b\u0631 \u0639\u0644\u0649 \u0645\u0646\u062a\u062c \u0646\u0634\u0637 \u0645\u0637\u0627\u0628\u0642 \u0644\u0640 '{query}'.",
        "sales.item_found_info": "{name} -- \u0627\u0644\u0645\u062a\u0627\u062d: {stock}",
        "sales.empty_sale_message": "\u0623\u0636\u0641 \u0645\u0646\u062a\u062c\u0627 \u0648\u0627\u062d\u062f\u0627 \u0639\u0644\u0649 \u0627\u0644\u0623\u0642\u0644 \u0642\u0628\u0644 \u0625\u062a\u0645\u0627\u0645 \u0627\u0644\u0628\u064a\u0639.",
        "sales.sale_completed_title": "\u062a\u0645 \u0625\u062a\u0645\u0627\u0645 \u0627\u0644\u0628\u064a\u0639",
        "sales.sale_completed_message": "\u062a\u0645\u062a \u0627\u0644\u0639\u0645\u0644\u064a\u0629 \u0631\u0642\u0645 {sale_id}. \u0627\u0644\u0625\u062c\u0645\u0627\u0644\u064a: {total}",
        "sales.confirm_clear_title": "\u0625\u0644\u063a\u0627\u0621 \u0627\u0644\u0628\u064a\u0639",
        "sales.confirm_clear_message": "\u0633\u064a\u062a\u0645 \u0641\u0642\u062f\u0627\u0646 \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a \u0627\u0644\u0645\u0636\u0627\u0641\u0629. \u0647\u0644 \u062a\u0631\u064a\u062f \u0627\u0644\u0645\u062a\u0627\u0628\u0639\u0629\u061f",
        "reports.title": "\u0627\u0644\u062a\u0642\u0627\u0631\u064a\u0631",
        "reports.period_day": "\u064a\u0648\u0645\u064a",
        "reports.period_month": "\u0634\u0647\u0631\u064a",
        "reports.period_year": "\u0633\u0646\u0648\u064a",
        "reports.period_custom": "\u0646\u0637\u0627\u0642 \u0645\u062e\u0635\u0635",
        "reports.from_label": "\u0645\u0646:",
        "reports.to_label": "\u0625\u0644\u0649:",
        "reports.button_generate": "\u0625\u0646\u0634\u0627\u0621 \u0627\u0644\u062a\u0642\u0631\u064a\u0631",
        "reports.tab_products": "\u062a\u0642\u0631\u064a\u0631 \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a",
        "reports.tab_best_sellers": "\u0627\u0644\u0623\u0643\u062b\u0631 \u0645\u0628\u064a\u0639\u0627",
        "reports.tab_most_profitable": "\u0627\u0644\u0623\u0643\u062b\u0631 \u0631\u0628\u062d\u064a\u0629",
        "reports.tab_slow_sellers": "\u0627\u0644\u0623\u0642\u0644 \u0645\u0628\u064a\u0639\u0627",
        "reports.column_purchased": "\u0627\u0644\u0643\u0645\u064a\u0629 \u0627\u0644\u0645\u0634\u062a\u0631\u0627\u0629",
        "reports.column_sold": "\u0627\u0644\u0643\u0645\u064a\u0629 \u0627\u0644\u0645\u0628\u0627\u0639\u0629",
        "reports.column_current_stock": "\u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u0627\u0644\u062d\u0627\u0644\u064a",
        "reports.column_purchase_unit": "\u0633\u0639\u0631 \u0627\u0644\u0634\u0631\u0627\u0621 (\u0644\u0644\u0648\u062d\u062f\u0629\u060c \u0644\u0644\u0641\u062a\u0631\u0629)",
        "reports.column_purchase_unit_tooltip": (
            "\u0645\u062a\u0648\u0633\u0637 \u0633\u0639\u0631 \u0627\u0644\u0634\u0631\u0627\u0621 \u062e\u0644\u0627\u0644 \u0627\u0644\u0641\u062a\u0631\u0629 \u0627\u0644\u0645\u062d\u062f\u062f\u0629 "
            "(\u0641\u0627\u0631\u063a \u0625\u0630\u0627 \u0644\u0645 \u062a\u0643\u0646 \u0647\u0646\u0627\u0643 \u0645\u0634\u062a\u0631\u064a\u0627\u062a \u062e\u0644\u0627\u0644 \u0627\u0644\u0641\u062a\u0631\u0629)."
        ),
        "reports.column_purchase_total": "\u0625\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0634\u0631\u0627\u0621",
        "reports.column_current_avg_cost": "\u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u062a\u0643\u0644\u0641\u0629 \u0627\u0644\u062d\u0627\u0644\u064a",
        "reports.column_current_avg_cost_tooltip": (
            "\u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u062a\u0643\u0644\u0641\u0629 \u0627\u0644\u0645\u0631\u062c\u062d \u0627\u0644\u0633\u0627\u0631\u064a \u062d\u0627\u0644\u064a\u0627 "
            "(\u064a\u064f\u0633\u062a\u062e\u062f\u0645 \u0644\u062d\u0633\u0627\u0628 \u0642\u064a\u0645\u0629 \u0627\u0644\u0645\u062e\u0632\u0648\u0646)\u060c \u0648\u0644\u064a\u0633 \u062e\u0627\u0635\u0627 \u0628\u0627\u0644\u0641\u062a\u0631\u0629 \u0627\u0644\u0645\u062d\u062f\u062f\u0629."
        ),
        "reports.column_sell_unit": "\u0633\u0639\u0631 \u0627\u0644\u0628\u064a\u0639 (\u0644\u0644\u0648\u062d\u062f\u0629)",
        "reports.column_sell_total": "\u0625\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0628\u064a\u0639",
        "reports.column_profit": "\u0627\u0644\u0631\u0628\u062d",
        "reports.column_inventory_value": "\u0642\u064a\u0645\u0629 \u0627\u0644\u0645\u062e\u0632\u0648\u0646",
        "reports.totals_row_label": "\u0627\u0644\u0625\u062c\u0645\u0627\u0644\u064a",
        "reports.rank": "#",
        "reports.column_item": "\u0627\u0644\u0645\u0646\u062a\u062c",
        "reports.column_sell_through_pct": "% \u0627\u0644\u062f\u0648\u0631\u0627\u0646",
        "reports.qty_sold": "\u0627\u0644\u0645\u0628\u0627\u0639",
        "reports.profit": "\u0627\u0644\u0631\u0628\u062d",
        "reports.sell_through": "{sold} \u0645\u0646 {available} \u0645\u062a\u0627\u062d ({pct}%)",
        "reports.no_data": "\u0644\u0627 \u062a\u0648\u062c\u062f \u0628\u064a\u0627\u0646\u0627\u062a \u0644\u0644\u0641\u062a\u0631\u0629 \u0627\u0644\u0645\u062d\u062f\u062f\u0629.",
        "reports.export_success": "\u062a\u0645 \u062a\u0635\u062f\u064a\u0631 \u0627\u0644\u062a\u0642\u0631\u064a\u0631 \u0625\u0644\u0649:\n{path}",
        "reports.export_failed": "\u062a\u0639\u0630\u0631 \u062a\u0635\u062f\u064a\u0631 \u0627\u0644\u062a\u0642\u0631\u064a\u0631: {detail}",
        "reports.slow_sellers_hint": (
            "\u0645\u0639\u062f\u0644 \u0627\u0644\u062f\u0648\u0631\u0627\u0646 = \u0627\u0644\u0648\u062d\u062f\u0627\u062a \u0627\u0644\u0645\u0628\u0627\u0639\u0629 / (\u0627\u0644\u0648\u062d\u062f\u0627\u062a \u0627\u0644\u0645\u0628\u0627\u0639\u0629 + \u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u0627\u0644\u062d\u0627\u0644\u064a). "
            "\u0627\u0644\u0646\u0633\u0628\u0629 \u0627\u0644\u0645\u0646\u062e\u0641\u0636\u0629 \u062a\u0639\u0646\u064a \u0623\u0646 \u0627\u0644\u0645\u0646\u062a\u062c \u064a\u062a\u062d\u0631\u0643 \u0628\u0628\u0637\u0621 \u0645\u0642\u0627\u0631\u0646\u0629 \u0628\u0627\u0644\u0645\u062a\u0627\u062d \u0645\u0646\u0647."
        ),
        "settings.title": "\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a",
        "settings.low_stock_threshold": "\u062d\u062f \u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u0627\u0644\u0645\u0646\u062e\u0641\u0636",
        "settings.default_sell_price": "\u0633\u0639\u0631 \u0627\u0644\u0628\u064a\u0639 \u0627\u0644\u0627\u0641\u062a\u0631\u0627\u0636\u064a",
        "settings.currency_symbol": "\u0631\u0645\u0632 \u0627\u0644\u0639\u0645\u0644\u0629",
        "settings.language": "\u0644\u063a\u0629 \u0627\u0644\u062a\u0637\u0628\u064a\u0642",
        "settings.saved": "\u062a\u0645 \u062d\u0641\u0638 \u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a.",
        "error.item_not_found": "\u0644\u0645 \u064a\u064f\u0639\u062b\u0631 \u0639\u0644\u0649 \u0645\u0646\u062a\u062c \u0628\u0627\u0644\u0631\u0642\u0645 {item_id}.",
        "error.item_inactive": "\u0627\u0644\u0645\u0646\u062a\u062c {item_id} \u0645\u0624\u0631\u0634\u0641 \u0648\u0644\u0627 \u064a\u0645\u0643\u0646 \u0628\u064a\u0639\u0647.",
        "error.insufficient_stock": (
            "\u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u063a\u064a\u0631 \u0643\u0627\u0641\u064d \u0644\u0644\u0645\u0646\u062a\u062c {item_id}: "
            "\u0627\u0644\u0645\u0637\u0644\u0648\u0628 {requested}\u060c \u0627\u0644\u0645\u062a\u0627\u062d {available}."
        ),
        "error.deletion_not_allowed": (
            "\u0627\u0644\u0645\u0646\u062a\u062c {item_id} \u0644\u062f\u064a\u0647 \u0633\u062c\u0644 \u0645\u0634\u062a\u0631\u064a\u0627\u062a \u0623\u0648 \u0645\u0628\u064a\u0639\u0627\u062a "
            "\u0648\u0644\u0627 \u064a\u0645\u0643\u0646 \u062d\u0630\u0641\u0647. \u0642\u0645 \u0628\u0623\u0631\u0634\u0641\u062a\u0647 \u0628\u062f\u0644\u0627 \u0645\u0646 \u0630\u0644\u0643."
        ),
        "error.database_unavailable": "\u062a\u0639\u0630\u0631 \u0627\u0644\u0648\u0635\u0648\u0644 \u0625\u0644\u0649 \u0642\u0627\u0639\u062f\u0629 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a. {detail}",
        "error.name_ar_required": "\u0627\u0644\u0627\u0633\u0645 \u0628\u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u0645\u0637\u0644\u0648\u0628.",
        "error.name_es_required": "\u0627\u0644\u0627\u0633\u0645 \u0628\u0627\u0644\u0625\u0633\u0628\u0627\u0646\u064a\u0629 \u0645\u0637\u0644\u0648\u0628.",
        "error.negative_purchase_price": "\u0644\u0627 \u064a\u0645\u0643\u0646 \u0623\u0646 \u064a\u0643\u0648\u0646 \u0633\u0639\u0631 \u0627\u0644\u0634\u0631\u0627\u0621 \u0633\u0627\u0644\u0628\u0627.",
        "error.negative_sell_price": "\u0644\u0627 \u064a\u0645\u0643\u0646 \u0623\u0646 \u064a\u0643\u0648\u0646 \u0633\u0639\u0631 \u0627\u0644\u0628\u064a\u0639 \u0633\u0627\u0644\u0628\u0627.",
        "error.negative_initial_stock": "\u0644\u0627 \u064a\u0645\u0643\u0646 \u0623\u0646 \u064a\u0643\u0648\u0646 \u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u0627\u0644\u0623\u0648\u0644\u064a \u0633\u0627\u0644\u0628\u0627.",
        "error.invalid_quantity": "\u064a\u062c\u0628 \u0623\u0646 \u062a\u0643\u0648\u0646 \u0627\u0644\u0643\u0645\u064a\u0629 \u0639\u062f\u062f\u0627 \u0635\u062d\u064a\u062d\u0627 \u0645\u0648\u062c\u0628\u0627.",
        "error.invalid_price": "\u064a\u062c\u0628 \u0623\u0646 \u064a\u0643\u0648\u0646 \u0627\u0644\u0633\u0639\u0631 \u0631\u0642\u0645\u0627 \u0635\u0627\u0644\u062d\u0627 \u0623\u0643\u0628\u0631 \u0645\u0646 \u0623\u0648 \u064a\u0633\u0627\u0648\u064a \u0627\u0644\u0635\u0641\u0631.",
        "error.invalid_threshold": "\u064a\u062c\u0628 \u0623\u0646 \u064a\u0643\u0648\u0646 \u0627\u0644\u062d\u062f \u0639\u062f\u062f\u0627 \u0635\u062d\u064a\u062d\u0627 \u063a\u064a\u0631 \u0633\u0627\u0644\u0628.",
        "error.unexpected": "\u062d\u062f\u062b \u062e\u0637\u0623 \u063a\u064a\u0631 \u0645\u062a\u0648\u0642\u0639: {detail}",
        "error.image_load_failed": "\u062a\u0639\u0630\u0631 \u062a\u062d\u0645\u064a\u0644 \u0627\u0644\u0635\u0648\u0631\u0629 \u0627\u0644\u0645\u062e\u062a\u0627\u0631\u0629.",
    },
}

_current_language = DEFAULT_LANGUAGE


def get_language() -> str:
    return _current_language


def set_language(language: str) -> None:
    global _current_language
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported language: {language!r}")
    _current_language = language


def language_display_name(language: str) -> str:
    return _LANGUAGE_NAMES.get(language, language)


def text_scale_display_name(preset: str, language: str | None = None) -> str:
    return t(f"text_scale.{preset}", language=language)


def is_rtl(language: str | None = None) -> bool:
    return (language or _current_language) == ARABIC


def t(key: str, language: str | None = None, **params) -> str:
    """Translate ``key`` into ``language`` (or the current language)."""
    lang = language or _current_language
    table = STRINGS.get(lang, STRINGS[DEFAULT_LANGUAGE])
    text = table.get(key)
    if text is None:
        text = STRINGS[DEFAULT_LANGUAGE].get(key, key)
    if params:
        try:
            return text.format(**params)
        except (KeyError, IndexError):
            return text
    return text
