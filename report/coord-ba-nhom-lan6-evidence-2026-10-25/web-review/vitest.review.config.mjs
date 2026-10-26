const worker = 'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w09-assistant/src/web/frontend';
const scratch = 'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r6-web-review-20261025';
export default {
  root: worker,
  cacheDir: scratch + '/vite-cache',
  esbuild: { jsx: 'automatic', jsxImportSource: 'react' },
  resolve: { alias: [
    { find: /^\.\/useAssistant$/, replacement: 'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r6-web-review-20261025/useAssistant.ts' },
    { find: /^react\/jsx-dev-runtime$/, replacement: worker + '/node_modules/react/jsx-dev-runtime.js' },
    { find: /^react\/jsx-runtime$/, replacement: worker + '/node_modules/react/jsx-runtime.js' },
    { find: /^react$/, replacement: worker + '/node_modules/react/index.js' },
    { find: /^vitest$/, replacement: worker + '/node_modules/vitest/dist/index.js' },
    { find: /^@testing-library\/react$/, replacement: worker + '/node_modules/@testing-library/react/dist/index.js' },
    { find: /^@testing-library\/user-event$/, replacement: worker + '/node_modules/@testing-library/user-event/dist/esm/index.js' },
    { find: /^react-router-dom$/, replacement: worker + '/node_modules/react-router-dom/dist/index.mjs' },
  ] },
  test: { environment: 'jsdom', setupFiles: [worker + '/src/test-setup.ts'],
    include: [scratch + '/Assistant.final-usage-race.test.tsx'] },
};
