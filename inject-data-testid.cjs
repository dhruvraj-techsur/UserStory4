/**
 * jscodeshift transform: Inject data-testid into input/button/form elements if neither
 * an id nor data-testid is present.
 */
module.exports = function(fileInfo, api) {
  const j = api.jscodeshift;
  let counter = 0;
  const filename = fileInfo.path.split('/').pop().replace(/\.[\w]+$/, '');

  return j(fileInfo.source)
    .find(j.JSXOpeningElement)
    .forEach(path => {
      const tag = path.node.name.name;
      // Extend to cover more interactive elements
      if (tag === 'input' || tag === 'button' || tag === 'form' || tag === 'select' || tag === 'textarea') {
        const hasTestIdOrId = path.node.attributes.some(
          attr =>
            attr.type === 'JSXAttribute' &&
            attr.name &&
            (attr.name.name === 'data-testid' || attr.name.name === 'id')
        );
        if (!hasTestIdOrId) {
          // Use j.stringLiteral for consistency and proper JSX string attributes
          path.node.attributes.push(
            j.jsxAttribute(
              j.jsxIdentifier('data-testid'),
              j.stringLiteral(`${filename}-${tag}-${counter++}`)
            )
          );
        }
      }
    })
    .toSource({ quote: 'single', reuseWhitespace: true });
}; 