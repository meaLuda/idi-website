/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static/**/*.js',
    './media/django-ckeditor-5/**/*.css', // Add this for CKEditor content
  ],
  theme: {
    extend: {
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