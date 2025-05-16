// src/components/admin/AdminHistoryComponent.vue
<template>
  <v-card class="my-4">
    <v-card-title class="d-flex align-center">
      <div>
        <v-icon start color="primary" class="mr-2">mdi-history</v-icon>
        {{ $t('admin.allUserActivity') }}
      </div>
      <v-spacer></v-spacer>
      <v-btn
          color="primary"
          prepend-icon="mdi-export"
          @click="exportCSV"
          :loading="exporting"
          class="mr-2"
      >
        {{ $t('admin.exportCSV') }}
      </v-btn>
      <v-btn
          color="error"
          prepend-icon="mdi-delete"
          @click="showClearDialog = true"
      >
        {{ $t('admin.clearHistory') }}
      </v-btn>
    </v-card-title>
    <v-divider></v-divider>
    <v-card-text class="pa-0">
      <v-list lines="two">
        <v-list-item
            v-for="(activity, index) in allActivities"
            :key="index"
            :title="formatActivityTitle(activity)"
            :subtitle="`${activity.User?.email || 'Unknown'} • ${formatTimestamp(activity.createdAt)}`"
        >
          <template v-slot:prepend>
            <v-avatar color="grey-lighten-3">
              <v-icon :color="getActivityIconColor(activity)">{{ getActivityIcon(activity) }}</v-icon>
            </v-avatar>
          </template>
          <template v-slot:append>
            <div class="d-flex flex-column align-end">
              <div class="text-caption" v-if="activity.city && activity.city !== 'Unknown'">
                {{ activity.city }}, {{ activity.country }}
              </div>
            </div>
          </template>
        </v-list-item>

        <div v-if="loading" class="pa-4 text-center">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
        </div>

        <div v-if="!loading && allActivities.length === 0" class="pa-4 text-center">
          <v-icon size="64" color="grey-lighten-2" class="mb-2">mdi-history</v-icon>
          <p>{{ $t('admin.noHistoryFound') }}</p>
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

    <!-- Confirmation Dialog -->
    <v-dialog v-model="showClearDialog" max-width="500px">
      <v-card>
        <v-card-title class="text-h5">{{ $t('admin.clearHistoryConfirm') }}</v-card-title>
        <v-card-text>
          {{ $t('admin.clearHistoryWarning') }}
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="text" @click="showClearDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" variant="flat" @click="clearHistory" :loading="clearing">{{ $t('admin.clearAll') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Authentication Debug Dialog -->
    <v-dialog v-model="showAuthDebug" max-width="600px">
      <v-card>
        <v-card-title class="text-h5">Authentication Debug</v-card-title>
        <v-card-text>
          <div class="mb-2"><strong>User:</strong> {{ authStore.user?.email || 'Not logged in' }}</div>
          <div class="mb-2"><strong>Is Admin:</strong> {{ authStore.isAdmin ? 'Yes' : 'No' }}</div>
          <div class="mb-2"><strong>Has Token:</strong> {{ authStore.token ? 'Yes' : 'No' }}</div>
          <div class="mb-2"><strong>Has API Key:</strong> {{ authStore.user?.apiKey ? 'Yes' : 'No' }}</div>
          <v-alert type="warning" class="mt-4" v-if="!authStore.isAdmin">
            You need admin privileges to view history records. Please contact your system administrator.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="refreshAuth">Refresh Auth</v-btn>
          <v-btn color="primary" variant="text" @click="showAuthDebug = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Success/error messages -->
    <v-snackbar v-model="showSnackbar" :color="snackbarColor">
      {{ snackbarText }}
      <template v-slot:actions v-if="authError">
        <v-btn variant="text" @click="showAuthDebug = true">Debug</v-btn>
      </template>
    </v-snackbar>
  </v-card>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import api from '@/services/api';  // ⚠️ Import your configured API service
import { useAuthStore } from '@/stores/auth';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const authStore = useAuthStore();

const allActivities = ref([]);
const loading = ref(false);
const exporting = ref(false);
const clearing = ref(false);
const currentPage = ref(1);
const totalPages = ref(1);
const showClearDialog = ref(false);
const showSnackbar = ref(false);
const snackbarColor = ref('success');
const snackbarText = ref('');
const authError = ref(false);
const showAuthDebug = ref(false);

// Base API URL with proper configuration
const apiUrl = computed(() => import.meta.env.VITE_API_URL || '/api');

onMounted(() => {
  // Check if the user is an admin before loading
  if (authStore.isAuthenticated && authStore.isAdmin) {
    loadHistory();
  } else if (authStore.isAuthenticated && !authStore.isAdmin) {
    showErrorSnackbar(t('admin.notAuthorized'));
    authError.value = true;
  } else {
    authStore.fetchUser().then(() => {
      if (authStore.isAdmin) {
        loadHistory();
      } else {
        showErrorSnackbar(t('admin.notAuthorized'));
        authError.value = true;
      }
    }).catch(err => {
      console.error('Failed to fetch user:', err);
      showErrorSnackbar(t('admin.authFailed'));
      authError.value = true;
    });
  }
});

const refreshAuth = async () => {
  try {
    await authStore.fetchUser();
    if (authStore.isAdmin) {
      loadHistory();
      showSuccessSnackbar('Authentication refreshed');
    } else {
      showErrorSnackbar(t('admin.notAuthorized'));
      authError.value = true;
    }
  } catch (error) {
    console.error('Auth refresh failed:', error);
    showErrorSnackbar('Auth refresh failed');
    authError.value = true;
  }
};

const getAuthHeaders = () => {
  const headers = {};

  if (authStore.token) {
    headers['Authorization'] = `Bearer ${authStore.token}`;
  }

  if (authStore.user?.apiKey) {
    headers['X-API-Key'] = authStore.user.apiKey;
  }

  return headers;
};

const loadHistory = async () => {
  if (!authStore.isAuthenticated || !authStore.isAdmin) {
    authError.value = true;
    showErrorSnackbar(t('admin.notAuthorized'));
    return;
  }

  loading.value = true;

  try {
    // Use the API service if configured, or fallback to axios
    const response = await axios.get(
        `${apiUrl.value}/history/admin/all`,
        {
          params: { page: currentPage.value, limit: 20 },
          headers: getAuthHeaders()
        }
    );

    console.log('History response:', response.data);
    allActivities.value = response.data.data || [];
    totalPages.value = response.data.pagination?.pages || 1;
    authError.value = false;
  } catch (error) {
    console.error('Failed to load history:', error);

    // Show detailed error information
    if (error.response) {
      console.log('Error response:', error.response);
      if (error.response.status === 401) {
        authError.value = true;
        showErrorSnackbar(t('admin.unauthorizedAccess'));
      } else if (error.response.status === 403) {
        authError.value = true;
        showErrorSnackbar(t('admin.forbiddenAccess'));
      } else {
        showErrorSnackbar(`${t('admin.historyLoadFailed')}: ${error.response.status}`);
      }
    } else {
      showErrorSnackbar(t('admin.historyLoadFailed'));
    }

    allActivities.value = [];
  } finally {
    loading.value = false;
  }
};

const exportCSV = async () => {
  if (!authStore.isAuthenticated || !authStore.isAdmin) {
    authError.value = true;
    showErrorSnackbar(t('admin.notAuthorized'));
    return;
  }

  exporting.value = true;

  try {
    const response = await axios.get(
        `${apiUrl.value}/history/admin/export`,
        {
          headers: getAuthHeaders(),
          responseType: 'blob'
        }
    );

    // Create a download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    const dateStr = new Date().toISOString().split('T')[0];
    link.setAttribute('download', `history-export-${dateStr}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showSuccessSnackbar(t('admin.exportSuccess'));
  } catch (error) {
    console.error('Failed to export history:', error);

    if (error.response && error.response.status === 401) {
      authError.value = true;
      showErrorSnackbar(t('admin.unauthorizedAccess'));
    } else {
      showErrorSnackbar(t('admin.exportFailed'));
    }
  } finally {
    exporting.value = false;
  }
};

const clearHistory = async () => {
  if (!authStore.isAuthenticated || !authStore.isAdmin) {
    authError.value = true;
    showErrorSnackbar(t('admin.notAuthorized'));
    return;
  }

  clearing.value = true;

  try {
    await axios.delete(
        `${apiUrl.value}/history/admin/clear`,
        {
          headers: getAuthHeaders()
        }
    );

    allActivities.value = [];
    showClearDialog.value = false;
    showSuccessSnackbar(t('admin.historyCleared'));
  } catch (error) {
    console.error('Failed to clear history:', error);

    if (error.response && error.response.status === 401) {
      authError.value = true;
      showErrorSnackbar(t('admin.unauthorizedAccess'));
    } else {
      showErrorSnackbar(t('admin.clearFailed'));
    }
  } finally {
    clearing.value = false;
  }
};

// ... rest of your functions remain the same
const formatActivityTitle = (activity) => {
  // Extract the operation type from the action
  const operation = activity.action.startsWith('pdf-')
      ? activity.action.replace('pdf-', '')
      : activity.action;

  const translatedOperation = t(`operations.${operation}`, operation);

  if (activity.description) {
    return activity.description;
  }

  return `${translatedOperation} ${t('operations.operation')}`;
};

const formatTimestamp = (timestamp) => {
  if (!timestamp) return '';

  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  // Pro relativní čas s překlady
  if (diffMins < 1) {
    return t('timeAgo.justNow');
  } else if (diffMins < 60) {
    return t('timeAgo.minutesAgo', { count: diffMins });
  } else if (diffHours < 24) {
    return t('timeAgo.hoursAgo', { count: diffHours });
  } else if (diffDays < 7) {
    return t('timeAgo.daysAgo', { count: diffDays });
  } else {
    // Formátování data včetně času
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  }
};

const getActivityIcon = (activity) => {
  const operation = activity.action.replace('pdf-', '');

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
    'login': 'mdi-login',
    'register': 'mdi-account-plus',
    'test': 'mdi-test-tube'
  };

  return iconMap[operation] || 'mdi-file-pdf-box';
};

const getActivityIconColor = (activity) => {
  const operation = activity.action.replace('pdf-', '');

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
    'login': 'blue-grey',
    'register': 'blue-grey',
    'test': 'blue-grey'
  };

  return colorMap[operation] || 'grey';
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
</script>