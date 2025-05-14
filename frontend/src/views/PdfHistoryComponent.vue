<template>
  <v-card class="my-4">
    <v-card-title>
      <v-icon start color="primary" class="mr-2">mdi-history</v-icon>
      {{ $t('dashboard.recentActivity') }}
      <v-spacer></v-spacer>
      <v-btn size="small" color="primary" variant="text" @click="createTestLog" class="mr-2">
        {{ $t('dashboard.testLog') }}
      </v-btn>
      <v-btn size="small" variant="text" @click="refreshHistory">
        <v-icon>mdi-refresh</v-icon>
      </v-btn>
    </v-card-title>

    <v-divider></v-divider>

    <v-card-text class="pa-0">
      <v-list lines="two">
        <v-list-item
            v-for="(activity, index) in filteredActivities"
            :key="index"
            :title="formatActivityTitle(activity)"
            :subtitle="formatTimestamp(activity.createdAt)"
        >
          <template v-slot:prepend>
            <v-avatar color="grey-lighten-3">
              <v-icon :color="getActivityIconColor(activity)">{{ getActivityIcon(activity) }}</v-icon>
            </v-avatar>
          </template>
          <template v-slot:append>
            <v-chip size="small" :color="activity.accessType === 'api' ? 'blue' : 'green'">
              {{ activity.accessType || 'frontend' }}
            </v-chip>
          </template>
        </v-list-item>

        <div v-if="loading" class="pa-4 text-center">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
        </div>

        <div v-if="!loading && filteredActivities.length === 0" class="pa-4 text-center">
          <v-icon size="64" color="grey-lighten-2" class="mb-2">mdi-file-outline</v-icon>
          <p>{{ $t('dashboard.noActivity') }}</p>
        </div>
      </v-list>

      <v-card-text v-if="!loading && totalPages > 1" class="text-center">
        <v-pagination
            v-model="currentPage"
            :length="totalPages"
            :total-visible="5"
            @update:model-value="loadHistory"
        ></v-pagination>
      </v-card-text>
    </v-card-text>

    <!-- Success/error messages -->
    <v-snackbar v-model="showSnackbar" :color="snackbarColor">
      {{ snackbarText }}
    </v-snackbar>
  </v-card>

  <v-card class="mt-4" v-if="debugMode">
    <v-card-title>Debug Authentication</v-card-title>
    <v-card-text>
      <p><strong>Authentication Status:</strong> {{ authStore.isAuthenticated ? 'Authenticated' : 'Not Authenticated' }}</p>
      <p><strong>Token:</strong> {{ !!authStore.token ? 'Present' : 'Missing' }}</p>
      <p><strong>User:</strong> {{ authStore.user ? authStore.user.email : 'Not loaded' }}</p>
      <p><strong>API Key:</strong> {{ authStore.user?.apiKey ? authStore.user.apiKey.substring(0, 10) + '...' : 'Missing' }}</p>

      <v-alert v-if="!authStore.user?.apiKey" color="error" class="mt-2">
        You need to generate an API key on your dashboard!
      </v-alert>

      <div class="mt-4">
        <v-btn color="primary" @click="refreshAuthState" :loading="loading">
          Refresh Auth State
        </v-btn>

        <v-btn class="ml-2" color="success" @click="testApiKeyAuth" :loading="testing" :disabled="!authStore.user?.apiKey">
          Test API Key Auth
        </v-btn>

        <v-btn class="ml-2" color="warning" @click="testDirectLog" :loading="logging" :disabled="!authStore.user?.apiKey">
          Test Direct Log
        </v-btn>
      </div>

      <v-alert v-if="result" :color="result.success ? 'success' : 'error'" class="mt-4">
        {{ result.message }}
      </v-alert>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import historyService from '@/services/historyService';
import { useAuthStore } from "@/stores/auth.js";
import { useI18n } from 'vue-i18n';
import api from '@/services/api';

const authStore = useAuthStore();
const { t } = useI18n();

// Configuration
const debugMode = ref(false); // Set to true to show debug card

// Data
const pdfActivities = ref([]);
const loading = ref(false);
const currentPage = ref(1);
const totalPages = ref(1);
const showSnackbar = ref(false);
const snackbarColor = ref('success');
const snackbarText = ref('');
const testing = ref(false);
const logging = ref(false);
const result = ref(null);

// Filter out download operations and duplicate entries
// Only keep backend entries (api)
const filteredActivities = computed(() => {
  // Create a Set to track unique operations
  const uniqueOps = new Set();

  // Filter and deduplicate activities
  return pdfActivities.value.filter(activity => {
    // Skip download operations
    if (activity.action.includes('download') || activity.action.includes('upload')) {
      return false;
    }

    // Generate a unique key for this operation (action + timestamp)
    const opKey = `${activity.action}_${activity.createdAt}`;

    // Skip if we've already seen this operation
    if (uniqueOps.has(opKey)) {
      return false;
    }

    // Add to our set of seen operations
    uniqueOps.add(opKey);

    // Keep only backend entries
    return activity.accessType === 'api';
  });
});

onMounted(() => {
  loadHistory();
  // Refresh history every 30 seconds
  setInterval(refreshHistory, 30000);
});

const refreshAuthState = async () => {
  loading.value = true;
  try {
    await authStore.fetchUser();
    showSuccessSnackbar(t('dashboard.authRefreshed'));
  } catch (error) {
    console.error('Failed to refresh auth state:', error);
    showErrorSnackbar(t('dashboard.authRefreshFailed'));
  } finally {
    loading.value = false;
  }
};

const testApiKeyAuth = async () => {
  testing.value = true;
  try {
    const response = await api.get('/history/recent', {
      params: { limit: 1 }
    });

    console.log('Test API call successful:', response.data);
    showSnackbar.value = true;
    snackbarText.value = t('dashboard.apiTestSuccess');
    result.value = { success: true, message: t('dashboard.apiTestSuccess') };
  } catch (error) {
    console.error('API key test failed:', error);
    showSnackbar.value = true;
    snackbarText.value = `${t('dashboard.apiTestFailed')}: ${error.message}`;
    result.value = { success: false, message: `${t('dashboard.apiTestFailed')}: ${error.message}` };
  } finally {
    testing.value = false;
  }
};

const testDirectLog = async () => {
  logging.value = true;
  try {
    const success = await historyService.logPdfOperation(
        'test',
        t('dashboard.testOperationDesc'),
        { source: 'test-function', timestamp: new Date().toISOString() }
    );

    result.value = {
      success,
      message: success ? t('dashboard.directLogSuccess') : t('dashboard.directLogFailed')
    };

    showSnackbar.value = true;
    snackbarText.value = success ? t('dashboard.directLogSuccess') : t('dashboard.directLogFailed');

    if (success) {
      await loadHistory(); // Refresh history to show the new entry
    }
  } catch (error) {
    console.error('Direct log test failed:', error);
    showSnackbar.value = true;
    snackbarText.value = `${t('dashboard.directLogFailed')}: ${error.message}`;
    result.value = { success: false, message: `${t('dashboard.directLogFailed')}: ${error.message}` };
  } finally {
    logging.value = false;
  }
};

const loadHistory = async () => {
  loading.value = true;

  try {
    const result = await historyService.getPdfHistory(currentPage.value, 10);
    pdfActivities.value = result.items || [];
    totalPages.value = result.pagination?.pages || 1;
  } catch (error) {
    console.error('Failed to load history:', error);
    pdfActivities.value = [];
    showErrorSnackbar(t('dashboard.historyLoadFailed'));
  } finally {
    loading.value = false;
  }
};

const refreshHistory = () => {
  loadHistory();
};

const createTestLog = async () => {
  try {
    const success = await historyService.logPdfOperation(
        'test',
        t('dashboard.testOperationFromHistory'),
        { testData: true, timestamp: new Date().toISOString() }
    );

    if (success) {
      showSuccessSnackbar(t('dashboard.testLogCreated'));
      await loadHistory(); // Refresh to show the new entry
    } else {
      showErrorSnackbar(t('dashboard.testLogFailed'));
    }
  } catch (error) {
    console.error('Failed to create test log:', error);
    showErrorSnackbar(`${t('dashboard.error')}: ${error.message || t('dashboard.unknownError')}`);
  }
};

const showSuccessSnackbar = (text) => {
  snackbarText.value = text;
  snackbarColor.value = 'success';
  showSnackbar.value = true;
};

const showErrorSnackbar = (text) => {
  snackbarText.value = text;
  snackbarColor.value = 'error';
  showSnackbar.value = true;
};

const formatActivityTitle = (activity) => {
  // Extract operation type from action (remove pdf- prefix)
  const operation = activity.action.replace('pdf-', '');

  // Translate the operation name - this assumes you have translation keys like 'operations.merge', etc.
  const translatedOperation = t(`operations.${operation}`, operation);

  // If there's file metadata with filename, include it
  if (activity.metadata && activity.metadata.fileName) {
    return `${translatedOperation}: ${activity.metadata.fileName}`;
  }

  // Fallback to description or generic operation name
  return activity.description || `${translatedOperation}`;
};

const formatTimestamp = (timestamp) => {
  if (!timestamp) return '';

  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  // Format relative time with translations
  if (diffMins < 1) {
    return t('timeAgo.justNow');
  } else if (diffMins < 60) {
    return t('timeAgo.minutesAgo', { count: diffMins });
  } else if (diffHours < 24) {
    return t('timeAgo.hoursAgo', { count: diffHours });
  } else if (diffDays < 7) {
    return t('timeAgo.daysAgo', { count: diffDays });
  } else {
    // Format date
    return date.toLocaleDateString();
  }
};

const getActivityIcon = (activity) => {
  const operation = activity.action.replace('pdf-', '');

  // Map operations to icons
  const iconMap = {
    'merge': 'mdi-file-link',
    'split': 'mdi-file-split',
    'watermark': 'mdi-format-color-highlight',
    'rotate': 'mdi-rotate-right',
    'delete-pages': 'mdi-file-remove',
    'protect': 'mdi-lock',
    'compress': 'mdi-zip-box',
    'edit-metadata': 'mdi-file-document-edit',
    'image-to-pdf': 'mdi-image-multiple',
    'pdf-to-image': 'mdi-file-image',
    'test': 'mdi-test-tube'
  };

  return iconMap[operation] || 'mdi-file-pdf-box';
};

const getActivityIconColor = (activity) => {
  const operation = activity.action.replace('pdf-', '');

  // Map operations to colors
  const colorMap = {
    'merge': 'blue',
    'split': 'orange',
    'watermark': 'purple',
    'rotate': 'green',
    'delete-pages': 'red',
    'protect': 'indigo',
    'compress': 'teal',
    'edit-metadata': 'amber',
    'image-to-pdf': 'deep-purple',
    'pdf-to-image': 'cyan',
    'test': 'blue-grey'
  };

  return colorMap[operation] || 'grey';
};
</script>