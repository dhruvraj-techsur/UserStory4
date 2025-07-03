const fs = require('fs');
const path = require('path');
const glob = require('glob');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;

const locators = {};

// Normalize value into a simple lowercase key
function normalizeKey(value) {
  // 1) If it matches Component-key-n, strip off prefix & suffix
  const m = /^.+\-([^\-]+)\-\d+$/.exec(value);
  if (m) {
    return m[1].toLowerCase();
  }
  // 2) Fallback: slugify everything else
  return value
    .toString()
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_');
}

// Build selector info object
function makeInfo(type, value) {
  if (type === 'id') {
    return { by: 'id', selector: `#${value}`, value };
  }
  if (type === 'data-testid') {
    return { by: 'css selector', selector: `[data-testid='${value}']`, value };
  }
  return null;
}

// Walk through all your JSX/TSX
function extract() {
  glob.sync('github_code/**/*.{js,jsx,ts,tsx}', { ignore: ['**/node_modules/**'] })
    .forEach(filePath => {
      let source = fs.readFileSync(filePath, 'utf8');
      let ast;
      try {
        ast = parser.parse(source, {
          sourceType: 'module',
          plugins: ['jsx','typescript'],
        });
      } catch (e) {
        console.warn(`⚠️  parse error in ${filePath}: ${e.message}`);
        return;
      }

      traverse(ast, {
        // 1) id & data-testid attributes
        JSXOpeningElement(path) {
          const tag = path.node.name.name;
          path.node.attributes.forEach(attr => {
            if (attr.type !== 'JSXAttribute' || !attr.name) return;
            const name = attr.name.name;
            let value = null;
            if (attr.value?.type === 'StringLiteral') {
              value = attr.value.value;
            }
            else if (attr.value?.type === 'JSXExpressionContainer' &&
                     attr.value.expression.type === 'Identifier') {
              value = attr.value.expression.name;
            }
            // only auto‐map data-testid on non-button tags here;
            // buttons get mapped by their innerText in JSXElement below
            if (
              (name === 'id') ||
              (name === 'data-testid' && tag !== 'button')
            ) {
              const key  = normalizeKey(value);
              if (!locators[key]) {
                const info = makeInfo(name, value);
                if (info) {
                  locators[key] = info;
                  console.log(`Found locator: ${key} -> ${info.selector}`);
                }
              }
            }
          });
        },

        // 2) labels: map label text -> htmlFor
        JSXElement(path) {
          const elName = path.node.openingElement.name.name;
          if (elName === 'label') {
            // find htmlFor attr
            const htmlForAttr = path.node.openingElement.attributes
              .find(a => a.type==='JSXAttribute' && a.name.name==='htmlFor');
            if (htmlForAttr && htmlForAttr.value?.type==='StringLiteral') {
              const htmlFor = htmlForAttr.value.value;
              // find the text child
              const textNode = path.node.children.find(c => c.type==='JSXText');
              if (textNode && textNode.value.trim()) {
                const key = normalizeKey(textNode.value);
                if (!locators[key]) {
                  locators[key] = { by:'id', selector:`#${htmlFor}`, value: htmlFor };
                  console.log(`Found label locator: ${key} -> #${htmlFor}`);
                }
              }
            }
          }

          // 3) buttons: map button innerText -> data-testid or fallback
          if (elName === 'button') {
            // compute a selector: prefer data-testid if present
            const attrs = path.node.openingElement.attributes;
            const testIdAttr = attrs.find(a => a.type==='JSXAttribute' && a.name.name==='data-testid');
            let selector, value;
            if (testIdAttr?.value?.type==='StringLiteral') {
              value = testIdAttr.value.value;
              selector = `[data-testid='${value}']`;
            } else {
              // fallback: use tag name and position, but better to have test-id
              return;
            }
            // button innerText → e.g. "Login" → key "login"
            const textNode = path.node.children.find(c => c.type==='JSXText');
            if (textNode && textNode.value.trim()) {
              const key = normalizeKey(textNode.value);
              if (!locators[key]) {
                locators[key] = { by:'css selector', selector, value };
                console.log(`Found button locator: ${key} -> ${selector}`);
              }
            }
          }
        }
      });
    });
}

// write out
extract();
const outDir = path.join(process.cwd(),'config');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);
fs.writeFileSync(path.join(outDir,'locators.json'),
                 JSON.stringify(locators, null, 2));
console.log('✅ locators.json keys →', Object.keys(locators).join(', ')); 