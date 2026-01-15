<template>
  <v-container fluid class="bg-background fill-height d-flex flex-column justify-center py-12">
    <v-row justify="center" class="flex-grow-0 w-100">
      <v-col cols="12" sm="10" md="8" lg="6">
        <div class="text-center mb-10">
          <h2 class="text-h3 font-weight-bold mb-2">Help & Support</h2>
          <p class="text-body-1 text-medium-emphasis">
            Need assistance with OmniForecast? Here to help.
          </p>
        </div>

        <v-card variant="flat" class="pa-8 border text-center">
          <v-icon size="48" color="primary" class="mb-4">mdi-help-circle-outline</v-icon>
          
          <h3 class="text-h5 mb-4">Contact for Support</h3>
          
          <v-divider class="mb-6"></v-divider>

          <div class="d-flex flex-column align-center">
            <span class="text-subtitle-1 font-weight-bold">Krzysztof Wancerski</span>
            <v-btn
              variant="text"
              color="primary"
              prepend-icon="mdi-email-outline"
              class="text-none text-body-1 mt-2"
              href="mailto:kw1022@ic.ac.uk"
            >
              kw1022@ic.ac.uk
            </v-btn>
          </div>
        </v-card>

      </v-col>
    </v-row>
  </v-container>
</template>