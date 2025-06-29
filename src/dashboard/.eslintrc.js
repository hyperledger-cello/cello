/*
 SPDX-License-Identifier: Apache-2.0
*/
module.exports = {
  parser: '@babel/eslint-parser',
  parserOptions: {
    requireConfigFile: false,
    babelOptions: {
      presets: ['@babel/preset-react'],
      plugins: [['@babel/plugin-proposal-decorators', { legacy: true }]],
    },
    ecmaFeatures: {
      legacyDecorators: true,
    },
  },
  extends: ['airbnb', 'prettier', 'plugin:compat/recommended'],
  plugins: ['react-hooks'],
  env: {
    browser: true,
    node: true,
    es6: true,
    mocha: true,
    jest: true,
    jasmine: true,
  },
  globals: {
    ANT_DESIGN_PRO_ONLY_DO_NOT_USE_IN_YOUR_PRODUCTION: true, // preview.pro.ant.design only do not use in your production ; preview.pro.ant.design 专用环境变量，请不要在你的项目中使用它。
    page: true,
  },
  rules: {
    'react/jsx-filename-extension': [1, { extensions: ['.js'] }],
    'react/jsx-wrap-multilines': 0,
    'react/prop-types': 0,
    'react/forbid-prop-types': 0,
    'react/jsx-one-expression-per-line': 0,
    'import/no-unresolved': [2, { ignore: ['^@/', '^umi/'] }],
    'import/no-extraneous-dependencies': [
      2,
      {
        optionalDependencies: true,
        devDependencies: ['**/tests/**.js', '/mock/**/**.js', '**/**.test.js'],
      },
    ],
    'import/no-cycle': 0,
    'jsx-a11y/no-noninteractive-element-interactions': 0,
    'jsx-a11y/click-events-have-key-events': 0,
    'jsx-a11y/no-static-element-interactions': 0,
    'jsx-a11y/anchor-is-valid': 0,
    'linebreak-style': 0,
    'prefer-destructuring': 0,
    'react/jsx-props-no-spreading': 0,
    'react/function-component-definition': 0,
    'react/react-in-jsx-scope': 0,
    'react-hooks/rules-of-hooks': 'off',
    'react-hooks/exhaustive-deps': 'warn',
    'import/extensions': 0,
    'react/state-in-constructor': 0,
    'react/static-property-placement': 0,
    'class-methods-use-this': 0,
    'react/jsx-fragments': 0,
    'react/jsx-no-useless-fragment': 0,
    'react/no-arrow-function-lifecycle': 0,
    'react/no-unstable-nested-components': 0,
    'react/no-unused-class-component-methods': 0,
    'arrow-body-style': 0,
    'no-useless-catch': 0,
    'compat/compat': 0,
    'import/order': 0,
    'react/jsx-curly-brace-presence': 0,
    'default-case-last': 0,
    'prefer-regex-literals': 0,
  },
  settings: {
    polyfills: ['fetch', 'promises', 'url', 'object-assign'],
    'import/resolver': {
      node: {
        extensions: ['.js', '.jsx', '.ts', '.tsx'],
      },
    },
  },
};
