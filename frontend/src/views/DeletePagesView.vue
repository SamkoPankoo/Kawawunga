<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.deletePages') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ $t('pdf.deletePagesDesc') }}</p>

            <v-file-input
                v-model="selectedFile"
                :label="$t('pdf.dropFilesHere')"
                accept="application/pdf"
                prepend-icon="mdi-file-pdf-box"
                :rules="[rules.required]"
                @update:model-value="handleFileChange"
                counter
                show-size
            ></v-file-input>

            <v-alert
                v-if="error"
                type="error"
                variant="tonal"
                class="mb-4"
                closable
                @click:close="error = null"
            >
              {{ error }}
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row v-if="pdfInfo">
      <v-col cols="12" md="7">
        <v-card>
          <v-card-title class="d-flex align-center">
            <span>{{ $t('pdf.preview') }}</span>
            <v-spacer></v-spacer>
            <v-chip v-if="isPreviewing" color="error" size="small" class="ml-2">
              {{ $t('pdf.previewingDeletion') }}
            </v-chip>
          </v-card-title>
          <v-card-text>
            <vue-pdf-embed
                v-if="currentPreviewUrl"
                :source="currentPreviewUrl"
                :page="currentPage"
                @loaded="handlePdfLoaded"
                @rendered="pageLoaded"
                @error="handleError"
                style="display: block; width: 100%;"
            ></vue-pdf-embed>
            <v-progress-circular
                v-if="loading"
                indeterminate
                color="primary"
                class="mt-5 d-flex mx-auto"
            ></v-progress-circular>

            <div class="d-flex justify-center align-center mt-4">
              <v-btn icon="mdi-chevron-left" @click="prevPage" :disabled="currentPage <= 1"></v-btn>
              <span class="mx-2">{{ currentPage }} / {{ numPages }}</span>
              <v-btn icon="mdi-chevron-right" @click="nextPage" :disabled="currentPage >= numPages"></v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="5">
        <v-card>
          <v-card-title>{{ $t('pdf.deleteOptions') }}</v-card-title>
          <v-card-text>
            <v-select
                v-model="deleteMethod"
                :items="deleteMethodOptions"
                :label="$t('pdf.deleteSelection')"
                @update:model-value="updateDeleteMethod"
                :disabled="numPages <= 1"
            ></v-select>

            <template v-if="deleteMethod === 'current'">
              <p class="text-body-2 mb-2">
                {{ $t('pdf.currentPage') }}: {{ currentPage }}
              </p>
            </template>

            <template v-if="deleteMethod === 'range'">
              <v-row>
                <v-col cols="6">
                  <v-text-field
                      v-model="pageRange.from"
                      type="number"
                      :label="$t('pdf.from')"
                      min="1"
                      :max="numPages"
                      :rules="[rules.required, rules.validPage]"
                      @update:model-value="previewDeletePages"
                  ></v-text-field>
                </v-col>
                <v-col cols="6">
                  <v-text-field
                      v-model="pageRange.to"
                      type="number"
                      :label="$t('pdf.to')"
                      min="1"
                      :max="numPages"
                      :rules="[rules.required, rules.validPage, validateRange]"
                      @update:model-value="previewDeletePages"
                  ></v-text-field>
                </v-col>
              </v-row>
            </template>

            <template v-if="deleteMethod === 'custom'">
              <v-text-field
                  v-model="customPages"
                  :label="$t('pdf.customPages')"
                  :hint="$t('pdf.customPagesHint')"
                  persistent-hint
                  :rules="[rules.required, validateCustomPages]"
                  @update:model-value="previewDeletePages"
              ></v-text-field>
            </template>

            <template v-if="deleteMethod === 'select'">
              <p class="text-body-2 mb-2">{{ $t('pdf.selectPagesToDelete') }}</p>
              <div class="page-selection-grid">
                <v-checkbox
                    v-for="page in numPages"
                    :key="page"
                    v-model="selectedPages"
                    :value="page"
                    :label="page.toString()"
                    hide-details
                    density="compact"
                    class="page-checkbox"
                    @update:model-value="previewDeletePages"
                ></v-checkbox>
              </div>
              <p class="text-caption mt-2">
                {{ $t('pdf.selectedPagesCount', { count: selectedPages.length }) }}
              </p>
            </template>

            <v-divider class="my-4"></v-divider>

            <v-alert
                v-if="numPages <= 1"
                type="warning"
                variant="tonal"
                class="mb-4"
            >
              {{ $t('pdf.minPagesWarning') }}
            </v-alert>

            <v-alert
                v-else-if="totalPagesToDelete >= numPages"
                type="warning"
                variant="tonal"
                class="mb-4"
            >
              {{ $t('pdf.cannotDeleteAllPages') }}
            </v-alert>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                :disabled="!canDeletePages || processing"
                :loading="processing"
                @click="deletePages"
                prepend-icon="mdi-file-remove"
                size="large"
            >
              {{ $t('pdf.applyDelete') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="showResultDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h5">
          <v-icon color="success" class="mr-2">mdi-check-circle</v-icon>
          {{ $t('common.success') }}
        </v-card-title>
        <v-card-text>
          <p>{{ $t('pdf.pagesDeleted') }}</p>
          <p class="text-grey">{{ resultFilename }}</p>
          <p>{{ $t('pdf.pagesDeletedDetails', { count: getPagesToDelete().length, total: numPagesOriginal }) }}</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
              color="primary"
              variant="text"
              @click="showResultDialog = false"
          >
            {{ $t('common.close') }}
          </v-btn>
          <v-btn
              color="primary"
              @click="downloadResult"
              prepend-icon="mdi-download"
          >
            {{ $t('common.download') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <LogOperation
        v-if="operationSuccess"
        :operation="'delete'"
        :description="getLogDescription()"
        :metadata="getLogMetadata()"
    />
  </v-container>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';

import VuePdfEmbed from 'vue-pdf-embed';
import { useAuthStore } from '@/stores/auth';
import LogOperation from '@/components/pdf/LogOperation.vue';
const operationSuccess = ref(false);
const resultFileId = ref(null);

const { t } = useI18n();
const authStore = useAuthStore();

const selectedFile = ref(null);
const pdfUrl = ref(null);
const pdfInfo = ref(null);
const currentPage = ref(1);
const numPages = ref(0);
const numPagesOriginal = ref(0);
const loading = ref(false);
const error = ref(null);
const fileId = ref(null);

// For live preview
const previewPdfUrl = ref(null);
const isPreviewing = ref(false);
const previewPending = ref(false);
const previewTimeout = ref(null);

// Current preview that's being displayed
const currentPreviewUrl = computed(() => {
  return previewPdfUrl.value || pdfUrl.value;
});

// Delete options
const deleteMethod = ref('current');
const pageRange = ref({ from: 1, to: 1 });
const customPages = ref('');
const selectedPages = ref([]);
const processing = ref(false);
const showResultDialog = ref(false);
const resultFileUrl = ref(null);
const resultFilename = ref(null);

const deleteMethodOptions = computed(() => [
  { title: t('pdf.currentPage'), value: 'current' },
  { title: t('pdf.pageRange'), value: 'range' },
  { title: t('pdf.customPages'), value: 'custom' },
  { title: t('pdf.selectPagesOption'), value: 'select' }
]);

const rules = {
  required: value => !!value || t('validation.required'),
  validPage: value => {
    const page = parseInt(value);
    return (page >= 1 && page <= numPages.value) || t('validation.pageRange', { max: numPages.value });
  }
};

const getLogDescription = () => {
  const pagesToDelete = getPagesToDelete();
  return `Deleted ${pagesToDelete.length} pages from ${numPagesOriginal.value}-page document`;
};

const getLogMetadata = () => {
  return {
    fileName: selectedFile.value?.name,
    deleteMethod: deleteMethod.value,
    deletedPages: getPagesToDelete(),
    resultFileName: resultFilename.value,
    timestamp: new Date().toISOString()
  };
};

const validateRange = () => {
  const start = parseInt(pageRange.value.from);
  const end = parseInt(pageRange.value.to);
  return start <= end || t('validation.startEndOrder');
};

const validateCustomPages = (value) => {
  if (!value) return true;

  // Check format (comma-separated numbers)
  const pagePattern = /^(\d+)(,\s*\d+)*$/;
  if (!pagePattern.test(value)) {
    return t('validation.extractPagesFormat');
  }

  // Check if all page numbers are valid
  const pages = value.split(',').map(p => parseInt(p.trim()));
  const invalidPages = pages.filter(p => p < 1 || p > numPages.value);

  if (invalidPages.length > 0) {
    return t('validation.invalidPages', { pages: invalidPages.join(', '), max: numPages.value });
  }

  return true;
};

// Get pages to delete based on the current selection method
const getPagesToDelete = () => {
  let pages = [];

  if (deleteMethod.value === 'current') {
    pages = [currentPage.value];
  } else if (deleteMethod.value === 'range') {
    const start = parseInt(pageRange.value.from);
    const end = parseInt(pageRange.value.to);

    if (!isNaN(start) && !isNaN(end) && start >= 1 && end <= numPages.value) {
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
    }
  } else if (deleteMethod.value === 'custom') {
    if (validateCustomPages(customPages.value) === true) {
      pages = customPages.value.split(',').map(p => parseInt(p.trim()));
    }
  } else if (deleteMethod.value === 'select') {
    pages = [...selectedPages.value];
  }

  return pages;
};

// Calculate total pages to delete
const totalPagesToDelete = computed(() => {
  return getPagesToDelete().length;
});

const canDeletePages = computed(() => {
  if (!pdfInfo.value || numPages.value <= 1) return false;

  const pagesToDelete = getPagesToDelete();

  // Can't delete if no pages selected or all pages would be deleted
  if (pagesToDelete.length === 0 || pagesToDelete.length >= numPages.value) {
    return false;
  }

  if (deleteMethod.value === 'range') {
    const start = parseInt(pageRange.value.from);
    const end = parseInt(pageRange.value.to);
    return !isNaN(start) && !isNaN(end) && start >= 1 && end <= numPages.value && start <= end;
  }

  if (deleteMethod.value === 'custom') {
    return validateCustomPages(customPages.value) === true;
  }

  if (deleteMethod.value === 'select') {
    return selectedPages.value.length > 0 && selectedPages.value.length < numPages.value;
  }

  return true;
});

watch(() => numPages.value, (newValue) => {
  if (newValue > 0) {
    pageRange.value.to = newValue;
    numPagesOriginal.value = newValue;
  }
});

watch(() => currentPage.value, () => {
  if (deleteMethod.value === 'current') {
    pageRange.value = { from: currentPage.value, to: currentPage.value };
    previewDeletePages();
  }
});

// Watch for changes in delete options to update preview
watch([
  () => deleteMethod.value,
  () => pageRange.value.from,
  () => pageRange.value.to,
  () => customPages.value,
  () => selectedPages.value
], () => {
  previewDeletePages();
}, { deep: true });

const handleFileChange = () => {
  if (selectedFile.value) {
    // Reset various states
    if (previewPdfUrl.value) {
      URL.revokeObjectURL(previewPdfUrl.value);
      previewPdfUrl.value = null;
    }
    isPreviewing.value = false;
    selectedPages.value = [];
    currentPage.value = 1;

    // Create a URL for the PDF
    pdfUrl.value = URL.createObjectURL(selectedFile.value);
    uploadFile();
  } else {
    pdfUrl.value = null;
    previewPdfUrl.value = null;
    pdfInfo.value = null;
    fileId.value = null;
  }
};

const handlePdfLoaded = (e) => {
  numPages.value = e.numPages;
  if (!numPagesOriginal.value) {
    numPagesOriginal.value = e.numPages;
  }
  pageLoaded();
};

const pageLoaded = () => {
  loading.value = false;
};

const handleError = (err) => {
  console.error('PDF error:', err);
  loading.value = false;
  error.value = t('pdf.pdfLoadError');
};

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--;
    loading.value = true;
  }
};

const nextPage = () => {
  if (currentPage.value < numPages.value) {
    currentPage.value++;
    loading.value = true;
  }
};

const updateDeleteMethod = () => {
  if (deleteMethod.value === 'current') {
    pageRange.value = { from: currentPage.value, to: currentPage.value };
  } else if (deleteMethod.value === 'range') {
    pageRange.value = { from: 1, to: numPages.value };
  } else if (deleteMethod.value === 'select') {
    selectedPages.value = [currentPage.value];
  } else {
    customPages.value = '';
  }

  // Update preview after changing method
  previewDeletePages();
};

const uploadFile = async () => {
  if (!selectedFile.value) return;

  loading.value = true;
  error.value = null;

  try {
    const formData = new FormData();
    formData.append('pdf', selectedFile.value);

    const response = await axios.post(
        `/python-api/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
    );

    fileId.value = response.data.id;
    pdfInfo.value = response.data;

    // Initialize options after upload
    updateDeleteMethod();
  } catch (error) {
    console.error('Error uploading PDF:', error);
    error.value = error.response?.data?.error || t('pdf.uploadError');
  } finally {
    loading.value = false;
  }
};

// Function to create live preview of pages to delete
const previewDeletePages = () => {
  // Debounce preview requests
  if (previewTimeout.value) {
    clearTimeout(previewTimeout.value);
  }

  previewTimeout.value = setTimeout(async () => {
    if (!fileId.value || previewPending.value) return;

    // Only preview if we have valid pages to delete
    const pagesToDelete = getPagesToDelete();

    if (pagesToDelete.length === 0 || pagesToDelete.length >= numPages.value) {
      if (previewPdfUrl.value) {
        URL.revokeObjectURL(previewPdfUrl.value);
        previewPdfUrl.value = null;
        isPreviewing.value = false;
      }
      return;
    }

    previewPending.value = true;

    try {
      const requestData = {
        file_id: fileId.value,
        pages: pagesToDelete
      };

      const headers = {
        'Content-Type': 'application/json'
      };

      // Add API key if user is authenticated
      if (authStore.token) {
        headers['X-API-Key'] = authStore.user?.apiKey;
      }

      const response = await axios.post(
          `/python-api/preview-remove-pages`,
          requestData,
          { headers }
      );

      // Get the preview PDF
      if (response.data && response.data.id) {
        const previewResponse = await axios.get(
            `/python-api/download/${response.data.id}`,
            { responseType: 'blob' }
        );

        // If we had a previous preview, revoke its URL
        if (previewPdfUrl.value) {
          URL.revokeObjectURL(previewPdfUrl.value);
        }

        // Create a new object URL for the preview
        previewPdfUrl.value = URL.createObjectURL(new Blob([previewResponse.data]));
        isPreviewing.value = true;
      }
    } catch (err) {
      console.error('Error creating delete preview:', err);
      // If preview fails, just use the original PDF
      if (previewPdfUrl.value) {
        URL.revokeObjectURL(previewPdfUrl.value);
        previewPdfUrl.value = null;
        isPreviewing.value = false;
      }
    } finally {
      previewPending.value = false;
    }
  }, 500); // 500ms debounce
};

const deletePages = async () => {
  if (!fileId.value) return;

  processing.value = true;
  error.value = null;

  try {
    const pagesToDelete = getPagesToDelete();

    if (pagesToDelete.length === 0 || pagesToDelete.length >= numPages.value) {
      error.value = t('pdf.invalidDeleteSelection');
      processing.value = false;
      return;
    }

    const requestData = {
      file_id: fileId.value,
      pages: pagesToDelete
    };

    const headers = {
      'Content-Type': 'application/json'
    };

    // Add API key if user is authenticated
    if (authStore.token) {
      headers['X-API-Key'] = authStore.user?.apiKey;
    }

    const response = await axios.post(
        `/python-api/remove-pages`,
        requestData,
        { headers }
    );

    resultFileUrl.value = response.data.id;
    resultFileId.value = response.data.id;
    operationSuccess.value = true;
    resultFilename.value = response.data.filename || 'pages_deleted.pdf';

    // Update the preview to show the final PDF with pages deleted
    const finalPdfResponse = await axios.get(
        `/python-api/download/${response.data.id}`,
        { responseType: 'blob' }
    );

    // If we had a previous preview, revoke its URL
    if (previewPdfUrl.value) {
      URL.revokeObjectURL(previewPdfUrl.value);
    }

    // Create a new object URL for the final PDF
    previewPdfUrl.value = URL.createObjectURL(new Blob([finalPdfResponse.data]));
    isPreviewing.value = false;

    // Update fileId to point to the new PDF with pages deleted
    fileId.value = response.data.id;
    pdfInfo.value = response.data;

    // Show result dialog
    showResultDialog.value = true;
  } catch (error) {
    console.error('Error deleting pages:', error);
    error.value = error.response?.data?.error || t('pdf.deleteError');
  } finally {
    processing.value = false;
  }
};

const downloadResult = async () => {
  if (!resultFileUrl.value) return;

  try {
    const response = await axios.get(
        `/python-api/download/${resultFileUrl.value}`,
        { responseType: 'blob' }
    );

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', resultFilename.value);
    document.body.appendChild(link);
    link.click();
    link.remove();

    // Clean up the URL
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error downloading file:', error);
    error.value = t('pdf.downloadError');
  }
};

// Clean up object URLs when component is destroyed
onBeforeUnmount(() => {
  if (pdfUrl.value) {
    URL.revokeObjectURL(pdfUrl.value);
  }
  if (previewPdfUrl.value) {
    URL.revokeObjectURL(previewPdfUrl.value);
  }

  // Clear any pending timers
  if (previewTimeout.value) {
    clearTimeout(previewTimeout.value);
  }
});

// Initialize
updateDeleteMethod();
</script>

<style scoped>
.page-selection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(70px, 1fr));
  gap: 8px;
  margin-bottom: 16px;
}

.page-checkbox {
  margin: 4px 0;
}
</style>

