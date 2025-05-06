<template>
  <v-container>
    <v-card class="mb-6">
      <v-card-title class="text-h4">
        {{ $t('apiDocs.title') }}
      </v-card-title>
      <v-card-text>
        <p>{{ $t('apiDocs.description') }}</p>
      </v-card-text>
    </v-card>

    <v-tabs v-model="activeTab" bg-color="primary" align-tabs="center">
      <v-tab value="backend">{{ $t('apiDocs.backend') }}</v-tab>
      <v-tab value="python">{{ $t('apiDocs.python') }}</v-tab>
    </v-tabs>

    <v-window v-model="activeTab" class="mt-4">
      <v-window-item value="backend">
        <v-card>
          <v-card-title class="d-flex">
            <div>
              <v-icon color="primary" class="mr-2">mdi-api</v-icon>
              {{ $t('apiDocs.backendTitle') }}
            </div>
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                variant="outlined"
                :href="backendSwaggerUrl"
                target="_blank"
                prepend-icon="mdi-open-in-new"
            >
              {{ $t('apiDocs.openInNewTab') }}
            </v-btn>
          </v-card-title>
          <v-card-text class="pa-4">
            <v-alert type="info" class="mb-4" icon="mdi-information">
              {{ $t('apiDocs.iframeError') }}
              <div class="mt-3">
                <v-btn
                    color="primary"
                    :href="backendSwaggerUrl"
                    target="_blank"
                    prepend-icon="mdi-open-in-new"
                    size="large"
                    class="mr-2"
                >
                  {{ $t('apiDocs.openDirectly') }}
                </v-btn>
              </div>
            </v-alert>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="python">
        <v-card>
          <v-card-title class="d-flex">
            <div>
              <v-icon color="primary" class="mr-2">mdi-language-python</v-icon>
              {{ $t('apiDocs.pythonTitle') }}
            </div>
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                variant="outlined"
                :href="pythonSwaggerUrl"
                target="_blank"
                prepend-icon="mdi-open-in-new"
            >
              {{ $t('apiDocs.openInNewTab') }}
            </v-btn>
          </v-card-title>
          <v-card-text class="pa-4">
            <v-alert type="info" class="mb-4" icon="mdi-information">
              {{ $t('apiDocs.iframeError') }}
              <div class="mt-3">
                <v-btn
                    color="primary"
                    :href="pythonSwaggerUrl"
                    target="_blank"
                    prepend-icon="mdi-open-in-new"
                    size="large"
                    class="mr-2"
                >
                  {{ $t('apiDocs.openDirectly') }}
                </v-btn>
              </div>
            </v-alert>
          </v-card-text>
        </v-card>
      </v-window-item>
    </v-window>
  </v-container>
</template>

<script setup>
import { ref, onMounted, watchEffect } from 'vue';

const activeTab = ref('backend');
const iframeError = ref(false);





onMounted(() => {
  // Vzhledem k CSP omezením automaticky zobrazíme jen výzvu k otevření v novém okně
  iframeError.value = true;
});
// Swagger URLs - upravte podľa vašej konfigurácie
const baseUrl = window.location.origin;
const backendSwaggerUrl = import.meta.env.VITE_API_URL.replace('/api', '/api-docs');
const pythonSwaggerUrl = import.meta.env.VITE_PYTHON_API_URL + '/api-docs';


</script>

<style scoped>
.swagger-iframe {
  width: 100%;
  height: 800px;
  overflow: auto;
  border: 0;
}
</style>