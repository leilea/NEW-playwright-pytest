export const ACTION_NAMES = [
  'goto', 'click', 'fill', 'expect', 'check', 'uncheck',
  'select', 'hover', 'wait', 'wait_for_load_state',
  'screenshot', 'scroll', 'eval',
] as const

export type ActionName = (typeof ACTION_NAMES)[number]

export interface FieldSpec {
  key: string
  label: string
  type: 'text' | 'number' | 'select'
  opts?: string[]
  placeholder?: string
}

export interface ActionSpec {
  action: ActionName
  label: string
  params: FieldSpec[]
}

export interface Step {
  seq: number
  action: ActionName
  note?: string
  [key: string]: string | number | undefined
}

export const STEP_SCHEMAS: Record<ActionName, ActionSpec> = {
  goto:      { action: 'goto',      label: 'Navigate',       params: [{ key: 'url', label: 'URL', type: 'text', placeholder: 'https://...' }] },
  click:     { action: 'click',     label: 'Click',          params: [{ key: 'selector', label: 'Selector', type: 'text', placeholder: '#id / .class / text=' }] },
  fill:      { action: 'fill',      label: 'Fill Input',     params: [{ key: 'selector', label: 'Selector', type: 'text' }, { key: 'value', label: 'Value', type: 'text' }] },
  expect:    { action: 'expect',    label: 'Assert',         params: [{ key: 'selector', label: 'Selector', type: 'text' }, { key: 'state', label: 'State', type: 'select', opts: ['visible', 'hidden', 'enabled', 'disabled', 'editable'] }, { key: 'text', label: 'Contains', type: 'text', placeholder: '(optional)' }] },
  check:     { action: 'check',     label: 'Checkbox',       params: [{ key: 'selector', label: 'Selector', type: 'text' }, { key: 'state', label: 'State', type: 'select', opts: ['check', 'uncheck'] }] },
  uncheck:   { action: 'uncheck',   label: 'Uncheck',         params: [{ key: 'selector', label: 'Selector', type: 'text' }] },
  select:    { action: 'select',    label: 'Select Dropdown', params: [{ key: 'selector', label: 'Selector', type: 'text' }, { key: 'value', label: 'Value', type: 'text' }] },
  hover:     { action: 'hover',     label: 'Hover',          params: [{ key: 'selector', label: 'Selector', type: 'text' }] },
  wait:      { action: 'wait',      label: 'Wait',           params: [{ key: 'ms', label: 'Milliseconds', type: 'number', placeholder: '1000' }] },
  wait_for_load_state: { action: 'wait_for_load_state', label: 'Wait Load State', params: [{ key: 'state', label: 'State', type: 'select', opts: ['domcontentloaded', 'load', 'networkidle'] }] },
  screenshot:{ action: 'screenshot',label: 'Screenshot',     params: [{ key: 'name', label: 'Name', type: 'text', placeholder: '(optional)' }] },
  scroll:    { action: 'scroll',    label: 'Scroll',         params: [{ key: 'x', label: 'X', type: 'number', placeholder: '0' }, { key: 'y', label: 'Y', type: 'number', placeholder: '0' }] },
  eval:      { action: 'eval',      label: 'Evaluate JS',    params: [{ key: 'code', label: 'JS Code', type: 'text', placeholder: 'document.title' }] },
}
