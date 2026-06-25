<template>
  <div class="parameter-config">
    <div class="parameter-config-header">
      <span class="parameter-config-title">参数配置</span>
      <span class="parameter-config-hint" v-text="'参数名输入格式示例: username 或 {{username}}'"></span>
    </div>

    <div v-if="params.length === 0" class="parameter-config-empty">
      暂无参数，点击"添加参数"按钮添加
    </div>

    <div v-else class="parameter-config-list">
      <div
        v-for="(item, index) in params"
        :key="index"
        class="parameter-config-row"
      >
        <el-input
          :model-value="item.key"
          placeholder="参数名"
          class="param-key"
          @update:model-value="updateParam(index, 'key', $event)"
        />
        <div class="param-value-wrap">
          <el-input
            :model-value="item.value"
            placeholder="参数值或选择类型"
            class="param-value-input"
            @update:model-value="updateParam(index, 'value', $event)"
          />
          <el-popover
            :visible="dropdownIndex === index"
            placement="bottom-start"
            :width="240"
            trigger="click"
            @show="dropdownIndex = index"
            @hide="dropdownIndex = null"
          >
            <template #reference>
              <el-button
                class="param-value-type-btn"
                size="small"
                @click="dropdownIndex = dropdownIndex === index ? null : index"
              >
                <el-icon><MagicStick /></el-icon>
              </el-button>
            </template>
            <div class="value-type-list">
              <div
                v-for="opt in valueTypeOptions"
                :key="opt.value"
                class="value-type-item"
                @click="insertValueType(index, opt)"
              >
                <el-icon class="value-type-icon"><component :is="opt.icon" /></el-icon>
                <div>
                  <div class="value-type-label">{{ opt.label }}</div>
                  <div class="value-type-desc">{{ opt.description }}</div>
                </div>
              </div>
            </div>
          </el-popover>
        </div>
        <el-input
          :model-value="item.description"
          placeholder="描述"
          class="param-desc"
          @update:model-value="updateParam(index, 'description', $event)"
        />
        <el-button
          class="param-delete-btn"
          size="small"
          type="danger"
          :icon="Delete"
          circle
          @click="deleteParam(index)"
        />
      </div>
    </div>

    <el-button class="param-add-btn" type="primary" :icon="Plus" @click="addParam">
      添加参数
    </el-button>

    <el-dialog
      v-model="showOffsetDialog"
      title="设置偏移量"
      width="360px"
      :close-on-click-modal="false"
    >
      <el-form>
        <el-form-item :label="offsetLabel">
          <el-input-number
            v-model="offsetValue"
            :min="0"
            :max="999"
            controls-position="right"
            class="offset-input"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showOffsetDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmOffset">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Calendar, Clock, Key, Edit, Delete, Plus, MagicStick } from '@element-plus/icons-vue'
import type { Parameter } from '@/types'

const props = defineProps<{
  modelValue: Parameter[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: Parameter[]]
}>()

const params = ref<Parameter[]>([...props.modelValue])
const dropdownIndex = ref<number | null>(null)
const showOffsetDialog = ref(false)
const offsetValue = ref(0)
const offsetTargetIndex = ref(0)
const offsetType = ref('')
const offsetLabel = ref('')

const valueTypeOptions = [
  { label: '随机数字',       value: '{{random:6}}',        icon: Key,      description: '6位随机数字',         hasOffset: false },
  { label: '随机字符串',     value: '{{randomStr:8}}',     icon: Edit,     description: '8位随机字符串',       hasOffset: false },
  { label: '当前日期',       value: '{{date}}',             icon: Calendar, description: 'YYYY-MM-DD',            hasOffset: false },
  { label: '当前时间',       value: '{{time}}',             icon: Clock,    description: 'HH:mm:ss',             hasOffset: false },
  { label: '日期时间',       value: '{{datetime}}',         icon: Calendar, description: 'YYYY-MM-DD HH:mm:ss',  hasOffset: false },
  { label: '时间戳',         value: '{{timestamp}}',        icon: Key,      description: '13位时间戳',           hasOffset: false },
  { label: '时间+小时',      value: 'timeAdd',              icon: Clock,    description: '当前时间+N小时',       hasOffset: true, offsetUnit: '小时' },
  { label: '时间-小时',      value: 'timeSub',              icon: Clock,    description: '当前时间-N小时',       hasOffset: true, offsetUnit: '小时' },
  { label: '日期+天',        value: 'dateAdd',              icon: Calendar, description: '当前日期+N天',         hasOffset: true, offsetUnit: '天' },
  { label: '日期-天',        value: 'dateSub',              icon: Calendar, description: '当前日期-N天',         hasOffset: true, offsetUnit: '天' },
]

function addParam() {
  params.value.push({ key: '', value: '', description: '' })
  emitUpdate()
}

function updateParam(index: number, field: keyof Parameter, value: string) {
  params.value[index] = { ...params.value[index], [field]: value }
  emitUpdate()
}

function deleteParam(index: number) {
  params.value.splice(index, 1)
  emitUpdate()
}

function emitUpdate() {
  emit('update:modelValue', [...params.value])
}

function insertValueType(index: number, opt: typeof valueTypeOptions[number]) {
  dropdownIndex.value = null
  if (opt.hasOffset) {
    offsetTargetIndex.value = index
    offsetType.value = opt.value
    offsetLabel.value = `偏移量(${opt.offsetUnit})`
    offsetValue.value = 0
    showOffsetDialog.value = true
  } else {
    const current = params.value[index].value || ''
    updateParam(index, 'value', current + opt.value)
  }
}

function confirmOffset() {
  const unit = offsetType.value.startsWith('time') ? 'h' : 'd'
  const sign = offsetType.value.endsWith('Add') ? '+' : offsetType.value.endsWith('Sub') ? '+' : '+'
  const suffix = `{{${offsetType.value}:${unit}${sign}${offsetValue.value}}}`
  const current = params.value[offsetTargetIndex.value].value || ''
  updateParam(offsetTargetIndex.value, 'value', current + suffix)
  showOffsetDialog.value = false
}
</script>

<style scoped>
.parameter-config {
  margin-bottom: 16px;
  padding: 12px 16px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  background: var(--el-fill-color-blank);
}

.parameter-config-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.parameter-config-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.parameter-config-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.parameter-config-empty {
  color: var(--el-text-color-placeholder);
  font-size: 13px;
  padding: 8px 0;
  margin-bottom: 8px;
}

.parameter-config-list {
  margin-bottom: 8px;
}

.parameter-config-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.param-key {
  width: 160px;
  flex-shrink: 0;
}

.param-value-wrap {
  display: flex;
  align-items: center;
  gap: 0;
  flex: 1;
}

.param-value-input {
  flex: 1;
}

.param-value-type-btn {
  border-radius: 0 4px 4px 0;
  margin-left: -1px;
  border-left: none;
}

.param-desc {
  width: 160px;
  flex-shrink: 0;
}

.param-delete-btn {
  flex-shrink: 0;
}

.param-add-btn {
  margin-top: 4px;
}

.value-type-list {
  max-height: 320px;
  overflow-y: auto;
}

.value-type-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.15s;
}

.value-type-item:hover {
  background: var(--el-fill-color-light);
}

.value-type-icon {
  font-size: 18px;
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.value-type-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.value-type-desc {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.offset-input {
  width: 100%;
}
</style>
