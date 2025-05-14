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
            <v-chip size="small" :color="activity.accessType === 'api' ? 'blue' : 'green'">
              {{ activity.accessType }}
            </v-chip>
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

    <!-- Success/error messages -->
    <v-snackbar v-model="showSnackbar" :color="snackbarColor">
      {{ snackbarText }}
    </v-snackbar>
  </v-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
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

onMounted(() => {
  // Check if the user is an admin before loading
  if (authStore.isAdmin) {
    loadHistory();
  } else {
    showErrorSnackbar(t('admin.notAuthorized'));
  }
});

const loadHistory = async () => {
  if (!authStore.token || !authStore.isAdmin) {
    console.error('Not authorized to view admin history');
    return;
  }

  loading.value = true;

  try {
    const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/history/admin/all`,
        {
          params: { page: currentPage.value, limit: 20 },
          headers: { 'Authorization': `Bearer ${authStore.token}` }
        }
    );

    allActivities.value = response.data.data;
    totalPages.value = response.data.pagination.pages;
  } catch (error) {
    console.error('Failed to load history:', error);
    allActivities.value = [];

    // Specifická chyba pro vypršení tokenu
    if (error.response && error.response.status === 401) {
      showErrorSnackbar(t('auth.sessionExpired'));
      // Volitelně: pokus o obnovení tokenu nebo odhlášení
      await authStore.logout();
    } else {
      showErrorSnackbar(t('admin.historyLoadFailed'));
    }
  } finally {
    loading.value = false;
  }
};
const exportCSV = async () => {
  if (!authStore.token || !authStore.isAdmin) {
    showErrorSnackbar(t('admin.notAuthorized'));
    return;
  }

  exporting.value = true;

  try {
    const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/history/admin/export`,
        {
          headers: {
            'Authorization': `Bearer ${authStore.token}`,
          },
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
    showErrorSnackbar(t('admin.exportFailed'));
  } finally {
    exporting.value = false;
  }
};

const clearHistory = async () => {
  if (!authStore.token || !authStore.isAdmin) {
    showErrorSnackbar(t('admin.notAuthorized'));
    return;
  }

  clearing.value = true;

  try {
    await axios.delete(
        `${import.meta.env.VITE_API_URL}/history/admin/clear`,
        {
          headers: { 'Authorization': `Bearer ${authStore.token}` }
        }
    );

    allActivities.value = [];
    showClearDialog.value = false;
    showSuccessSnackbar(t('admin.historyCleared'));
  } catch (error) {
    console.error('Failed to clear history:', error);
    showErrorSnackbar(t('admin.clearFailed'));
  } finally {
    clearing.value = false;
  }
};

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
  // Same logic as in your PdfHistoryComponent.vue
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
  // Same logic as in your PdfHistoryComponent.vue
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