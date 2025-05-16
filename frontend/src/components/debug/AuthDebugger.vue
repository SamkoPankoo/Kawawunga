// src/components/debug/AuthDebugger.vue
<template>
  <v-card v-if="showDebugger" class="my-4 auth-debugger">
    <v-card-title class="d-flex">
      <span>Authentication Debug</span>
      <v-spacer></v-spacer>
      <v-btn icon @click="showDebugger = false">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-card-title>

    <v-card-text>
      <v-alert
          :color="authStore.isAuthenticated ? 'success' : 'error'"
          border="left"
          class="mb-3"
      >
        Authentication Status: {{ authStore.isAuthenticated ? 'Authenticated' : 'Not Authenticated' }}
      </v-alert>

      <div class="d-flex align-center mb-2">
        <strong class="mr-2">JWT Token:</strong>
        <code v-if="authStore.token" class="text-truncate">{{ authStore.token.substring(0, 15) }}...</code>
        <span v-else class="red--text">Missing</span>
      </div>

      <div class="d-flex align-center mb-2">
        <strong class="mr-2">User Email:</strong>
        <span>{{ authStore.user?.email || 'Not loaded' }}</span>
      </div>

      <div class="d-flex align-center mb-2">
        <strong class="mr-2">API Key:</strong>
        <code v-if="authStore.user?.apiKey" class="text-truncate">{{ authStore.user.apiKey.substring(0, 10) }}...</code>
        <span v-else class="red--text">Missing</span>
      </div>

      <v-alert v-if="!authStore.user?.apiKey" color="error" class="mt-2">
        API key missing! Go to Dashboard and generate one.
      </v-alert>

      <div class="mt-4">
        <v-btn color="primary" @click="refreshAuthState" :loading="loading">
          Refresh Auth
        </v-btn>

        <v-btn class="ml-2" color="success" @click="testApiKey" :loading="testing" :disabled="!authStore.user?.apiKey">
          Test API Key
        </v-btn>
      </div>

      <v-alert v-if="message" :color="success ? 'success' : 'error'" class="mt-4">
        {{ message }}
      </v-alert>
    </v-card-text>
  </v-card>

  <v-btn
      v-else
      color="warning"
      @click="showDebugger = true"
      fixed
      bottom
      right
      fab
      small
  >
    <v-icon>mdi-bug</v-icon>
  </v-btn>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import api from '@/services/api';

const authStore = useAuthStore();
const showDebugger = ref(false);
const loading = ref(false);
const testing = ref(false);
const success = ref(false);
const message = ref('');

const refreshAuthState = async () => {
  loading.value = true;
  try {
    await authStore.fetchUser();
    success.value = true;
    message.value = 'Authentication state refreshed successfully.';
  } catch (error) {
    success.value = false;
    message.value = `Auth refresh failed: ${error.message}`;
  } finally {
    loading.value = false;
  }
};

const testApiKey = async () => {
  testing.value = true;
  try {
    // Use the api instance that has the proper interceptors configured
    const response = await api.get('/history/recent', {
      params: { limit: 1 }
    });

    success.value = true;
    message.value = `API key authentication works! Received ${
        Array.isArray(response.data) ? response.data.length : 0
    } history items.`;
  } catch (error) {
    success.value = false;
    message.value = `API key test failed: ${error.response?.data?.message || error.message}`;
  } finally {
    testing.value = false;
  }
};
</script>

<style scoped>
.auth-debugger {
  max-width: 500px;
  z-index: 1000;
}
code {
  background-color: #f5f5f5;
  padding: 2px 4px;
  border-radius: 4px;
  font-family: monospace;
  word-break: break-all;
}
</style>