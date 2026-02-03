<template>
  <v-card class="pa-4 mb-2 bg-surface" :class="{ 'on-ignore': localState.isIgnored }" variant="outlined">
    <div class="d-flex align-center flex-wrap" style="gap: 8px; line-height: 2.0;">
      <span class="text-medium-emphasis">In the future, I expect </span>

      <b class="text-primary font-weight-bold">{{ column }}</b>

      <span class="text-medium-emphasis"> to </span>

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
            subtitle="Use last known value"
            title="Remain Status Quo"
            @click="setOption('default')"
          />
          <v-list-item
            subtitle="Set a constant value"
            title="Change to..."
            @click="setOption('constant')"
          />
          <v-list-item
            subtitle="Upload series of values"
            title="Follow a Custom Plan"
            @click="setOption('custom')"
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
          label="Paste series of values (comma separated)"
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
  }>()

  const emit = defineEmits(['update:modelValue'])

  const option = ref<'default' | 'constant' | 'custom' | 'ignore'>('default')
  const constantValue = ref<number>(0)
  const customPlanRaw = ref('')
  const customPlanParsed = ref<number[]>([])

  const localState = computed(() => covariateProps.modelValue)

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
    switch (option.value) {
      case 'default': { return 'Remain Status Quo'
      }
      case 'constant': { return 'Change to...'
      }
      case 'custom': { return 'Follow a Custom Plan'
      }
      case 'ignore': { return 'Be Ignored'
      }
      default: { return ''
      }
    }
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
</style>
