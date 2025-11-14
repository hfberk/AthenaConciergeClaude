/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Sage Luxury Palette - Nature Inspired
        earth: {
          dark: '#736E58',
          black: '#000000',
        },
        sage: {
          dark: '#7E9D85',
          DEFAULT: '#9DBB9C',
          medium: '#9DBB9C',
          light: '#E4ECE6',
          white: '#F8FAF9',
        },
        gold: {
          accent: '#D6A84E',
          DEFAULT: '#D6A84E',
        },
        // Legacy primary for backwards compatibility
        primary: {
          50: '#F8FAF9',
          100: '#E4ECE6',
          200: '#9DBB9C',
          300: '#7E9D85',
          400: '#736E58',
          500: '#7E9D85',
          600: '#736E58',
          700: '#5a5646',
          800: '#403d32',
          900: '#000000',
        },
      },
      fontFamily: {
        display: ['Fraunces', 'Crimson Pro', 'serif'],
        body: ['Libre Baskerville', 'Georgia', 'serif'],
        ui: ['Jost', 'Avenir', 'sans-serif'],
      },
      fontSize: {
        root: ['0.75rem', { lineHeight: '1.5' }],
        sprout: ['0.875rem', { lineHeight: '1.5' }],
        stem: ['1rem', { lineHeight: '1.6' }],
        branch: ['1.25rem', { lineHeight: '1.4' }],
        limb: ['1.75rem', { lineHeight: '1.3' }],
        trunk: ['2.25rem', { lineHeight: '1.2' }],
        canopy: ['3rem', { lineHeight: '1.1' }],
      },
      spacing: {
        fib1: '8px',
        fib2: '13px',
        fib3: '21px',
        fib4: '34px',
        fib5: '55px',
        fib6: '89px',
      },
      borderRadius: {
        organic: '16px 20px 18px 14px',
        'organic-sm': '8px 10px 9px 7px',
        'organic-lg': '24px 28px 26px 22px',
      },
      animation: {
        'leaf-rustle': 'leafRustle 4s ease-in-out infinite',
        'branch-sway': 'branchSway 8s ease-in-out infinite',
        'root-pulse': 'rootPulse 2s ease-in-out infinite',
        'grow-in': 'growIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
      },
      keyframes: {
        leafRustle: {
          '0%, 100%': { transform: 'rotate(0deg) translateY(0)' },
          '25%': { transform: 'rotate(1deg) translateY(-2px)' },
          '75%': { transform: 'rotate(-1deg) translateY(-1px)' },
        },
        branchSway: {
          '0%, 100%': { transform: 'translateX(0) rotate(0deg)' },
          '50%': { transform: 'translateX(8px) rotate(1deg)' },
        },
        rootPulse: {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '1' },
        },
        growIn: {
          '0%': { transform: 'scale(0.8) translateY(20px)', opacity: '0' },
          '100%': { transform: 'scale(1) translateY(0)', opacity: '1' },
        },
      },
      boxShadow: {
        organic: '0 4px 20px rgba(115, 110, 88, 0.08)',
        'organic-hover': '0 8px 24px rgba(126, 157, 133, 0.15)',
      },
    },
  },
  plugins: [],
}
