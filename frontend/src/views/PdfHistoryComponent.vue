<template>
  <v-card class="my-4">
    <v-card-title>
      <v-icon start color="primary" class="mr-2">mdi-history</v-icon>
      {{ $t('dashboard.recentActivity') }}
    </v-card-title>
    <v-divider></v-divider>
    <v-card-text class="pa-0">
      <v-list lines="two">
        <v-list-item
            v-for="(activity, index) in pdfActivities"
            :key="index"
            :title="formatActivityTitle(activity)"
            :subtitle="formatTimestamp(activity.createdAt)"
        >
          <template v-slot:prepend>
            <v-avatar color="grey-lighten-3">
              <v-icon :color="getActivityIconColor(activity)">{{ getActivityIcon(activity) }}</v-icon>
            </v-avatar>
          </template>
          <template v-slot:append v-if="activity.metadata && activity.metadata.fileId">
            <v-btn
                variant="text"
                size="small"
                color="primary"
                @click="downloadFile(activity)"
            >
              {{ $t('dashboard.downloadFile') }}
            </v-btn>
          </template>
        </v-list-item>

        <div v-if="loading" class="pa-4 text-center">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
        </div>

        <div v-if="!loading && pdfActivities.length === 0" class="pa-4 text-center">
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
  </v-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const authStore = useAuthStore();

const pdfActivities = ref([]);
const loading = ref(false);
const currentPage = ref(1);
const totalPages = ref(1);

onMounted(() => {
  loadHistory();
});

const loadHistory = async () => {
  if (!authStore.token) return;

  loading.value = true;

  try {
    const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/pdf-logs`,
        {
          params: { page: currentPage.value, limit: 10 },
          headers: { 'Authorization': `Bearer ${authStore.token}` }
        }
    );

    pdfActivities.value = response.data.data;
    totalPages.value = response.data.pagination.pages;
  } catch (error) {
    console.error('Failed to load PDF history:', error);
    pdfActivities.value = [];
  } finally {
    loading.value = false;
  }
};

const formatActivityTitle = (activity) => {
  // Extract the operation type from the action (remove "pdf-" prefix)
  const operation = activity.action.replace('pdf-', '');

  // If there's metadata with a filename, include it
  if (activity.metadata && activity.metadata.fileName) {
    return `${t(`pdf.${operation}Operation`)}: ${activity.metadata.fileName}`;
  }

  // Default fallback
  return activity.description || t(`pdf.${operation}Operation`);
};

const formatTimestamp = (timestamp) => {
  if (!timestamp) return '';

  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  // Format relative time
  if (diffMins < 1) {
    return t('common.justNow');
  } else if (diffMins < 60) {
    return t('common.minutesAgo', { count: diffMins });
  } else if (diffHours < 24) {
    return t('common.hoursAgo', { count: diffHours });
  } else if (diffDays < 7) {
    return t('common.daysAgo', { count: diffDays });
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
  };

  return colorMap[operation] || 'grey';
};

const downloadFile = async (activity) => {
  if (!activity.metadata || !activity.metadata.fileId) return;

  try {
    const response = await axios.get(
        `${import.meta.env.VITE_PYTHON_API_URL}/download/${activity.metadata.fileId}`,
        { responseType: 'blob' }
    );

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', activity.metadata.fileName || 'document.pdf');
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    console.error('Error downloading file:', error);
    alert(t('pdf.downloadError'));
  }
};
</script>