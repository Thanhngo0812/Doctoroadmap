/**
 * verify_figma_plugin_vm.cjs
 * Executes design/figma-plugin/code.js variable setup block in isolated Node VM
 * with an in-memory Figma API stub to produce real output without Cloud access.
 */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const args = process.argv.slice(2);
function getArg(flag, def = null) {
  const idx = args.indexOf(flag);
  return idx !== -1 && idx + 1 < args.length ? args[idx + 1] : def;
}
const hasFlag = (flag) => args.includes(flag);

const codePath = getArg('--code-path', path.join(__dirname, '../design/figma-plugin/code.js'));
const faultVar = getArg('--fault-var', null);
const removeAccounting = hasFlag('--remove-accounting');

let code = fs.readFileSync(codePath, 'utf8');
if (removeAccounting) {
  // Simulate mutant where accounting was stripped
  code = code.replace(/variableReport\.created \+= 1;/g, '/* accounting removed */');
}

const conversions = code.slice(code.indexOf('    function rgbaToFigma'), code.indexOf('  const C ='));
const setup = code.slice(code.indexOf('  // 2b. Native Figma Variables Setup'), code.indexOf('  // Helper creators'));

const collections = [];
const variables = [];
const notifications = [];

const figma = {
  variables: {
    getLocalVariableCollections: () => collections,
    createVariableCollection: (name) => {
      const col = {
        name,
        id: 'col_' + collections.length,
        modes: [{ modeId: 'mode_light', name: 'Mode 1' }],
        renameMode: (id, name) => {
          const m = col.modes.find(x => x.modeId === id);
          if (m) m.name = name;
        },
        addMode: (name) => {
          const id = 'mode_dark';
          col.modes.push({ modeId: id, name });
          return id;
        }
      };
      collections.push(col);
      return col;
    },
    createVariable: (name, collection, type) => {
      if (faultVar && name === faultVar) {
        throw new Error('Forced creation failure for ' + name);
      }
      const v = {
        name,
        collectionId: collection.id,
        type,
        valuesByMode: {},
        setValueForMode: (modeId, val) => {
          v.valuesByMode[modeId] = val;
        }
      };
      variables.push(v);
      return v;
    }
  },
  notify: (msg, opts) => {
    notifications.push({ msg, opts });
  }
};

(async () => {
  await vm.runInNewContext('(async () => {' + conversions + setup + '})()', {
    figma,
    console: { log: () => {}, error: () => {} },
    hexToRgb: (hex) => ({ r: 1, g: 1, b: 1 }),
    Math,
    parseInt
  });

  const report = figma.__variableReport;
  const result = {
    report,
    notifications,
    variableCount: variables.length,
    variables: variables.map(v => ({ name: v.name, type: v.type, valuesByMode: v.valuesByMode }))
  };
  process.stdout.write(JSON.stringify(result));
})().catch(err => {
  process.stderr.write(String(err));
  process.exit(1);
});
