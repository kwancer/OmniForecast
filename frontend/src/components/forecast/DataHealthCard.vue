<template>
  <!-- HERO MODE: Full-width banner for the top of the results page -->
  <div
    v-if="mode === 'hero' && dataHealthReport"
    class="hero-score-banner"
    :class="borderColorClass"
  >
    <div class="hero-score-content">
      <div class="hero-score-text">
        <div class="text-overline text-medium-emphasis mb-1 hero-overline">
          Forecast Skill Score
        </div>
        <div class="hero-headline">
          Your forecast is
          <span class="hero-score-number" :class="textColorClass">
            {{ dataHealthReport.score }}%
          </span>
          better than a guess
          <v-tooltip location="bottom" max-width="360">
            <template #activator="{ props: tooltip }">
              <v-icon
                class="ml-2 mb-1"
                color="medium-emphasis"
                size="22"
                v-bind="tooltip"
              >
                mdi-information-outline
              </v-icon>
            </template>
            <div class="text-body-2">
              <strong>How is this calculated?</strong>
              <p class="mt-1">
                The score compares the winning model's accuracy against a simple baseline:
                extending the last observed value forward as a flat line (naïve forecast).
              </p>
              <p class="mt-1">
                A score of <strong>74</strong> means the model reduced prediction error by 74%
                compared with simply repeating the most recent number.
                A score of 100 would mean a perfect forecast; 0 means the model did no better than the baseline.
              </p>
            </div>
          </v-tooltip>
        </div>
        <div class="hero-subheadline mt-2">
          <v-chip
            class="mr-2"
            :color="chipColor"
            size="small"
            variant="flat"
          >
            {{ dataHealthReport.rating }}
          </v-chip>
          <span class="text-body-1 text-medium-emphasis">
            {{ heroReassurance }}
          </span>
        </div>
      </div>

      <!-- Large decorative gauge -->
      <div class="hero-gauge">
        <svg height="120" viewBox="0 0 120 120" width="120">
          <circle
            cx="60"
            cy="60"
            fill="none"
            r="50"
            stroke="rgba(var(--v-theme-on-surface), 0.08)"
            stroke-width="10"
          />
          <circle
            cx="60"
            cy="60"
            fill="none"
            r="50"
            :stroke="gaugeColor"
            stroke-linecap="round"
            stroke-width="10"
            transform="rotate(-90 60 60)"
            :style="{
              strokeDasharray: heroCircumference,
              strokeDashoffset: animatedHeroOffset,
              transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1)'
            }"
          />
          <text
            class="hero-gauge-text"
            :fill="gaugeColor"
            text-anchor="middle"
            x="60"
            y="67"
          >
            {{ dataHealthReport.score }}
          </text>
        </svg>
      </div>
    </div>
  </div>

  <!-- COMPACT MODE: Small header card for sidebar or tight spaces -->
  <v-card
    v-else-if="mode === 'compact' && dataHealthReport"
    class="pa-3"
    :class="borderColorClass"
    variant="outlined"
  >
    <div class="d-flex align-center justify-space-between">
      <div>
        <div class="text-caption text-medium-emphasis">
          Forecast Score
        </div>
        <div class="d-flex align-center mt-1">
          <span class="text-h4 font-weight-bold" :class="textColorClass">
            {{ dataHealthReport.score }}
          </span>
          <span class="text-body-2 text-medium-emphasis ml-1">/100</span>
          <v-chip
            class="ml-2"
            :color="chipColor"
            size="x-small"
            variant="flat"
          >
            {{ dataHealthReport.rating }}
          </v-chip>
        </div>
      </div>
      <svg height="48" viewBox="0 0 48 48" width="48">
        <circle
          cx="24"
          cy="24"
          fill="none"
          r="19"
          stroke="rgba(var(--v-theme-on-surface), 0.08)"
          stroke-width="6"
        />
        <circle
          cx="24"
          cy="24"
          fill="none"
          r="19"
          :stroke="gaugeColor"
          stroke-linecap="round"
          stroke-width="6"
          transform="rotate(-90 24 24)"
          :style="{
            strokeDasharray: circumferenceCompact,
            strokeDashoffset: animatedCompactOffset,
            transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1)'
          }"
        />
      </svg>
    </div>
  </v-card>

  <!-- LEGACY MODE: Original card with details toggle (retained for backwards compatibility) -->
  <v-card
    v-else-if="dataHealthReport"
    class="mb-4 pa-4"
    :class="borderColorClass"
    variant="outlined"
  >
    <div class="d-flex align-center justify-space-between mb-3">
      <div class="flex-grow-1">
        <div class="text-overline text-medium-emphasis mb-1">
          Forecast Skill Score
        </div>
        <div class="d-flex align-center">
          <span class="text-h3 font-weight-bold" :class="textColorClass">
            {{ dataHealthReport?.score ?? 'N/A' }}
          </span>
          <span class="text-h6 text-medium-emphasis ml-1">/100</span>
          <v-chip
            class="ml-3"
            :color="chipColor"
            size="small"
            variant="flat"
          >
            {{ dataHealthReport.rating }}
          </v-chip>
        </div>
      </div>

      <!-- Circular Gauge & Toggle -->
      <div class="d-flex flex-column align-center">
        <svg height="80" viewBox="0 0 80 80" width="80">
          <circle
            cx="40"
            cy="40"
            fill="none"
            r="32"
            stroke="#e0e0e0"
            stroke-width="8"
          />
          <circle
            cx="40"
            cy="40"
            fill="none"
            r="32"
            :stroke="gaugeColor"
            stroke-linecap="round"
            stroke-width="8"
            transform="rotate(-90 40 40)"
            :style="{
              strokeDasharray: circumference,
              strokeDashoffset: animatedLegacyOffset,
              transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1)'
            }"
          />
          <text
            class="gauge-text"
            :fill="gaugeColor"
            text-anchor="middle"
            x="40"
            y="45"
          >
            {{ dataHealthReport.score }}
          </text>
        </svg>

        <v-btn
          size="x-small"
          variant="text"
          @click="showDetails = !showDetails"
        >
          {{ showDetails ? 'Hide' : 'Details' }}
          <v-icon
            end
            :icon="showDetails ? 'mdi-chevron-up' : 'mdi-chevron-down'"
            size="small"
          />
        </v-btn>
      </div>
    </div>

    <!-- Collapsible Details Section -->
    <v-expand-transition>
      <div v-show="showDetails">
        <v-divider class="mb-3" />

        <p class="text-body-2 text-medium-emphasis mb-0">
          {{ dataHealthReport.explanation }}
        </p>

        <!-- Low Score Warning -->
        <v-alert
          v-if="dataHealthReport.score <= 30"
          class="mt-3"
          color="warning"
          density="compact"
          icon="mdi-alert-circle"
          variant="tonal"
        >
          <div class="text-body-2">
            <strong>Why is the forecast flat?</strong>
            <br>
            A low score means your data does not have a clear, repeatable pattern that the models can latch onto. This often happens with very volatile or sparse data. The forecast falls back to a simple average, which is the safest guess when patterns are unclear.
          </div>
        </v-alert>

        <!-- Dual Metrics Display -->
        <div class="mt-3">
          <div
            v-if="dataHealthReport.mse_naive !== undefined && dataHealthReport.mse_winner !== undefined"
            class="mt-3"
          >
            <div class="d-flex align-center gap-1 mb-2">
              <span class="text-caption text-medium-emphasis">How the score is calculated</span>
              <v-tooltip location="top" max-width="320">
                <template #activator="{ props: tip }">
                  <v-icon v-bind="tip" class="text-medium-emphasis" size="14">mdi-information-outline</v-icon>
                </template>
                <span>
                  The score compares the winning model's accuracy against a simple "flat line" baseline.
                  A score of 100 means the model predicts perfectly; 0 means it did no better than the baseline.
                </span>
              </v-tooltip>
            </div>
            <div class="d-flex gap-3">
              <v-card class="flex-1 pa-3" color="surface" variant="outlined">
                <div class="text-caption text-medium-emphasis">Simple Baseline Error</div>
                <div class="text-h6 font-weight-bold font-mono text-error">
                  {{ formatMse(dataHealthReport.mse_naive) }}
                </div>
                <div class="text-caption text-medium-emphasis mt-1">Guessing the average every time</div>
              </v-card>
              <v-card class="flex-1 pa-3" color="surface" variant="outlined">
                <div class="text-caption text-medium-emphasis">Winner Model Error</div>
                <div class="text-h6 font-weight-bold font-mono text-success">
                  {{ formatMse(dataHealthReport.mse_winner) }}
                </div>
                <div class="text-caption text-medium-emphasis mt-1">{{ dataHealthReport.winner_name }}</div>
              </v-card>
            </div>
            <v-progress-linear
              class="mt-3"
              color="primary"
              height="6"
              :model-value="dataHealthReport.score"
              rounded
            />
            <div class="text-caption text-medium-emphasis mt-1">
              The winner reduced the prediction error by
              <strong>{{ formatNumber(dataHealthReport.score, { suffix: '%' }) }}</strong>
              compared with simply guessing the historical average.
            </div>
          </div>
        </div>
      </div>
    </v-expand-transition>
  </v-card>
</template>

<script setup lang="ts">
  import type { DataHealthReport } from '@/types'
  import { computed, nextTick, onMounted, ref } from 'vue'
  import { formatNumber } from '@/utils/formatters'

  const props = defineProps<{
    dataHealthReport: DataHealthReport | null
    mode?: 'hero' | 'compact' | 'legacy'
  }>()

  const showDetails = ref(false)

  function formatMse (val: number | undefined | null) {
    return formatNumber(val)
  }

  const borderColorClass = computed(() => {
    if (!props.dataHealthReport) return ''
    const score = props.dataHealthReport.score
    if (score >= 70) return 'border-s-4 border-success'
    if (score <= 30) return 'border-s-4 border-error'
    return 'border-s-4 border-warning'
  })

  const textColorClass = computed(() => {
    if (!props.dataHealthReport) return ''
    const score = props.dataHealthReport.score
    if (score >= 70) return 'text-success'
    if (score <= 30) return 'text-error'
    return 'text-warning'
  })

  const chipColor = computed(() => {
    if (!props.dataHealthReport) return 'grey'
    const score = props.dataHealthReport.score
    if (score >= 70) return 'success'
    if (score <= 30) return 'error'
    return 'warning'
  })

  const gaugeColor = computed(() => {
    if (!props.dataHealthReport) return '#9E9E9E'
    const score = props.dataHealthReport.score
    if (score >= 70) return '#4CAF50'
    if (score <= 30) return '#F44336'
    return '#FF9800'
  })

  const heroReassurance = computed(() => {
    if (!props.dataHealthReport) return ''
    const score = props.dataHealthReport.score
    if (score >= 70) {
      return 'The model found clear patterns in your data and is confident in its predictions.'
    }
    if (score <= 30) {
      return 'Your data does not show a strong repeatable pattern. The forecast is conservative.'
    }
    return 'The model found some patterns, but there is still noticeable uncertainty.'
  })

  // Hero gauge calculations (r=50)
  const heroRadius = 50
  const heroCircumference = 2 * Math.PI * heroRadius

  const heroProgressOffset = computed(() => {
    if (!props.dataHealthReport) return heroCircumference
    const progress = props.dataHealthReport.score / 100
    return heroCircumference * (1 - progress)
  })

  // Legacy gauge calculations (r=32)
  const radius = 32
  const circumference = 2 * Math.PI * radius

  const progressOffset = computed(() => {
    if (!props.dataHealthReport) return circumference
    const progress = props.dataHealthReport.score / 100
    return circumference * (1 - progress)
  })

  // Compact gauge calculations (r=19)
  const radiusCompact = 19
  const circumferenceCompact = 2 * Math.PI * radiusCompact

  const progressOffsetCompact = computed(() => {
    if (!props.dataHealthReport) return circumferenceCompact
    const progress = props.dataHealthReport.score / 100
    return circumferenceCompact * (1 - progress)
  })

  // Animated gauge offsets (start empty, animate to target)
  const animatedHeroOffset = ref(heroCircumference)
  const animatedLegacyOffset = ref(circumference)
  const animatedCompactOffset = ref(circumferenceCompact)

  onMounted(async () => {
    await nextTick()
    if (props.dataHealthReport) {
      animatedHeroOffset.value = heroProgressOffset.value
      animatedLegacyOffset.value = progressOffset.value
      animatedCompactOffset.value = progressOffsetCompact.value
    }
  })
</script>

<style scoped>
  .font-mono {
    font-family: 'JetBrains Mono', 'Roboto Mono', monospace;
  }

  /* ─── Hero Banner ─── */
  .hero-score-banner {
    width: 100%;
    padding: 28px 36px;
    border-radius: 16px;
    background:
      radial-gradient(circle at 0% 0%, rgba(var(--v-theme-success), 0.06), transparent 50%),
      radial-gradient(circle at 100% 100%, rgba(var(--v-theme-primary), 0.04), transparent 50%),
      rgb(var(--v-theme-surface));
    border: 1px solid rgba(var(--v-theme-primary), 0.08);
    transition: border-color 0.3s ease;
  }

  .hero-score-banner:hover {
    border-color: rgba(var(--v-theme-primary), 0.15);
  }

  .hero-score-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
  }

  .hero-score-text {
    flex: 1;
    min-width: 0;
  }

  .hero-overline {
    font-size: 0.75rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
  }

  .hero-headline {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.2;
    color: rgb(var(--v-theme-on-surface));
  }

  .hero-score-number {
    font-size: 2.4rem;
    font-weight: 800;
    line-height: 1;
  }

  .hero-subheadline {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .hero-gauge {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .hero-gauge-text {
    font-size: 28px;
    font-weight: 800;
    font-family: 'Roboto', sans-serif;
  }

  @media (max-width: 768px) {
    .hero-headline {
      font-size: 1.4rem;
    }
    .hero-score-number {
      font-size: 1.6rem;
    }
    .hero-score-banner {
      padding: 20px 24px;
    }
    .hero-gauge {
      display: none;
    }
  }

  /* ─── Legacy Gauge ─── */
  .gauge-text {
    font-size: 18px;
    font-weight: bold;
    font-family: 'Roboto', sans-serif;
  }

  .gap-3 {
    gap: 12px;
  }

  .flex-1 {
    flex: 1;
  }

  .border-s-4 {
    border-left-width: 4px !important;
    border-left-style: solid !important;
  }

  .border-success {
    border-left-color: rgb(var(--v-theme-success)) !important;
  }

  .border-error {
    border-left-color: rgb(var(--v-theme-error)) !important;
  }

  .border-warning {
    border-left-color: rgb(var(--v-theme-warning)) !important;
  }
</style>
