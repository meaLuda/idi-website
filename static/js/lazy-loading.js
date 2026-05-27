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

// Add CSS for smooth transitions — only injected when lazy elements actually exist on
// the page. We start at opacity:0.01 (never a true 0) so we don't trip the Chromium
// NO_LCP bug where animating an LCP candidate from opacity:0 suppresses the LCP entry.
if (document.querySelector('img.lazy, .lazy-bg')) {
    const style = document.createElement('style');
    style.textContent = `
        img.lazy {
            opacity: 0.01;
            transition: opacity 0.3s ease-in-out;
        }

        img.loaded {
            opacity: 1;
        }

        .lazy-bg {
            background-image: none !important;
            transition: background-image 0.3s ease-in-out;
        }
    `;
    document.head.appendChild(style);
}