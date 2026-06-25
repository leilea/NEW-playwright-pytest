export function selectorToLocator(sel: string): string {
  if (!sel) return ''

  let parent: string | undefined
  let rest = sel
  if (rest.includes(' > ')) {
    const idx = rest.lastIndexOf(' > ')
    parent = rest.slice(0, idx)
    rest = rest.slice(idx + 3)
  }

  if (rest.includes('|')) {
    const pipeIdx = rest.lastIndexOf('|')
    const afterPipe = rest.slice(pipeIdx + 1)
    if (/^[a-zA-Z][a-zA-Z0-9_-]*$/.test(afterPipe)) {
      rest = rest.slice(0, pipeIdx)
    }
  }

  const inner = _toLocatorRaw(rest)
  if (parent) {
    const pp = _toLocatorRaw(parent)
    if (!pp) return parent
    const innerSuffix = inner.replace(/^page\./, '')
    return `${pp}.${innerSuffix}`
  }
  return inner
}

function _toLocatorRaw(sel: string): string {
  if (sel.startsWith('__testid:')) return `page.get_by_test_id(${_q(sel.slice(9))})`
  if (sel.startsWith('__role:')) {
    const rest = sel.slice(7)
    const ci = rest.indexOf(':')
    if (ci > 0) return `page.get_by_role(${_q(rest.slice(0, ci))}, name=${_q(rest.slice(ci + 1))}, exact=True)`
    return `page.get_by_role(${_q(rest)})`
  }
  if (sel.startsWith('__label:')) return `page.get_by_label(${_q(sel.slice(8))})`
  if (sel.startsWith('__placeholder:')) return `page.get_by_placeholder(${_q(sel.slice(14))})`
  if (sel.startsWith('__text:')) return `page.get_by_text(${_q(sel.slice(7))}, exact=True)`
  if (sel.startsWith('__alt:')) return `page.get_by_alt_text(${_q(sel.slice(6))})`
  if (sel.startsWith('__title:')) return `page.get_by_title(${_q(sel.slice(8))})`
  return `page.locator(${_q(sel)})`
}

export function locatorToSelector(loc: string): string {
  if (!loc) return ''

  let parent = ''
  let rest = loc
  const arrowIdx = loc.lastIndexOf(' > ')
  if (arrowIdx > 0) {
    parent = loc.slice(0, arrowIdx)
    rest = loc.slice(arrowIdx + 3)
  }

  const m = rest.match(/^page\.(.+?)\((.+)\)$/)
  if (!m) return loc

  const method = m[1]
  const args = m[2]

  let inner = ''
  if (method === 'get_by_label') { inner = '__label:' + _unquote(args) }
  else if (method === 'get_by_placeholder') { inner = '__placeholder:' + _unquote(args) }
  else if (method === 'get_by_test_id') { inner = '__testid:' + _unquote(args) }
  else if (method === 'get_by_text') { const v = _unquote(args.split(',')[0]); inner = '__text:' + v }
  else if (method === 'get_by_alt_text') { inner = '__alt:' + _unquote(args) }
  else if (method === 'get_by_title') { inner = '__title:' + _unquote(args) }
  else if (method === 'get_by_role') {
    const parts = args.split(',')
    const role = _unquote(parts[0].trim())
    const namePart = parts.find(p => p.trim().startsWith('name='))
    const name = namePart ? _unquote(namePart.split('=').slice(1).join('=').trim()) : ''
    inner = name ? `__role:${role}:${name}` : `__role:${role}`
  }
  else if (method === 'locator') { inner = _unquote(args) }
  else { return loc }

  return parent ? `${parent} > ${inner}` : inner
}

function _q(v: string): string {
  return JSON.stringify(v)
}

function _unquote(s: string): string {
  const t = s.trim()
  if ((t.startsWith('"') && t.endsWith('"')) || (t.startsWith("'") && t.endsWith("'"))) {
    return JSON.parse(t)
  }
  return t
}
