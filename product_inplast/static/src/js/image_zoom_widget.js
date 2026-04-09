/** @odoo-module **/

// Función para mostrar el modal con la imagen
function showImageModal(imageSrc, imageElement) {
    // Verificar que la imagen tenga contenido
    if (!imageSrc || imageSrc.includes('placeholder') || imageSrc.includes('data:,')) return;

    console.log('Opening image modal:', imageSrc);

    // Crear modal
    const modal = document.createElement('div');
    modal.className = 'modal fade show d-block image-zoom-modal';
    modal.style.cssText = 'background-color: rgba(0,0,0,0.7); z-index: 10000;';

    modal.innerHTML = `
        <div class="modal-dialog modal-xl modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Image Preview</h5>
                    <button type="button" class="btn-close"></button>
                </div>
                <div class="modal-body text-center p-0">
                    <img src="${imageSrc}" class="img-fluid" style="max-width: 100%; max-height: 80vh;" alt="Full size image"/>
                </div>
            </div>
        </div>
    `;

    // Agregar al body
    document.body.appendChild(modal);

    // Cerrar modal al hacer click fuera o en el botón
    const closeModal = () => {
        modal.remove();
    };

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    modal.querySelector('.btn-close').addEventListener('click', closeModal);

    // Cerrar con ESC
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
}

// Función para verificar si una imagen tiene contenido válido
function hasValidImage(img) {
    const src = img.src;

    // Verificar que no sea placeholder o imagen vacía
    if (!src || src.includes('placeholder') || src.includes('data:,') || src.includes('/web/static/img/placeholder.png')) {
        return false;
    }

    // Verificar que la imagen tenga dimensiones
    if (img.naturalWidth === 0 || img.naturalHeight === 0) {
        return false;
    }

    return true;
}

// Event delegation desde document para capturar clicks en imágenes
document.addEventListener('click', function(e) {
    const target = e.target;

    // Verificar si el click es en una imagen
    if (target.tagName === 'IMG') {
        const parent = target.closest('.clickable-image, .o_field_image');

        if (parent) {
            // IMPORTANTE: Solo funciona en FORM VIEW, no en tree view
            const isInTreeView = target.closest('.coa_content_tree_view');

            if (isInTreeView) {
                console.log('Image in tree view - allowing normal behavior (open form)');
                return; // Dejar que abra el formulario normalmente
            }

            // Solo capturar el evento si la imagen tiene contenido válido
            if (!hasValidImage(target)) {
                console.log('Empty image in form view');
                return;
            }

            console.log('Image clicked in form view!', target.src);

            // Prevenir propagación solo en form view
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();

            // Mostrar modal
            showImageModal(target.src, target);

            return false;
        }
    }
}, true); // useCapture = true para capturar antes que otros handlers

console.log('Image zoom widget loaded!');
