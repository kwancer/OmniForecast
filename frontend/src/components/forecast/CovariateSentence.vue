<template>
  <v-card
    class="pa-4 mb-2 bg-surface covariate-card"
    :class="{
      'on-ignore': localState.isIgnored,
      'is-controllable': type === 'controllable',
      'is-exogenous': type === 'exogenous'
    }"
    variant="outlined"
  >
    <div class="d-flex align-center flex-wrap" style="gap: 8px; line-height: 2.0;">
      <v-tooltip v-if="type === 'exogenous'" location="top">
        <template #activator="{ props: tProps }">
          <v-icon
            v-bind="tProps"
            class="mr-1"
            color="info"
            icon="mdi-alert-circle-outline"
            size="small"
          />
        </template>
        <span>⚠️ This is an external factor. The AI is making an assumption based on past history.</span>
      </v-tooltip>

      <span class="text-medium-emphasis">{{ prefixText }}</span>

      <b class="text-primary font-weight-bold">{{ column }}</b>

      <span class="text-medium-emphasis"> {{ joinText }} </span>

      <v-menu>
        <template #activator="{ props }">
          <v-chip
            v-bind="props"
            class="font-weight-bold"
            :color="getChipColor"
            size="large"
            variant="tonal"
          >
            {{ getOptionLabel }} <v-icon end icon="mdi-chevron-down" />
          </v-chip>
        </template>
        <v-list density="compact">
          <v-list-item
            v-for="opt in availableOptions"
            :key="opt.value"
            :subtitle="opt.subtitle"
            :title="opt.title"
            @click="setOption(opt.value)"
          />
          <v-divider />
          <v-list-item
            color="error"
            subtitle="Remove from model"
            title="Be Ignored"
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
          hint="e.g. 10, 12, 15, 14, 10..."
          :label="customPlanLabel"
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
  import { computed, onMounted, ref } from 'vue'

  export interface CovariateState {
    override: number | number[] | null
    isIgnored: boolean
  }

  const covariateProps = defineProps<{
    column: string
    modelValue: CovariateState
    type: 'controllable' | 'exogenous' | 'static'
  }>()

  const emit = defineEmits(['update:modelValue'])

  const option = ref<'default' | 'constant' | 'custom' | 'ignore'>('default')
  const constantValue = ref<number>(0)
  const customPlanRaw = ref('')
  const customPlanParsed = ref<number[]>([])

  const localState = computed(() => covariateProps.modelValue)

  const prefixText = computed(() => {
    return covariateProps.type === 'controllable' ? 'I plan to set' : 'Assume'
  })

  const joinText = computed(() => {
    return covariateProps.type === 'controllable' ? 'to' : 'will be'
  })

  const customPlanLabel = computed(() => {
    return covariateProps.type === 'controllable' ? 'Paste series of values (comma separated)' : 'Upload series of values (Custom Scenario)'
  })

  const availableOptions = computed(() => {
    if (covariateProps.type === 'controllable') {
      return [
        { value: 'default', title: 'Keep Current (Status Quo)', subtitle: 'Assume no change from today' },
        { value: 'constant', title: 'Change to...', subtitle: 'Set a specific constant value' },
        { value: 'custom', title: 'Follow Custom Plan', subtitle: 'Provide a series of future values' },
      ] as const
    } else {
      return [
        { value: 'default', title: 'Same as Last Year (Seasonal)', subtitle: 'AI assumption based on history' },
        { value: 'constant', title: 'Status Quo (Last Value)', subtitle: 'Assume last known value level' },
        { value: 'custom', title: 'Custom Scenario (Upload)', subtitle: 'Provide your own growth/trend scenario' },
      ] as const
    }
  })

  // Init from props
  onMounted(() => {
    if (covariateProps.modelValue.isIgnored) {
      option.value = 'ignore'
    } else if (Array.isArray(covariateProps.modelValue.override)) {
      option.value = 'custom'
      customPlanParsed.value = covariateProps.modelValue.override
      customPlanRaw.value = covariateProps.modelValue.override.join(', ')
    } else if (covariateProps.modelValue.override === null) {
      option.value = 'default'
    } else {
      option.value = 'constant'
      constantValue.value = Number(covariateProps.modelValue.override)
    }
  })

  const getOptionLabel = computed(() => {
    const opt = availableOptions.value.find(o => o.value === option.value)
    return opt ? opt.title : (option.value === 'ignore' ? 'Be Ignored' : '')
  })

  const getChipColor = computed(() => {
    if (option.value === 'ignore') return 'error'
    if (option.value === 'default') return 'grey'
    return 'secondary'
  })

  function setOption (opt: 'default' | 'constant' | 'custom' | 'ignore') {
    option.value = opt
    emitChange()
  }

  function parseCustomPlan () {
    const parts = customPlanRaw.value.split(',').map(s => s.trim()).filter(s => s !== '')
    const nums = parts.map(Number).filter(n => !Number.isNaN(n))
    customPlanParsed.value = nums
    emitChange()
  }

  function emitChange () {
    const newState: CovariateState = { override: null, isIgnored: false }

    switch (option.value) {
      case 'ignore': {
        newState.isIgnored = true

        break
      }
      case 'constant': {
        newState.override = constantValue.value

        break
      }
      case 'custom': {
        newState.override = customPlanParsed.value

        break
      }
      default: {
        // default
        newState.override = null
      }
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
.covariate-card {
  transition: all 0.3s ease;
}
.is-controllable {
  border: 1px solid rgba(76, 175, 80, 0.4) !important;
}
.is-controllable:hover {
  border-color: #4CAF50 !important;
  background-color: rgba(76, 175, 80, 0.05) !important;
}
.is-exogenous {
  border: 1px solid rgba(33, 150, 243, 0.4) !important;
}
.is-exogenous:hover {
  border-color: #2196F3 !important;
  background-color: rgba(33, 150, 243, 0.05) !important;
}
</style>

