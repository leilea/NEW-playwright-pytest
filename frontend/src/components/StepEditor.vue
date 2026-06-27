<template>
  <div class="step-editor">
    <vxe-table
      :data="steps"
      :edit-config="{ trigger: 'click', mode: 'cell' }"
      @edit-closed="onEditClosed"
    >
      <vxe-column field="seq" title="#" width="50" />
      <vxe-column field="action" title="Action" width="140">
        <template #default="{ row }">
          <vxe-select v-model="row.action" @change="({ value }: any) => changeAction(row, value)">
            <vxe-option v-for="a in actionNames" :key="a" :value="a" :label="STEP_SCHEMAS[a].label" />
          </vxe-select>
        </template>
      </vxe-column>
      <vxe-column title="Parameters" min-width="350">
        <template #default="{ row }">
          <template v-for="f in stepSchema(row.action).params" :key="f.key">
            <template v-if="f.key === 'selector'">
              <vxe-input
                :modelValue="editCache.get(row) || ''"
                @update:modelValue="(v: any) => editCache.set(row, String(v ?? ''))"
                @blur="onLocatorBlur(row)"
                placeholder="locator"
                style="width:720px;margin-right:6px"
              />
            </template>
            <template v-else-if="f.key === 'value' && row.selector">
              <span style="margin:0 2px;color:var(--el-border-color);font-size:14px">|</span>
              <vxe-input v-model="row.value" style="width:280px" />
            </template>
            <template v-else-if="f.key === 'url'">
              <vxe-input v-model="row.url" placeholder="https://..." style="width:720px;margin-right:8px" />
            </template>
            <template v-else>
              <label style="margin-right:4px">{{ f.label }}</label>
              <vxe-input
                v-if="f.type === 'text'"
                 v-model="row[f.key]"
                :placeholder="f.placeholder || ''"
                style="width:140px;margin-right:8px"
              />
              <vxe-input
                v-else-if="f.type === 'number'"
                 v-model.number="row[f.key]"
                type="number"
                style="width:100px;margin-right:8px"
              />
              <vxe-select
                v-else-if="f.type === 'select'"
                 v-model="row[f.key]"
                style="width:120px;margin-right:8px"
              >
                <vxe-option v-for="o in f.opts" :key="o" :value="o" :label="o" />
              </vxe-select>
            </template>
          </template>
        </template>
      </vxe-column>
      <vxe-column title="Notes" width="120">
        <template #default="{ row }">
          <vxe-input v-model="row.note" placeholder="标识/说明" style="width:100%" />
        </template>
      </vxe-column>
      <vxe-column title="Move" width="70">
        <template #default="{ $rowIndex }">
          <vxe-button size="mini" icon="vxe-icon-arrow-up" :disabled="$rowIndex === 0" @click="moveUp($rowIndex)" />
          <vxe-button size="mini" icon="vxe-icon-arrow-down" :disabled="$rowIndex === steps.length - 1" @click="moveDown($rowIndex)" />
        </template>
      </vxe-column>
      <vxe-column title="Ops" width="70">
        <template #default="{ $rowIndex }">
          <vxe-button size="mini" icon="vxe-icon-copy" @click="copyStep($rowIndex)" />
          <vxe-button size="mini" icon="vxe-icon-delete" status="danger" @click="removeStep($rowIndex)" />
        </template>
      </vxe-column>
    </vxe-table>
    <vxe-button @click="addStep" style="margin-top:8px">+ Add Step</vxe-button>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { type Step, type ActionName, ACTION_NAMES, STEP_SCHEMAS } from '../types/step'
import { selectorToLocator, locatorToSelector } from '../utils/locator'

const props = defineProps<{ modelValue: Step[] }>()
const emit = defineEmits<{ 'update:modelValue': [val: Step[]] }>()

const actionNames = ACTION_NAMES

const steps = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const editCache = reactive(new Map<Step, string>())

watch(() => props.modelValue, (steps) => {
  editCache.clear()
  for (const s of steps) {
    editCache.set(s, selectorToLocator(String(s.selector || '')).replace(/page\./g, ''))
  }
}, { immediate: true, deep: true })

function onLocatorBlur(row: Step) {
  const val = editCache.get(row) || ''
  if (!val) return
  const expr = val.startsWith('page.') ? val : 'page.' + val
  row.selector = locatorToSelector(expr)
  editCache.set(row, selectorToLocator(String(row.selector)).replace(/page\./g, ''))
}

function flushEditCache() {
  const entries = Array.from(editCache.entries())
  for (const [row, val] of entries) {
    const expr = val.startsWith('page.') ? val : 'page.' + val
    row.selector = locatorToSelector(expr)
  }
  editCache.clear()
}

defineExpose({ flushEditCache })

function defaultParams(action: ActionName): Record<string, string | number> {
  const p: Record<string, string | number> = {}
  for (const f of STEP_SCHEMAS[action].params) p[f.key] = ''
  return p
}

function addStep() {
  const seq = steps.value.length + 1
  steps.value = [...steps.value, { seq, action: 'goto' as ActionName, url: '' }]
}

function copyStep(idx: number) {
  const arr = [...steps.value]
  const clone = JSON.parse(JSON.stringify(arr[idx]))
  arr.splice(idx + 1, 0, clone)
  arr.forEach((s, i) => s.seq = i + 1)
  steps.value = arr
}

function removeStep(idx: number) {
  const arr = [...steps.value]
  arr.splice(idx, 1)
  arr.forEach((s, i) => s.seq = i + 1)
  steps.value = arr
}

function moveUp(idx: number) {
  if (idx === 0) return
  const arr = [...steps.value]
  ;[arr[idx - 1], arr[idx]] = [arr[idx], arr[idx - 1]]
  arr.forEach((s, i) => (s.seq = i + 1))
  steps.value = arr
}

function moveDown(idx: number) {
  if (idx >= steps.value.length - 1) return
  const arr = [...steps.value]
  ;[arr[idx + 1], arr[idx]] = [arr[idx], arr[idx + 1]]
  arr.forEach((s, i) => (s.seq = i + 1))
  steps.value = arr
}

function changeAction(row: Step, newAction: string) {
  const oldAction = row.action
  row.action = newAction as ActionName
  if (newAction !== oldAction) {
    const defs = defaultParams(newAction as ActionName)
    Object.keys(row).forEach(k => { if (k !== 'seq' && k !== 'action') delete (row as any)[k] })
    Object.assign(row, defs)
  }
}

function stepSchema(action: ActionName) {
  return STEP_SCHEMAS[action] || STEP_SCHEMAS.goto
}

function onEditClosed() {}
</script>
