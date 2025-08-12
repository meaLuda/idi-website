// Lazy Loading Implementation
document.addEventListener('DOMContentLoaded', function() {
    // Check if IntersectionObserver is supported
    if ('IntersectionObserver' in window) {
        // Create intersection observer for lazy loading images
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    
                    // Replace data-src with src
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    
                    // Replace data-srcset with srcset
                    if (img.dataset.srcset) {
                        img.srcset = img.dataset.srcset;
                        img.removeAttribute('data-srcset');
                    }
                    
                    // Remove lazy class and add loaded class
                    img.classList.remove('lazy');
                    img.classList.add('loaded');
                    
                    // Stop observing this image
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });

        // Observe all images with lazy class
        const lazyImages = document.querySelectorAll('img.lazy');
        lazyImages.forEach(img => {
            imageObserver.observe(img);
        });

        // Create intersection observer for lazy loading background images
        const bgObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    
                    if (element.dataset.bg) {
                        element.style.backgroundImage = `url(${element.dataset.bg})`;
                        element.removeAttribute('data-bg');
                        element.classList.remove('lazy-bg');
                        element.classList.add('loaded-bg');
                        observer.unobserve(element);
                    }
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });

        // Observe all elements with lazy-bg class
        const lazyBgs = document.querySelectorAll('.lazy-bg');
        lazyBgs.forEach(bg => {
            bgObserver.observe(bg);
        });

    } else {
        // Fallback for browsers that don't support IntersectionObserver
        const lazyImages = document.querySelectorAll('img.lazy');
        lazyImages.forEach(img => {
            if (img.dataset.src) {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
            }
            if (img.dataset.srcset) {
                img.srcset = img.dataset.srcset;
                img.removeAttribute('data-srcset');
            }
            img.classList.remove('lazy');
            img.classList.add('loaded');
        });

        const lazyBgs = document.querySelectorAll('.lazy-bg');
        lazyBgs.forEach(bg => {
            if (bg.dataset.bg) {
                bg.style.backgroundImage = `url(${bg.dataset.bg})`;
                bg.removeAttribute('data-bg');
                bg.classList.remove('lazy-bg');
                bg.classList.add('loaded-bg');
            }
        });
    }
});

// Add CSS for smooth transitions
const style = document.createElement('style');
style.textContent = `
    img.lazy {
        opacity: 0;
        transition: opacity 0.3s ease-in-out;
    }
    
    img.loaded {
        opacity: 1;
    }
    
    .lazy-bg {
        background-image: none !important;
        transition: background-image 0.3s ease-in-out;
    }
    
    .loaded-bg {
        /* Background image will be set via JS */
    }
    
    /* Placeholder for loading images */
    img.lazy::before {
        content: '';
        display: block;
        background: #f0f0f0;
        background-image: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
`;
document.head.appendChild(style);