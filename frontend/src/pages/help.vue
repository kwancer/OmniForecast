<template>
  <v-container class="bg-background fill-height d-flex flex-column justify-center py-12" fluid>
    <v-row class="flex-grow-0 w-100" justify="center">
      <v-col cols="12" lg="6" md="8" sm="10">
        <div class="text-center mb-10">
          <h2 class="text-h3 font-weight-bold mb-2">Help & Support</h2>
          <p class="text-body-1 text-medium-emphasis">
            Need assistance with AskForecast? Here to help.
          </p>
        </div>

        <v-card class="pa-8 border text-center" variant="flat">
          <v-icon class="mb-4" color="primary" size="48">mdi-help-circle-outline</v-icon>

          <h3 class="text-h5 mb-4">Contact for Support</h3>

          <v-divider class="mb-6" />

          <div class="d-flex flex-column align-center">
            <span class="text-subtitle-1 font-weight-bold">Krzysztof Wancerski</span>
            <v-btn
              class="text-none text-body-1 mt-2"
              color="primary"
              href="mailto:kw1022@ic.ac.uk"
              prepend-icon="mdi-email-outline"
              variant="text"
            >
              kw1022@ic.ac.uk
            </v-btn>
          </div>
        </v-card>

      </v-col>
    </v-row>
  </v-container>
</template>
