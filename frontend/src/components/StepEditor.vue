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
          <vxe-select v-model="row.action" @change="(v:string) => changeAction(row, v)">
            <vxe-option v-for="a in actionNames" :key="a" :value="a" :label="STEP_SCHEMAS[a].label" />
          </vxe-select>
        </template>
      </vxe-column>
      <vxe-column title="Parameters" min-width="300">
        <template #default="{ row }">
          <template v-for="f in stepSchema(row.action).params" :key="f.key">
            <label style="margin-right:4px">{{ f.label }}</label>
            <vxe-input
              v-if="f.type === 'text'"
              v-model="row.params[f.key]"
              :placeholder="f.placeholder || ''"
              style="width:140px;margin-right:8px"
            />
            <vxe-input
              v-else-if="f.type === 'number'"
              v-model.number="row.params[f.key]"
              type="number"
              style="width:100px;margin-right:8px"
            />
            <vxe-select
              v-else-if="f.type === 'select'"
              v-model="row.params[f.key]"
              style="width:120px;margin-right:8px"
            >
              <vxe-option v-for="o in f.opts" :key="o" :value="o" :label="o" />
            </vxe-select>
          </template>
        </template>
      </vxe-column>
      <vxe-column title="Ops" width="100">
        <template #default="{ row, $rowIndex }">
          <vxe-button size="mini" icon="vxe-icon-arrow-up" :disabled="$rowIndex === 0" @click="moveUp($rowIndex)" />
          <vxe-button size="mini" icon="vxe-icon-arrow-down" :disabled="$rowIndex === steps.length - 1" @click="moveDown($rowIndex)" />
          <vxe-button size="mini" icon="vxe-icon-delete" status="danger" @click="removeStep($rowIndex)" />
        </template>
      </vxe-column>
    </vxe-table>
    <vxe-button @click="addStep" style="margin-top:8px">+ Add Step</vxe-button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { type Step, type ActionName, ACTION_NAMES, STEP_SCHEMAS } from '../types/step'

const props = defineProps<{ modelValue: Step[] }>()
const emit = defineEmits<{ 'update:modelValue': [val: Step[]] }>()

const actionNames = ACTION_NAMES

const steps = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

function emptyParams(action: ActionName): Record<string, string | number> {
  const p: Record<string, string | number> = {}
  for (const f of STEP_SCHEMAS[action].params) p[f.key] = ''
  return p
}

function addStep() {
  const seq = steps.value.length + 1
  steps.value = [...steps.value, { seq, action: 'goto' as ActionName, params: { url: '' } }]
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
  row.action = newAction as ActionName
  row.params = emptyParams(newAction as ActionName)
}

function stepSchema(action: ActionName) {
  return STEP_SCHEMAS[action] || STEP_SCHEMAS.goto
}

function onEditClosed() {}
</script>
