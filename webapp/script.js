document.addEventListener('DOMContentLoaded', () => {
    const gallery = document.querySelector('.gallery');
    const lightbox = document.createElement('div');
    lightbox.id = 'lightbox';
    document.body.appendChild(lightbox);

    gallery.addEventListener('click', e => {
        if (e.target.tagName === 'IMG') {
            lightbox.classList.add('active');
            const img = document.createElement('img');
            img.src = e.target.src;
            while (lightbox.firstChild) {
                lightbox.removeChild(lightbox.firstChild);
            }
            lightbox.appendChild(img);
        }
    });

    lightbox.addEventListener('click', e => {
        if (e.target !== e.currentTarget) return;
        lightbox.classList.remove('active');
    });
});
