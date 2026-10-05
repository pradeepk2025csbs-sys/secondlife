// SECONDLIFE - Main Frontend Script

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.flash-alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // Confirmation for delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            const message = btn.getAttribute('data-confirm-delete') || 'Are you sure you want to delete this?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // ═══════ LIGHTWEIGHT 3D CARD TILT INTERACTION ═══════
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isHoverCapable = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

    if (!prefersReducedMotion && isHoverCapable) {
        const tiltCards = document.querySelectorAll('.card-3d-tilt');

        tiltCards.forEach(function (card) {
            let isHovered = false;
            let rafId = null;
            let targetRotX = 0;
            let targetRotY = 0;

            function updateCardTilt() {
                if (!isHovered) return;
                card.style.transform = `perspective(1000px) rotateX(${targetRotX.toFixed(2)}deg) rotateY(${targetRotY.toFixed(2)}deg) translateY(-4px)`;
            }

            card.addEventListener('mouseenter', function () {
                isHovered = true;
                card.style.transition = 'transform 0.1s ease-out, box-shadow 0.25s ease';
            });

            card.addEventListener('mousemove', function (e) {
                if (!isHovered) return;
                const rect = card.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return;

                // Relative position normalized: -1 (left/top) to +1 (right/bottom)
                const normX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
                const normY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;

                const maxTilt = 4.5; // Max ~5 degrees subtle rotation

                // Mouse moves toward top-left (normX < 0, normY < 0):
                // Card tilts slightly toward top-left
                // Mouse moves toward bottom-right (normX > 0, normY > 0):
                // Card tilts slightly toward bottom-right
                targetRotX = -normY * maxTilt;
                targetRotY = normX * maxTilt;

                if (!rafId) {
                    rafId = requestAnimationFrame(function () {
                        updateCardTilt();
                        rafId = null;
                    });
                }
            });

            card.addEventListener('mouseleave', function () {
                isHovered = false;
                if (rafId) {
                    cancelAnimationFrame(rafId);
                    rafId = null;
                }
                card.style.transition = 'transform 0.5s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.5s ease';
                card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)';
            });
        });
    }

    // ═══════ IMAGE UPLOAD INSTANT PREVIEW & DRAG-AND-DROP ═══════
    const imageInput = document.getElementById('image');
    const dropzone = document.getElementById('uploadDropzone');
    const previewContainer = document.getElementById('imagePreviewContainer');
    const previewImage = document.getElementById('imagePreview');
    const previewFilename = document.getElementById('imagePreviewFilename');
    const removeImageBtn = document.getElementById('removeImageBtn');

    if (imageInput && previewContainer) {
        function showPreview(file) {
            if (!file) return;
            if (!file.type.match('image.*')) {
                alert('Please select an image file (PNG, JPG, JPEG, WEBP).');
                return;
            }
            const reader = new FileReader();
            reader.onload = function (e) {
                if (previewImage) previewImage.src = e.target.result;
                if (previewFilename) previewFilename.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
                previewContainer.classList.remove('d-none');
                if (dropzone) dropzone.classList.add('has-file');
            };
            reader.readAsDataURL(file);
        }

        imageInput.addEventListener('change', function () {
            if (this.files && this.files[0]) {
                showPreview(this.files[0]);
            }
        });

        if (removeImageBtn) {
            removeImageBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                imageInput.value = '';
                previewContainer.classList.add('d-none');
                if (previewImage) previewImage.src = '';
                if (dropzone) dropzone.classList.remove('has-file');
            });
        }

        if (dropzone) {
            ['dragenter', 'dragover'].forEach(function (eventName) {
                dropzone.addEventListener(eventName, function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    dropzone.classList.add('dragover');
                }, false);
            });

            ['dragleave', 'drop'].forEach(function (eventName) {
                dropzone.addEventListener(eventName, function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    dropzone.classList.remove('dragover');
                }, false);
            });

            dropzone.addEventListener('drop', function (e) {
                const dt = e.dataTransfer;
                const files = dt.files;
                if (files && files.length > 0) {
                    imageInput.files = files;
                    showPreview(files[0]);
                }
            });
        }
    }
});

