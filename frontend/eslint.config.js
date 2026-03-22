import js from '@eslint/js'
import ts from '@typescript-eslint/eslint-plugin'
import tsParser from '@typescript-eslint/parser'
import svelte from 'eslint-plugin-svelte'
import globals from 'globals'
import svelteParser from 'svelte-eslint-parser'

export default [
  {
    // Browser globals (fetch, document, localStorage, etc.) for all source files
    languageOptions: {
      globals: {
        ...globals.browser,
      },
    },
  },
  js.configs.recommended,
  {
    files: ['src/**/*.ts'],
    languageOptions: {
      parser: tsParser,
      parserOptions: { project: './tsconfig.json' },
      globals: { ...globals.browser },
    },
    plugins: { '@typescript-eslint': ts },
    rules: {
      ...ts.configs['recommended'].rules,
      '@typescript-eslint/no-explicit-any': 'warn',
    },
  },
  {
    files: ['src/**/*.svelte'],
    languageOptions: {
      parser: svelteParser,
      parserOptions: { parser: tsParser },
      globals: { ...globals.browser },
    },
    plugins: { svelte, '@typescript-eslint': ts },
    rules: {
      ...svelte.configs.recommended.rules,
      '@typescript-eslint/no-explicit-any': 'warn',
      // TypeScript function type parameter names in Svelte files are not real JS
      // variables — set args: 'none' to avoid false positives on type signatures
      'no-unused-vars': ['error', { vars: 'all', args: 'none' }],
    },
  },
  {
    ignores: ['dist/', 'node_modules/'],
  },
]
