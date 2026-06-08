import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import VxeTable from 'vxe-table'
import VxePCUI from 'vxe-pc-ui'
import StepEditor from '@/components/StepEditor.vue'
import { STEP_SCHEMAS, type Step, type ActionName } from '@/types/step'

function factory(steps: Step[] = []) {
  return mount(StepEditor, {
    props: { modelValue: steps },
    global: { plugins: [VxeTable, VxePCUI] },
  })
}

describe('StepEditor', () => {
  it('renders empty state', () => {
    const w = factory([])
    expect(w.find('.vxe-table').exists()).toBe(true)
    expect(w.find('.vxe-button').text()).toContain('Add Step')
  })

  it('adds default goto step on click', async () => {
    const w = factory([])
    await w.find('.vxe-button').trigger('click')
    await nextTick()
    const emitted = w.emitted('update:modelValue') as any[]
    expect(emitted).toBeTruthy()
    const steps = emitted[0][0] as Step[]
    expect(steps.length).toBe(1)
    expect(steps[0].action).toBe('goto')
    expect(steps[0].seq).toBe(1)
  })

  it('mounts with steps array', () => {
    const steps: Step[] = [{ seq: 1, action: 'goto', params: { url: 'http://a.com' } }]
    const w = factory(steps)
    expect(w.props().modelValue).toEqual(steps)
  })

  it('all 11 schemas are defined', () => {
    const names: ActionName[] = ['goto','click','fill','expect','check','select','hover','wait','screenshot','scroll','eval']
    for (const n of names) {
      const s = STEP_SCHEMAS[n]
      expect(s).toBeDefined()
      expect(s.action).toBe(n)
      expect(s.params.length).toBeGreaterThanOrEqual(1)
    }
  })
})
