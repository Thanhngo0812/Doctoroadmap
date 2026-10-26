const fs = require('fs');
const vm = require('vm');

function testHtml(htmlPath, variant) {
  let html = fs.readFileSync(htmlPath, 'utf8');

  if (variant === 'inverted') {
    if (!html.includes('cardGroup === group')) throw new Error('Cannot find cardGroup === group');
    html = html.replace('cardGroup === group', 'cardGroup !== group');
  } else if (variant === 'old-origin') {
    html = html.replace(/function filterLibrary\(group, tabBtn\)[\s\S]*?\}\s*<\/script>/, 
      `function filterLibrary(group, tabBtn) {
        document.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
        tabBtn.classList.add('active');
        const cards = document.querySelectorAll('.doc-card');
        cards.forEach(card => {
          const origin = card.getAttribute('data-origin');
          if (group === 'all' || origin === (group === 'here' ? 'button' : 'assistant')) {
            card.style.display = 'flex';
          } else {
            card.style.display = 'none';
          }
        });
      }
    </script>`);
  }

  const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/i);
  if (!scriptMatch) throw new Error('No script tag found');
  const scriptCode = scriptMatch[1];

  const cardRegex = /<div class="doc-card"[^>]*data-group="([^"]+)"[^>]*data-origin="([^"]+)"[\s\S]*?<h3[^>]*>([\s\S]*?)<\/h3>/g;
  const cards = [];
  let m;
  while ((m = cardRegex.exec(html)) !== null) {
    cards.push({
      group: m[1],
      origin: m[2],
      title: m[3].trim(),
      style: { display: 'flex' },
      getAttribute(attr) {
        if (attr === 'data-group') return this.group;
        if (attr === 'data-origin') return this.origin;
        return null;
      },
      dataset: { group: m[1], origin: m[2] }
    });
  }

  const tabs = {
    'all': { id: 'tab-lib-all', classList: { list: new Set(['active']), add(c) { this.list.add(c); }, remove(c) { this.list.delete(c); } } },
    'here': { id: 'tab-lib-here', classList: { list: new Set(), add(c) { this.list.add(c); }, remove(c) { this.list.delete(c); } } },
    'elsewhere': { id: 'tab-lib-elsewhere', classList: { list: new Set(), add(c) { this.list.add(c); }, remove(c) { this.list.delete(c); } } }
  };

  // Checkbox inputs for updateScopeCount
  const checkboxes = Array.from({ length: 8 }, (_, i) => ({
    checked: i < 2, // initial 2
    type: 'checkbox'
  }));

  const indicator = { textContent: '', className: '' };
  const warning = { style: { display: 'none' } };
  const btnCreate = {
    attributes: {},
    style: {},
    setAttribute(k, v) { this.attributes[k] = v; },
    removeAttribute(k) { delete this.attributes[k]; }
  };

  const sandbox = {
    document: {
      documentElement: { getAttribute: () => 'light', setAttribute: () => {} },
      querySelectorAll: (sel) => {
        if (sel === '.filter-tab') return Object.values(tabs);
        if (sel === '.doc-card') return cards;
        if (sel === '.module-chips input:checked') return checkboxes.filter(c => c.checked);
        return [];
      },
      getElementById: (id) => {
        if (id === 'scope-count-indicator') return indicator;
        if (id === 'scope-warning-box') return warning;
        if (id === 'btn-create-document') return btnCreate;
        return null;
      }
    },
    console: console
  };

  vm.createContext(sandbox);
  vm.runInContext(scriptCode, sandbox);

  // 1. Test Filter Behavior
  sandbox.filterLibrary('here', tabs['here']);
  const visibleHere = cards.filter(c => c.style.display !== 'none').map(c => c.title);

  sandbox.filterLibrary('elsewhere', tabs['elsewhere']);
  const visibleElsewhere = cards.filter(c => c.style.display !== 'none').map(c => c.title);

  sandbox.filterLibrary('all', tabs['all']);
  const visibleAll = cards.filter(c => c.style.display !== 'none').map(c => c.title);

  // 2. Test Scope Boundary Behavior: 5 -> 6 -> 5
  // Set 5 checkboxes checked
  checkboxes.forEach((c, idx) => { c.checked = idx < 5; });
  sandbox.updateScopeCount();
  const at5_disabled = btnCreate.attributes['disabled'] === 'true';
  const at5_warning = warning.style.display === 'block';

  // Set 6 checkboxes checked
  checkboxes.forEach((c, idx) => { c.checked = idx < 6; });
  sandbox.updateScopeCount();
  const at6_disabled = btnCreate.attributes['disabled'] === 'true';
  const at6_warning = warning.style.display === 'block';

  // Return to 5 checkboxes checked
  checkboxes.forEach((c, idx) => { c.checked = idx < 5; });
  sandbox.updateScopeCount();
  const back5_disabled = btnCreate.attributes['disabled'] === 'true';
  const back5_warning = warning.style.display === 'block';

  return {
    visibleHere,
    visibleElsewhere,
    visibleAll,
    scopeBoundary: {
      at5: { disabled: at5_disabled, warning: at5_warning },
      at6: { disabled: at6_disabled, warning: at6_warning },
      back5: { disabled: back5_disabled, warning: back5_warning }
    }
  };
}

const targetPath = process.argv[2] || 'design/preview/w10_quiz_screens.html';
const variant = process.argv[3] || 'normal';

const res = testHtml(targetPath, variant);
console.log(JSON.stringify(res));
