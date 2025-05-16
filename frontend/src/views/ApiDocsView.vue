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

          <v-card-text class="pa-0">
            <div id="backend-swagger-ui" class="swagger-container"></div>
            <div v-if="!swaggerLoaded.backend" class="text-center pa-6">
              <v-progress-circular indeterminate color="primary" class="mb-4"></v-progress-circular>
              <p>{{ $t('apiDocs.iframeError') }}</p>
              <v-btn
                  color="primary"
                  :href="backendSwaggerUrl"
                  target="_blank"
                  prepend-icon="mdi-open-in-new"
                  size="large"
                  class="mt-3"
              >
                {{ $t('apiDocs.openDirectly') }}
              </v-btn>
            </div>
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

          <v-card-text class="pa-0">
            <div id="python-swagger-ui" class="swagger-container"></div>
            <div v-if="!swaggerLoaded.python" class="text-center pa-6">
              <v-progress-circular indeterminate color="primary" class="mb-4"></v-progress-circular>
              <p>{{ $t('apiDocs.iframeError') }}</p>
              <v-btn
                  color="primary"
                  :href="pythonSwaggerUrl"
                  target="_blank"
                  prepend-icon="mdi-open-in-new"
                  size="large"
                  class="mt-3"
              >
                {{ $t('apiDocs.openDirectly') }}
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-window-item>
    </v-window>
  </v-container>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useAuthStore } from '@/stores/auth';

const activeTab = ref('backend');
const swaggerLoaded = ref({
  backend: false,
  python: false
});

const authStore = useAuthStore();

// Base URLs
const baseUrl = window.location.origin;
const backendDocsUrl = `${import.meta.env.VITE_API_URL}/api-docs-spec`;
const pythonDocsUrl = `${import.meta.env.VITE_PYTHON_API_URL}/api-docs-spec`;

// URLs for external opening in new tab
const backendSwaggerUrl = `${import.meta.env.VITE_API_URL.replace('/api', '/api-docs')}`;
const pythonSwaggerUrl = `${import.meta.env.VITE_PYTHON_API_URL}/api-docs`;

// Dynamically load the Swagger UI script
const loadSwaggerUI = () => {
  return new Promise((resolve) => {
    // Check if Swagger UI is already loaded
    if (window.SwaggerUIBundle) {
      resolve();
      return;
    }

    // Load CSS first
    const cssLink = document.createElement('link');
    cssLink.rel = 'stylesheet';
    cssLink.type = 'text/css';
    cssLink.href = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css';
    document.head.appendChild(cssLink);

    // Then load the JS
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js';
    script.onload = () => resolve();
    document.head.appendChild(script);
  });
};

// Initialize Swagger UI with auth
const initSwaggerUI = async (tab) => {
  await loadSwaggerUI();

  if (!window.SwaggerUIBundle) {
    console.error("SwaggerUIBundle not loaded properly");
    return;
  }

  try {
    const elementId = `${tab}-swagger-ui`;
    const element = document.getElementById(elementId);

    if (!element) {
      console.error(`Element ${elementId} not found`);
      return;
    }

    // Clear the element first
    element.innerHTML = '';

    // The URL to fetch the Swagger spec from
    const specUrl = tab === 'backend' ? backendDocsUrl : pythonDocsUrl;

    // Create requestInterceptor to add API key to all requests
    const requestInterceptor = (req) => {
      // Add API key if available
      if (authStore.user?.apiKey) {
        req.headers["X-API-Key"] = authStore.user.apiKey;
      }

      // Add token if available
      if (authStore.token) {
        req.headers["Authorization"] = `Bearer ${authStore.token}`;
      }

      return req;
    };

    // Initialize SwaggerUI
    window.SwaggerUIBundle({
      dom_id: `#${elementId}`,
      url: specUrl,
      deepLinking: true,
      presets: [
        window.SwaggerUIBundle.presets.apis,
        window.SwaggerUIBundle.SwaggerUIStandalonePreset
      ],
      layout: "BaseLayout",
      supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
      onComplete: () => {
        console.log(`Swagger UI for ${tab} loaded successfully`);
        swaggerLoaded.value[tab] = true;
      },
      onFailure: (error) => {
        console.error(`Failed to load Swagger UI for ${tab}:`, error);
        swaggerLoaded.value[tab] = false;
      },
      requestInterceptor: requestInterceptor,
      persistAuthorization: true
    });
  } catch (error) {
    console.error(`Error initializing Swagger UI for ${tab}:`, error);
    swaggerLoaded.value[tab] = false;
  }
};

// Initialize on mount
onMounted(() => {
  // Initialize Swagger UI for the initial tab
  initSwaggerUI(activeTab.value);

  // Add event listener for tab visibility changes
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && activeTab.value && !swaggerLoaded.value[activeTab.value]) {
      initSwaggerUI(activeTab.value);
    }
  });
});

// Watch for tab changes
watch(activeTab, (newTab) => {
  if (!swaggerLoaded.value[newTab]) {
    initSwaggerUI(newTab);
  }
});
</script>

<style>
.swagger-container {
  height: 800px;
  overflow: auto;
  border: 0;
}

/* Override some Swagger UI styles for better integration */
.swagger-ui .topbar {
  display: none;
}

.swagger-ui .information-container {
  padding: 20px;
  margin: 0;
}

.swagger-ui .scheme-container {
  padding: 10px 0;
  background-color: transparent;
  box-shadow: none;
}
</style>