<template>
  <v-container fluid class="bg-background py-12 d-flex flex-column align-center">
    <v-row justify="center" class="w-100">
      <v-col cols="12" sm="10" md="8" lg="7">
        <div class="text-center mb-10">
          <h2 class="text-h3 font-weight-bold mb-4">Privacy & Data Policy</h2>
          <p class="text-body-1 text-medium-emphasis">
            How we handle your data to provide forecasting services.
          </p>
        </div>

        <v-card variant="flat" class="pa-8 border">
          <section class="mb-8">
            <h3 class="text-h5 mb-4">1. Data Retention & Purpose</h3>
            <p class="text-body-2 mb-4">
              We distinguish between the <strong>transient processing</strong> of raw data and the <strong>permanent storage</strong> of analytical outputs:
            </p>
            
            <v-table class="border rounded-lg mb-4">
              <thead>
                <tr>
                  <th class="text-left">Data Type</th>
                  <th class="text-left">Retention Status</th>
                  <th class="text-left">Purpose</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Raw Uploaded Data</strong></td>
                  <td>Transient</td>
                  <td>Used strictly for immediate computation and purged thereafter.</td>
                </tr>
                <tr>
                  <td><strong>Forecasted Results</strong></td>
                  <td>Stored</td>
                  <td>To allow you to refetch sessions and view historical forecasts.</td>
                </tr>
                <tr>
                  <td><strong>Problem Descriptions</strong></td>
                  <td>Stored</td>
                  <td>To maintain context for your saved sessions.</td>
                </tr>
                <tr>
                  <td><strong>Summary Statistics</strong></td>
                  <td>Stored</td>
                  <td>To provide analytical continuity and dashboarding.</td>
                </tr>
              </tbody>
            </v-table>

            <p class="text-body-2 italic">
              <strong>Note on Session Persistence:</strong> We store your generated forecasts and problem metadata specifically so that you may revisit, refetch, and manage your previous sessions without needing to re-upload raw datasets.
            </p>
          </section>

          <section class="mb-8">
            <h3 class="text-h5 mb-3">2. Third-Party AI Sub-Processors</h3>
            <p class="text-body-2">
              In accordance with the <strong>UK GDPR</strong> principle of transparency, we disclose that your <strong>problem description</strong> and <strong>summary statistics</strong> are shared with an external AI inference provider. This is necessary for the sophisticated analysis required to generate your forecast. 
            </p>
            <p class="text-body-2 mt-2">
              The actual forecast is generated on our secure local infrastructure using the insights provided by the external model.
            </p>
          </section>

          <section class="mb-8">
            <h3 class="text-h5 mb-3">3. Data Subject Rights</h3>
            <p class="text-body-2">
              Under the <strong>Data Protection Act 2018</strong>, you have the right to access, rectify, or request the erasure of the stored forecasted data and problem descriptions associated with your account.
            </p>
          </section>

          <v-divider class="mb-6"></v-divider>

          <p class="text-caption text-center text-medium-emphasis">
            By using this service, you acknowledge that you have read and agree to these terms.
          </p>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>