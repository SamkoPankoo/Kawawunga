<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.compressPdf') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ $t('pdf.compressPdfDesc') }}</p>

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
          <v-card-title>{{ $t('pdf.preview') }}</v-card-title>
          <v-card-text>
            <pdf
                v-if="pdfUrl"
                :src="pdfUrl"
                :page="currentPage"
                @num-pages="numPages = $event"
                @page-loaded="pageLoaded"
                @error="handleError"
                style="display: block; width: 100%;"
            ></pdf>
            <v-progress-circular
                v-if="loading"
                indeterminate
                color="primary"
                class="mt-5"
            ></v-progress-circular>

            <div class="text-center mt-3">
              <div class="text-body-1 mb-1">{{ $t('pdf.fileInfo') }}</div>
              <div class="d-flex justify-center">
                <v-chip class="mx-1">{{ $t('pdf.pages') }}: {{ numPages }}</v-chip>
                <v-chip class="mx-1">{{ $t('pdf.size') }}: {{ formatFileSize(selectedFile?.size) }}</v-chip>
              </div>
            </div>

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
          <v-card-title>{{ $t('pdf.compressionOptions') }}</v-card-title>
          <v-card-text>
            <h3 class="text-subtitle-1 font-weight-bold mb-2">{{ $t('pdf.compressionLevel') }}</h3>
            <v-radio-group
                v-model="compressionLevel"
                mandatory
            >
              <v-radio
                  :label="$t('pdf.low')"
                  value="low"
              >
                <template v-slot:label>
                  <div>
                    <div class="text-subtitle-2">{{ $t('pdf.low') }}</div>
                    <div class="text-caption">{{ $t('pdf.lowCompressionDesc') }}</div>
                  </div>
                </template>
              </v-radio>
              <v-radio
                  :label="$t('pdf.medium')"
                  value="medium"
              >
                <template v-slot:label>
                  <div>
                    <div class="text-subtitle-2">{{ $t('pdf.medium') }}</div>
                    <div class="text-caption">{{ $t('pdf.mediumCompressionDesc') }}</div>
                  </div>
                </template>
              </v-radio>
              <v-radio
                  :label="$t('pdf.high')"
                  value="high"
              >
                <template v-slot:label>
                  <div>
                    <div class="text-subtitle-2">{{ $t('pdf.high') }}</div>
                    <div class="text-caption">{{ $t('pdf.highCompressionDesc') }}</div>
                  </div>
                </template>
              </v-radio>
            </v-radio-group>

            <v-alert
                type="info"
                variant="tonal"
                class="mt-4"
                icon="mdi-information"
            >
              {{ $t('pdf.compressionNote') }}
            </v-alert>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                :disabled="!canCompress || processing"
                :loading="processing"
                @click="compressPdf"
                prepend-icon="mdi-zip-box"
                size="large"
            >
              {{ $t('pdf.applyCompression') }}
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
          <p>{{ $t('pdf.compressionApplied') }}</p>
          <p class="text-grey">{{ resultFilename }}</p>
          <v-alert
              v-if="originalSize && compressedSize"
              type="success"
              variant="tonal"
              class="mt-3"
          >
            <strong>{{ formatFileSize(originalSize) }}</strong> → <strong>{{ formatFileSize(compressedSize) }}</strong>
            ({{ calculateReduction(originalSize, compressedSize) }}% {{ $t('pdf.reduction') }})
          </v-alert>
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
  </v-container>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import PdfEmbed from 'vue-pdf-embed';
import { useAuthStore } from '../stores/auth';

const { t } = useI18n();
const authStore = useAuthStore();

const selectedFile = ref(null);
const pdfUrl = ref(null);
const pdfInfo = ref(null);
const currentPage = ref(1);
const numPages = ref(0);
const loading = ref(false);
const error = ref(null);
const fileId = ref(null);

// Compression options
const compressionLevel = ref('medium');
const processing = ref(false);
const showResultDialog = ref(false);
const resultFileUrl = ref(null);
const resultFilename = ref(null);
const originalSize = ref(null);
const compressedSize = ref(null);

const rules = {
  required: value => !!value || t('validation.required')
};

const canCompress = computed(() => {
  return pdfInfo.value && selectedFile.value;
});

const formatFileSize = (size) => {
  if (!size) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024;
    i++;
  }

  return `${size.toFixed(2)} ${units[i]}`;
};

const calculateReduction = (original, compressed) => {
  if (!original || !compressed || original === 0) return 0;
  const reduction = ((original - compressed) / original) * 100;
  return reduction.toFixed(1);
};

const handleFileChange = () => {
  if (selectedFile.value) {
    pdfUrl.value = URL.createObjectURL(selectedFile.value);
    originalSize.value = selectedFile.value.size;
    uploadFile();
  } else {
    pdfUrl.value = null;
    pdfInfo.value = null;
    fileId.value = null;
    originalSize.value = null;
  }
};

const pageLoaded = () => {
  loading.value = false;
};

const handleError = (err) => {
  console.error('PDF error:', err);
  loading.value = false;
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

const uploadFile = async () => {
  if (!selectedFile.value) return;

  loading.value = true;
  error.value = null;

  try {
    const formData = new FormData();
    formData.append('pdf', selectedFile.value);

    const response = await axios.post(
        `${import.meta.env.VITE_PYTHON_API_URL}/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
    );

    fileId.value = response.data.id;
    pdfInfo.value = response.data;
  } catch (error) {
    console.error('Error uploading PDF:', error);
    error.value = error.response?.data?.error || t('pdf.uploadError');
  } finally {
    loading.value = false;
  }
};

const compressPdf = async () => {
  if (!fileId.value) return;

  processing.value = true;
  error.value = null;

  try {
    const requestData = {
      file_id: fileId.value,
      compression_level: compressionLevel.value
    };

    const headers = {
      'Content-Type': 'application/json'
    };

    // Add API key if user is authenticated
    if (authStore.token) {
      headers['X-API-Key'] = authStore.user?.apiKey;
    }

    const response = await axios.post(
        `${import.meta.env.VITE_PYTHON_API_URL}/compress`,
        requestData,
        { headers }
    );

    resultFileUrl.value = response.data.id;
    resultFilename.value = response.data.filename || 'compressed.pdf';

    // Get compressed file size
    const fileResponse = await axios.head(
        `${import.meta.env.VITE_PYTHON_API_URL}/download/${resultFileUrl.value}`
    );

    compressedSize.value = parseInt(fileResponse.headers['content-length']) || 0;
    showResultDialog.value = true;
  } catch (error) {
    console.error('Error compressing PDF:', error);
    error.value = error.response?.data?.error || t('pdf.compressError');
  } finally {
    processing.value = false;
  }
};

const downloadResult = async () => {
  if (!resultFileUrl.value) return;

  try {
    const response = await axios.get(
        `${import.meta.env.VITE_PYTHON_API_URL}/download/${resultFileUrl.value}`,
        { responseType: 'blob' }
    );

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', resultFilename.value);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    console.error('Error downloading file:', error);
    error.value = t('pdf.downloadError');
  }
};
</script>