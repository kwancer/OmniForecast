<template>
  <v-card class="pa-4 mb-2 bg-surface" variant="outlined" :class="{ 'on-ignore': localState.isIgnored }">
    <div class="d-flex align-center flex-wrap" style="gap: 8px; line-height: 2.0;">
      <span class="text-medium-emphasis">In the future, I expect </span>

      <b class="text-primary font-weight-bold">{{ column }}</b>

      <span class="text-medium-emphasis"> to </span>

      <v-menu>
        <template #activator="{ props }">
          <v-chip
            v-bind="props"
            :color="getChipColor"
            class="font-weight-bold"
            size="large"
            variant="tonal"
          >
            {{ getOptionLabel }} <v-icon end icon="mdi-chevron-down" />
          </v-chip>
        </template>
        <v-list density="compact">
          <v-list-item 
            title="Remain Status Quo" 
            subtitle="Use last known value" 
            @click="setOption('default')"
          />
          <v-list-item 
            title="Change to..." 
            subtitle="Set a constant value" 
            @click="setOption('constant')"
          />
          <v-list-item 
            title="Follow a Custom Plan" 
            subtitle="Upload series of values" 
            @click="setOption('custom')"
          />
          <v-divider />
          <v-list-item 
            title="Be Ignored" 
            subtitle="Remove from model" 
            color="error"
            @click="setOption('ignore')"
          />
        </v-list>
      </v-menu>

      <!-- Constant Input -->
      <div v-if="option === 'constant'" style="width: 100px; display: inline-block;">
        <v-text-field
          v-model.number="constantValue"
          class="centered-input text-h6 font-weight-bold text-primary"
          density="compact"
          hide-details
          single-line
          type="number"
          variant="underlined"
          @update:model-value="emitChange"
        />
      </div>

    </div>

    <!-- Custom Plan Input (Expandable) -->
    <v-expand-transition>
      <div v-if="option === 'custom'" class="mt-4">
        <v-textarea
          v-model="customPlanRaw"
          label="Paste series of values (comma separated)"
          hint="e.g. 10, 12, 15, 14, 10..."
          persistent-hint
          rows="2"
          variant="filled"
          @update:model-value="parseCustomPlan"
        />
        <div class="text-caption text-medium-emphasis mt-1">
          Parsed: {{ customPlanParsed.length }} values
        </div>
      </div>
    </v-expand-transition>

  </v-card>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'

export interface CovariateState {
  override: number | number[] | null
  isIgnored: boolean
}

const props = defineProps<{
  column: string
  modelValue: CovariateState
}>()

const emit = defineEmits(['update:modelValue'])

const option = ref<'default' | 'constant' | 'custom' | 'ignore'>('default')
const constantValue = ref<number>(0)
const customPlanRaw = ref('')
const customPlanParsed = ref<number[]>([])

const localState = computed(() => props.modelValue)

// Init from props
onMounted(() => {
  if (props.modelValue.isIgnored) {
    option.value = 'ignore'
  } else if (Array.isArray(props.modelValue.override)) {
    option.value = 'custom'
    customPlanParsed.value = props.modelValue.override
    customPlanRaw.value = props.modelValue.override.join(', ')
  } else if (props.modelValue.override !== null) {
    option.value = 'constant'
    constantValue.value = Number(props.modelValue.override)
  } else {
    option.value = 'default'
  }
})

const getOptionLabel = computed(() => {
  switch (option.value) {
    case 'default': return 'Remain Status Quo'
    case 'constant': return 'Change to...'
    case 'custom': return 'Follow a Custom Plan'
    case 'ignore': return 'Be Ignored'
  }
})

const getChipColor = computed(() => {
  if (option.value === 'ignore') return 'error'
  if (option.value === 'default') return 'grey'
  return 'secondary'
})

function setOption(opt: 'default' | 'constant' | 'custom' | 'ignore') {
  option.value = opt
  emitChange()
}

function parseCustomPlan() {
  const parts = customPlanRaw.value.split(',').map(s => s.trim()).filter(s => s !== '')
  const nums = parts.map(Number).filter(n => !isNaN(n))
  customPlanParsed.value = nums
  emitChange()
}

function emitChange() {
  let newState: CovariateState = { override: null, isIgnored: false }
  
  if (option.value === 'ignore') {
    newState.isIgnored = true
  } else if (option.value === 'constant') {
    newState.override = constantValue.value
  } else if (option.value === 'custom') {
    newState.override = customPlanParsed.value
  } else {
    // default
    newState.override = null
  }
  
  emit('update:modelValue', newState)
}
</script>

<style scoped>
.centered-input :deep(input) {
  text-align: center;
}
.on-ignore {
  opacity: 0.6;
  text-decoration: line-through;
}
</style>
