/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static/**/*.js',
    './media/django-ckeditor-5/**/*.css', // Add this for CKEditor content
  ],
  theme: {
    extend: {
      colors: {
        'brand-teal': {
          50: '#e6f1f3',
          100: '#b8dadf',
          200: '#8ac2cb',
          400: '#2a8a99',
          500: '#006377',
          600: '#0c8485',
          700: '#004d5c',
          800: '#073a47',
          900: '#051924',
        },
        'hero-teal': '#0c8485',
        'brand-orange': '#f99a00',
        'brand-amber': '#ffad00',
        'brand-yellow': '#ffd300',
        'brand-sage': '#ccd19c',
        'surface': '#ffffff',
        'surface-alt': '#f6f5f0',
        'ink': '#0b1f24',
        'ink-muted': '#4b5b60',
      },
      fontFamily: {
        // Make the default `font-sans` utility match the html-level Poppins.
        // Without this, `font-sans` resolves to Tailwind's default
        // (ui-sans-serif, system-ui, ...) and overrides the inherited Poppins
        // back to system fonts wherever it is applied.
        sans: ['Poppins', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        'eyebrow': ['0.75rem', { lineHeight: '1.4', letterSpacing: '0.12em' }],
        'display-lg': ['clamp(2rem, 3.5vw, 3rem)', { lineHeight: '1.1', letterSpacing: '-0.01em' }],
        'display-xl': ['clamp(2.5rem, 5vw, 4.25rem)', { lineHeight: '1.05', letterSpacing: '-0.02em' }],
      },
      boxShadow: {
        'card': '0 4px 16px rgba(5,25,36,0.08)',
        'card-lg': '0 12px 32px rgba(5,25,36,0.14)',
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none', // Prevents prose from constraining width
            color: 'inherit', // Use text color from parent
            a: {
              color: '#3182ce',
              '&:hover': {
                color: '#2c5282',
              },
              textDecoration: 'none',
            },
            'figure.image': {
              margin: '2em 0',
            },
            'figure.image img': {
              margin: '0 auto',
            },
            'figure.image figcaption': {
              textAlign: 'center',
              fontStyle: 'italic',
              marginTop: '0.5em',
            },
            table: {
              width: '100%',
              borderCollapse: 'collapse',
              marginTop: '1em',
              marginBottom: '1em',
            },
            'td, th': {
              border: '1px solid #e5e7eb',
              padding: '0.5em',
              textAlign: 'left',
            },
            img: {
              marginTop: '1em',
              marginBottom: '1em',
              borderRadius: '0.375rem',
            },
            '.image-style-align-left': {
              float: 'left',
              marginRight: '1em',
            },
            '.image-style-align-right': {
              float: 'right',
              marginLeft: '1em',
            },
            '.image-style-align-center': {
              margin: '0 auto',
              display: 'block',
            }
          }
        }
      }
    }
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}